"""
Angle extraction module for drone image metadata processing.
Extracts camera orientation data from EXIF metadata for area correction calculations.
"""

import math
from PIL import Image
from PIL.ExifTags import TAGS
import rasterio


class AngleExtractor:
    """
    Handles extraction of camera angle data from image metadata.
    """
    
    def __init__(self):
        self.angle_tolerance = 5.0  # Degrees - consider perpendicular if within this range
    
    def extract_angles_from_image(self, image_path):
        """
        Extract camera angle information from image metadata.
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Angle information and correction factors
        """
        result = {
            'has_angle_data': False,
            'is_perpendicular': True,
            'pitch_angle': 0.0,
            'roll_angle': 0.0,
            'correction_factor': 1.0,
            'image_type': 'unknown',
            'camera_model': None,
            'angle_source': None
        }
        
        # Try different extraction methods
        angles = self._extract_from_exif(image_path)
        if not angles['has_angle_data']:
            angles = self._extract_from_geotiff(image_path)
        
        result.update(angles)
        
        # Calculate correction factor and perpendicular status
        if result['has_angle_data']:
            result['correction_factor'] = self._calculate_correction_factor(
                result['pitch_angle'], result['roll_angle']
            )
            result['is_perpendicular'] = self._is_perpendicular(
                result['pitch_angle'], result['roll_angle']
            )
        
        return result
    
    def _extract_from_exif(self, image_path):
        """
        Extract angle data from EXIF metadata (drone images).
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Extracted angle data
        """
        result = {
            'has_angle_data': False,
            'pitch_angle': 0.0,
            'roll_angle': 0.0,
            'camera_model': None,
            'image_type': 'standard',
            'angle_source': 'exif'
        }
        
        try:
            with Image.open(image_path) as img:
                exif_data = img.getexif()
                
                if not exif_data:
                    return result
                
                # Convert EXIF data to readable format
                exif_dict = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_dict[tag] = value
                
                # Check for camera model
                camera_make = exif_dict.get('Make', '')
                camera_model = exif_dict.get('Model', '')
                result['camera_model'] = f"{camera_make} {camera_model}".strip()
                
                # Look for drone-specific angle fields
                angle_fields = {
                    'CameraPitch': 'pitch_angle',
                    'CameraRoll': 'roll_angle',
                    'GimbalPitchDegree': 'pitch_angle',
                    'GimbalRollDegree': 'roll_angle',
                    'FlightPitchDegree': 'pitch_angle',
                    'FlightRollDegree': 'roll_angle'
                }
                
                angles_found = False
                for exif_field, angle_type in angle_fields.items():
                    if exif_field in exif_dict:
                        angle_value = float(exif_dict[exif_field])
                        result[angle_type] = angle_value
                        angles_found = True
                
                if angles_found:
                    result['has_angle_data'] = True
                    result['image_type'] = 'drone'
                    
                    # Detect if this is a DJI or other drone
                    if 'DJI' in result['camera_model'].upper():
                        result['image_type'] = 'dji_drone'
                
        except Exception as e:
            # Silent fail - not all images have EXIF data
            pass
        
        return result
    
    def _extract_from_geotiff(self, image_path):
        """
        Check if image is already orthorectified (angle-corrected).
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Image type information
        """
        result = {
            'has_angle_data': False,
            'pitch_angle': 0.0,
            'roll_angle': 0.0,
            'camera_model': 'Processed',
            'image_type': 'standard',
            'angle_source': 'geotiff'
        }
        
        try:
            with rasterio.open(image_path) as src:
                if src.crs is not None:
                    # This is a georeferenced image, likely orthorectified
                    result['image_type'] = 'orthorectified'
                    result['has_angle_data'] = True  # Already corrected
                    result['camera_model'] = 'Orthorectified GeoTIFF'
                    # Angles remain 0.0 because correction already applied
                    
        except Exception:
            # Not a valid rasterio file, probably standard image
            pass
        
        return result
    
    def _calculate_correction_factor(self, pitch_angle, roll_angle):
        """
        Calculate area correction factor based on camera angles.
        
        Args:
            pitch_angle: Camera pitch in degrees (negative = tilted down)
            roll_angle: Camera roll in degrees
            
        Returns:
            float: Correction factor to multiply apparent area
        """
        # Convert to radians
        pitch_rad = math.radians(abs(pitch_angle))
        roll_rad = math.radians(abs(roll_angle))
        
        # For small roll angles, pitch dominates the correction
        # For perpendicular shots (pitch ~-90°), correction factor approaches 1.0
        # For angled shots, use cosine correction
        
        if abs(pitch_angle) > 85:
            # Nearly perpendicular - minimal correction needed
            correction_factor = 1.0 / math.cos(roll_rad)
        else:
            # Significant angle - apply both pitch and roll correction
            effective_angle = math.sqrt(pitch_rad**2 + roll_rad**2)
            correction_factor = 1.0 / math.cos(effective_angle)
        
        # Limit correction factor to reasonable range (1.0 to 3.0)
        return min(max(correction_factor, 1.0), 3.0)
    
    def _is_perpendicular(self, pitch_angle, roll_angle):
        """
        Determine if camera was positioned approximately perpendicular to ground.
        
        Args:
            pitch_angle: Camera pitch in degrees
            roll_angle: Camera roll in degrees
            
        Returns:
            bool: True if approximately perpendicular
        """
        # For drone photography, pitch close to -90° means perpendicular
        perpendicular_pitch = abs(abs(pitch_angle) - 90) <= self.angle_tolerance
        minimal_roll = abs(roll_angle) <= self.angle_tolerance
        
        return perpendicular_pitch and minimal_roll
    
    def get_angle_description(self, angle_data):
        """
        Generate human-readable description of camera angle.
        
        Args:
            angle_data: Dictionary from extract_angles_from_image
            
        Returns:
            str: Description of camera angle and correction status
        """
        if not angle_data['has_angle_data']:
            return "No angle data available"
        
        if angle_data['image_type'] == 'orthorectified':
            return "Orthorectified image - angles already corrected"
        
        if angle_data['is_perpendicular']:
            return f"Perpendicular capture (Pitch: {angle_data['pitch_angle']:.1f}°, Roll: {angle_data['roll_angle']:.1f}°)"
        else:
            correction_percent = (angle_data['correction_factor'] - 1.0) * 100
            return f"Angled capture (Pitch: {angle_data['pitch_angle']:.1f}°, Roll: {angle_data['roll_angle']:.1f}°) - {correction_percent:.1f}% correction applied"
    
    def get_angle_warning(self, angle_data):
        """
        Generate warning message for significant angle corrections.
        
        Args:
            angle_data: Dictionary from extract_angles_from_image
            
        Returns:
            str: Warning message or None
        """
        if not angle_data['has_angle_data'] or angle_data['is_perpendicular']:
            return None
        
        correction_factor = angle_data['correction_factor']
        
        if correction_factor > 1.5:
            return "High angle correction applied - consider using perpendicular imagery for maximum accuracy"
        elif correction_factor > 1.2:
            return "Moderate angle correction applied - accuracy reduced compared to perpendicular imagery"
        else:
            return None