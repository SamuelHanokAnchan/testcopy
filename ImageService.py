import enum
import os
import tempfile
from logging import debug, warn, error

import rasterio
from PIL import Image
from pathlib import Path
import numpy as np

from angle_extractor import AngleExtractor


class ImageTypes(enum.Enum):
    TIFF = 1
    TIF = 2
    PNG = 3
    JPG = 4
    JPEG = 5

class ImageService:
    angle_extractor = AngleExtractor()

    def load_image(self, picture_id: str) -> object:
        """
        Load Image from arbitrary source based on provided ID.
        :rtype: object
        """
        file_type = self.__image_filetype(picture_id)
        image: object = self.__load_standard_image(picture_id)
        if file_type is None:
            raise RuntimeError(f"File type not supported: {picture_id}")
        elif file_type is ImageTypes.TIFF or file_type is ImageTypes.TIF:
            image = self.__load_tiff_image(picture_id)
        else:
            image = self.__load_standard_image(picture_id)

        return image

    def __load_tiff_image(self, picture_id: str):
        """Load TIFF image with geospatial data using rasterio."""
        file_content = Path("./data/"+picture_id).read_bytes()
        tmp_path = None
        try:
            if len(file_content) < 1000 and b'version https://git-lfs.github.com' in file_content:
                raise RuntimeError(
                    "This appears to be a Git LFS pointer file, not the actual image. Please run 'git lfs pull' to download the actual files.")

            with tempfile.NamedTemporaryFile(delete=False, suffix='.tiff') as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name

            file_size = os.path.getsize(tmp_path)
            debug(f'File {tmp_path} has a size of {file_size}.')

            try:
                with rasterio.open(tmp_path) as src:
                    image_data = src.read()

                    if image_data.shape[0] == 1:
                        display_array = np.stack([image_data[0], image_data[0], image_data[0]], axis=2)
                    elif image_data.shape[0] >= 3:
                        display_array = np.transpose(image_data[:3], (1, 2, 0))
                    else:
                        display_array = np.stack([image_data[0], image_data[0], image_data[0]], axis=2)

                    if display_array.dtype != np.uint8:
                        display_array = self.normalize_image_array(display_array)

                    metadata = {
                        'width': src.width,
                        'height': src.height,
                        'count': src.count,
                        'dtype': str(src.dtypes[0]),
                        'crs': str(src.crs) if src.crs else 'No CRS',
                        'transform': src.transform,
                        'bounds': src.bounds
                    }

                    pixel_size_x = abs(src.transform[0]) if src.transform else None
                    pixel_size_y = abs(src.transform[4]) if src.transform else None

                    result = {
                        'array': display_array,
                        'metadata': metadata,
                        'pixel_size_x': pixel_size_x,
                        'pixel_size_y': pixel_size_y,
                        'has_geospatial': src.crs is not None,
                        'file_path': tmp_path
                    }

                    return result

            except Exception as rasterio_error:
                warn(f"Rasterio failed ({str(rasterio_error)}), trying with PIL...")
                return self.load_standard_image_from_path(tmp_path)

        except Exception as e:
            raise RuntimeError(f"Error processing TIFF file: {str(e)}")

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass

    def __image_filetype(self, picture_id: str) -> ImageTypes | None:
        """
        Determine the filetype of a given image.

        :param picture_id: The image identifier.
        :return: The corresponding image type.
        :rtype: ImageTypes
        """
        file_extension = picture_id.lower().split('.')[-1]
        match file_extension:
            case 'tiff':
                return ImageTypes.TIFF
            case 'tif':
                return ImageTypes.TIF
            case 'png':
                return ImageTypes.PNG
            case 'jpg':
                return ImageTypes.JPG
            case 'jpeg':
                return ImageTypes.JPEG
            case _:
                return None

    def __load_standard_image(self, picture_id: str) -> object:
        """
        Load standard image formats (PNG, JPG, etc.) with angle extraction.
        :rtype: object
        """
        try:
            path = Path("./data/" + picture_id)
            # Check angle_data folder if not in data. Remove once proper image service is implemented.
            if not path.exists():
                path = Path("./data/angle_data/" + picture_id)
            file_content = path.read_bytes()
            file_extension = picture_id.split('.')[-1].lower()

            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name

            image = Image.open(tmp_path)

            if image.mode != 'RGB':
                image = image.convert('RGB')

            image_array = np.array(image)

            result = {
                'array': image_array,
                'metadata': {
                    'width': image.width,
                    'height': image.height,
                    'mode': image.mode
                },
                'has_geospatial': False,
                'pixel_size_x': None,
                'pixel_size_y': None,
                'file_path': tmp_path
            }

            return result

        except Exception as e:
            raise RuntimeError(f"Error loading image: {str(e)}") from e

    @staticmethod
    def normalize_image_array(array):
        """Normalize image array to 0-255 uint8 range."""
        if array.max() <= 1.0:
            return (array * 255).astype(np.uint8)
        elif array.max() <= 255:
            return array.astype(np.uint8)
        else:
            array_min = array.min()
            array_max = array.max()
            normalized = ((array - array_min) / (array_max - array_min) * 255)
            return normalized.astype(np.uint8)

    @staticmethod
    def load_standard_image_from_path(file_path):
        """Load standard image from file path."""
        try:
            image = Image.open(file_path)

            if image.mode != 'RGB':
                image = image.convert('RGB')

            image_array = np.array(image)

            return {
                'array': image_array,
                'metadata': {
                    'width': image.width,
                    'height': image.height,
                    'mode': image.mode
                },
                'has_geospatial': False,
                'pixel_size_x': None,
                'pixel_size_y': None,
                'file_path': file_path
            }

        except Exception as e:
            raise RuntimeError(f"Error loading image from path: {str(e)}")

    def extract_and_display_angle_info(self, image_data):
        """Extract and display angle information from image."""
        if 'file_path' not in image_data or not image_data['file_path']:
            return None

        try:
           return self.angle_extractor.extract_angles_from_image(image_data['file_path'])

        except Exception as e:
            error(f"Error extracting angle data: {str(e)}")
            return None
