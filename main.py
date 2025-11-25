import os
from typing import Tuple

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyQuery, APIKeyHeader
from starlette.middleware.cors import CORSMiddleware

from ImageService import ImageService
from area_calculator import AreaCalculator
from auto_detection import SAMAutoDetection
from models.AreaReturnModel import AreaReturnModel
from models.ImageMetadataModel import ImageMetadataModel

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:4200",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
API_KEY = os.environ.get("API_KEY")
auto_detector = SAMAutoDetection()
image_service = ImageService()
area_calculator = AreaCalculator()

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
) -> str:
    """Retrieve and validate an API key from the query parameters or HTTP header.

    Args:
        api_key_query: The API key passed as a query parameter.
        api_key_header: The API key passed in the HTTP header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is invalid or missing.
    """
    if not API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key server error.")

    if api_key_query == API_KEY:
        return api_key_query
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


@app.get("/area/metadata/{picture_id}", response_model=ImageMetadataModel)
def get_area_metadata(picture_id: str, api_key: str = Security(get_api_key)) -> ImageMetadataModel:
    image_data = image_service.load_image(picture_id)
    return ImageMetadataModel(image_data.get('metadata'))

@app.post("/area/smart/{picture_id}", response_model=AreaReturnModel)
def calc_smart_area(picture_id: str, point_coordinate: Tuple[int, int], api_key: str = Security(get_api_key)) -> AreaReturnModel:
    image_data = image_service.load_image(picture_id)
    detected_areas = auto_detector.detect_with_points(image_array= image_data['array'],
                                                      point_coords=[point_coordinate], point_labels=[1])
    if detected_areas and len(detected_areas) > 0:
        # Take only the first detected area to prevent multiples
        # NOTE: from student solution, validate if this actually makes sense/there is no better option!
        area = detected_areas[0]
        if len(area) >= 3:  # Valid polygon
            angle_data = image_service.extract_and_display_angle_info(image_data)
            pixel_size_x = image_data.get('pixel_size_x', 0.1)
            area_result = area_calculator.calculate_corrected_area(area, pixel_size_x, pixel_size_x, angle_data)
            return AreaReturnModel(calculated_area=area_result, polygon=area)
            #return the area
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid area selected.")
            #invalid area
    else:
        # area too small
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Detected area is too small.")


@app.post("/area/custom/{picture_id}", response_model=AreaReturnModel)
def calc_custom_area(picture_id: str, polygon: list[Tuple[int, int]], api_key: str = Security(get_api_key)) -> AreaReturnModel:
    image_data = image_service.load_image(picture_id)
    angle_data = image_service.extract_and_display_angle_info(image_data)
    pixel_size_x = image_data.get('pixel_size_x', 0.1)
    area_result = area_calculator.calculate_corrected_area(polygon, pixel_size_x, pixel_size_x, angle_data)
    return AreaReturnModel(calculated_area=area_result, polygon=polygon)

