"""
Area calculation module for construction resource planning.
Handles polygon area calculations, coordinate transformations, and angle corrections.
"""

import numpy as np
import cv2
from shapely.geometry import Polygon


class AreaCalculator:
    """
    Handles area calculations for construction planning polygons with angle correction support.
    """
    
    def __init__(self):
        pass
    
    def calculate_polygon_area_pixels(self, polygon_points):
        """
        Calculate area of a polygon in square pixels using shoelace formula.
        
        Args:
            polygon_points: List of [x, y] coordinates in pixels
            
        Returns:
            float: Area in square pixels
        """
        if len(polygon_points) < 3:
            return 0.0
        
        # Use OpenCV contour area calculation
        points = np.array(polygon_points, dtype=np.int32)
        area = cv2.contourArea(points)
        return abs(area)
    
    def calculate_polygon_area_shapely(self, polygon_points):
        """
        Alternative area calculation using Shapely for complex polygons.
        
        Args:
            polygon_points: List of [x, y] coordinates
            
        Returns:
            float: Area in square units
        """
        if len(polygon_points) < 3:
            return 0.0
        
        try:
            polygon = Polygon(polygon_points)
            if polygon.is_valid:
                return polygon.area
            else:
                # Try to fix invalid polygon
                fixed_polygon = polygon.buffer(0)
                return fixed_polygon.area if fixed_polygon.is_valid else 0.0
        except Exception:
            # Fallback to OpenCV method
            return self.calculate_polygon_area_pixels(polygon_points)
    
    def pixels_to_square_meters(self, pixel_area, pixel_size_x, pixel_size_y=None):
        """
        Convert pixel area to real-world square meters.
        
        Args:
            pixel_area: Area in square pixels
            pixel_size_x: Meters per pixel in X direction
            pixel_size_y: Meters per pixel in Y direction (optional)
            
        Returns:
            float: Area in square meters
        """
        # Handle None values with default pixel size
        if pixel_size_x is None:
            pixel_size_x = 0.1  # Default: 10cm per pixel
        
        if pixel_size_y is None:
            pixel_size_y = pixel_size_x
        
        # Calculate area conversion factor
        area_conversion_factor = pixel_size_x * pixel_size_y
        
        return pixel_area * area_conversion_factor
    
    def apply_angle_correction(self, apparent_area, correction_factor):
        """
        Apply angle correction to area measurement.
        
        Args:
            apparent_area: Area as measured from angled image
            correction_factor: Correction factor from angle analysis
            
        Returns:
            float: Corrected area
        """
        return apparent_area * correction_factor
    
    def calculate_corrected_area(self, polygon_points, pixel_size_x, pixel_size_y=None, angle_data=None):
        """
        Calculate area with angle correction applied.
        
        Args:
            polygon_points: List of [x, y] coordinates in pixels
            pixel_size_x: Meters per pixel in X direction
            pixel_size_y: Meters per pixel in Y direction (optional)
            angle_data: Dictionary with angle information from AngleExtractor
            
        Returns:
            dict: Area calculation results with correction details
        """
        # Handle None values with defaults
        if pixel_size_x is None:
            pixel_size_x = 0.1  # Default: 10cm per pixel
        if pixel_size_y is None:
            pixel_size_y = pixel_size_x
        
        # Calculate base pixel area
        pixel_area = self.calculate_polygon_area_pixels(polygon_points)
        
        # Convert to real-world area
        apparent_area_m2 = self.pixels_to_square_meters(pixel_area, pixel_size_x, pixel_size_y)
        
        # Apply angle correction if available
        corrected_area_m2 = apparent_area_m2
        correction_applied = False
        correction_factor = 1.0
        
        if angle_data and angle_data.get('has_angle_data', False):
            correction_factor = angle_data.get('correction_factor', 1.0)
            corrected_area_m2 = self.apply_angle_correction(apparent_area_m2, correction_factor)
            correction_applied = not angle_data.get('is_perpendicular', True)
        
        return {
            'pixel_area': pixel_area,
            'apparent_area_m2': apparent_area_m2,
            'corrected_area_m2': corrected_area_m2,
            'correction_factor': correction_factor,
            'correction_applied': correction_applied,
            'area_difference_m2': corrected_area_m2 - apparent_area_m2,
            'area_difference_percent': ((corrected_area_m2 / apparent_area_m2) - 1.0) * 100 if apparent_area_m2 > 0 else 0
        }
    
    def calculate_polygon_perimeter(self, polygon_points, pixel_size_x, pixel_size_y=None):
        """
        Calculate polygon perimeter in meters.
        
        Args:
            polygon_points: List of [x, y] coordinates in pixels
            pixel_size_x: Meters per pixel in X direction
            pixel_size_y: Meters per pixel in Y direction (optional)
            
        Returns:
            float: Perimeter in meters
        """
        if len(polygon_points) < 3:
            return 0.0
        
        # Handle None values with defaults
        if pixel_size_x is None:
            pixel_size_x = 0.1  # Default: 10cm per pixel
        if pixel_size_y is None:
            pixel_size_y = pixel_size_x
        
        perimeter_meters = 0.0
        
        # Calculate perimeter by summing distances between consecutive points
        for i in range(len(polygon_points)):
            x1, y1 = polygon_points[i]
            x2, y2 = polygon_points[(i + 1) % len(polygon_points)]
            
            # Calculate distance in pixels
            dx_pixels = x2 - x1
            dy_pixels = y2 - y1
            
            # Convert to meters
            dx_meters = dx_pixels * pixel_size_x
            dy_meters = dy_pixels * pixel_size_y
            
            # Euclidean distance
            distance_meters = np.sqrt(dx_meters**2 + dy_meters**2)
            perimeter_meters += distance_meters
        
        return perimeter_meters
    
    def get_polygon_bounds(self, polygon_points, pixel_size_x, pixel_size_y=None):
        """
        Get bounding box dimensions of polygon in meters.
        
        Args:
            polygon_points: List of [x, y] coordinates in pixels
            pixel_size_x: Meters per pixel in X direction
            pixel_size_y: Meters per pixel in Y direction (optional)
            
        Returns:
            dict: Bounding box information
        """
        if len(polygon_points) < 1:
            return {}
        
        # Handle None values with defaults
        if pixel_size_x is None:
            pixel_size_x = 0.1  # Default: 10cm per pixel
        if pixel_size_y is None:
            pixel_size_y = pixel_size_x
        
        points = np.array(polygon_points)
        
        min_x, min_y = points.min(axis=0)
        max_x, max_y = points.max(axis=0)
        
        width_pixels = max_x - min_x
        height_pixels = max_y - min_y
        
        width_meters = width_pixels * pixel_size_x
        height_meters = height_pixels * pixel_size_y
        
        return {
            'min_x_pixels': min_x,
            'min_y_pixels': min_y,
            'max_x_pixels': max_x,
            'max_y_pixels': max_y,
            'width_pixels': width_pixels,
            'height_pixels': height_pixels,
            'width_meters': width_meters,
            'height_meters': height_meters
        }
    
    def calculate_multiple_polygons(self, polygons_list, pixel_size_x, pixel_size_y=None, angle_data=None):
        """
        Calculate areas for multiple polygons with angle correction.
        
        Args:
            polygons_list: List of polygon point lists
            pixel_size_x: Meters per pixel in X direction
            pixel_size_y: Meters per pixel in Y direction (optional)
            angle_data: Dictionary with angle information from AngleExtractor
            
        Returns:
            dict: Summary of all polygon calculations with correction details
        """
        # Handle None values with defaults
        if pixel_size_x is None:
            pixel_size_x = 0.1  # Default: 10cm per pixel
        if pixel_size_y is None:
            pixel_size_y = pixel_size_x
        results = {
            'individual_areas_m2': [],
            'individual_areas_sqft': [],
            'individual_corrected_areas_m2': [],
            'individual_corrected_areas_sqft': [],
            'individual_perimeters_m': [],
            'individual_corrections': [],
            'total_apparent_area_m2': 0.0,
            'total_corrected_area_m2': 0.0,
            'total_apparent_area_sqft': 0.0,
            'total_corrected_area_sqft': 0.0,
            'total_perimeter_m': 0.0,
            'polygon_count': len(polygons_list),
            'angle_correction_summary': {
                'correction_applied': False,
                'average_correction_factor': 1.0,
                'total_area_difference_m2': 0.0,
                'total_area_difference_percent': 0.0
            }
        }
        
        total_correction_factors = 0.0
        corrections_applied = 0
        
        for i, polygon_points in enumerate(polygons_list):
            # Calculate area with correction
            area_result = self.calculate_corrected_area(
                polygon_points, pixel_size_x, pixel_size_y, angle_data
            )
            
            apparent_area_m2 = area_result['apparent_area_m2']
            corrected_area_m2 = area_result['corrected_area_m2']
            
            # Convert to square feet
            apparent_area_sqft = apparent_area_m2 * 10.764
            corrected_area_sqft = corrected_area_m2 * 10.764
            
            # Calculate perimeter
            perimeter_m = self.calculate_polygon_perimeter(polygon_points, pixel_size_x, pixel_size_y)
            
            # Store individual results
            results['individual_areas_m2'].append(apparent_area_m2)
            results['individual_areas_sqft'].append(apparent_area_sqft)
            results['individual_corrected_areas_m2'].append(corrected_area_m2)
            results['individual_corrected_areas_sqft'].append(corrected_area_sqft)
            results['individual_perimeters_m'].append(perimeter_m)
            results['individual_corrections'].append(area_result)
            
            # Add to totals
            results['total_apparent_area_m2'] += apparent_area_m2
            results['total_corrected_area_m2'] += corrected_area_m2
            results['total_apparent_area_sqft'] += apparent_area_sqft
            results['total_corrected_area_sqft'] += corrected_area_sqft
            results['total_perimeter_m'] += perimeter_m
            
            # Track corrections
            if area_result['correction_applied']:
                total_correction_factors += area_result['correction_factor']
                corrections_applied += 1
        
        # Calculate correction summary
        if corrections_applied > 0:
            results['angle_correction_summary']['correction_applied'] = True
            results['angle_correction_summary']['average_correction_factor'] = (
                total_correction_factors / corrections_applied
            )
            results['angle_correction_summary']['total_area_difference_m2'] = (
                results['total_corrected_area_m2'] - results['total_apparent_area_m2']
            )
            if results['total_apparent_area_m2'] > 0:
                results['angle_correction_summary']['total_area_difference_percent'] = (
                    (results['total_corrected_area_m2'] / results['total_apparent_area_m2'] - 1.0) * 100
                )
        
        return results
    
    def validate_polygon(self, polygon_points):
        """
        Validate if polygon points form a valid polygon.
        
        Args:
            polygon_points: List of [x, y] coordinates
            
        Returns:
            dict: Validation results
        """
        validation = {
            'is_valid': False,
            'point_count': len(polygon_points),
            'has_minimum_points': False,
            'has_area': False,
            'is_self_intersecting': False,
            'error_message': None
        }
        
        # Check minimum points
        if len(polygon_points) < 3:
            validation['error_message'] = "Polygon must have at least 3 points"
            return validation
        
        validation['has_minimum_points'] = True
        
        # Check if has area
        area = self.calculate_polygon_area_pixels(polygon_points)
        if area > 0:
            validation['has_area'] = True
        else:
            validation['error_message'] = "Polygon has no area"
            return validation
        
        # Check for self-intersection using Shapely
        try:
            polygon = Polygon(polygon_points)
            if not polygon.is_valid:
                validation['is_self_intersecting'] = True
                validation['error_message'] = "Polygon is self-intersecting"
                return validation
        except Exception as e:
            validation['error_message'] = f"Polygon validation error: {str(e)}"
            return validation
        
        validation['is_valid'] = True
        return validation
    
    def get_area_summary_text(self, area_results, pixel_size_x, polygon_points, angle_data=None):
        """
        Generate human-readable summary of area calculation with angle correction details.
        
        Args:
            area_results: Results from calculate_corrected_area
            pixel_size_x: Pixel resolution in meters
            polygon_points: List of polygon points
            angle_data: Angle information from AngleExtractor
            
        Returns:
            str: Formatted summary text
        """
        # Handle None pixel size
        if pixel_size_x is None:
            pixel_size_x = 0.1  # Default: 10cm per pixel
        
        corrected_area_m2 = area_results['corrected_area_m2']
        apparent_area_m2 = area_results['apparent_area_m2']
        corrected_area_sqft = corrected_area_m2 * 10.764
        
        perimeter_m = self.calculate_polygon_perimeter(polygon_points, pixel_size_x)
        bounds = self.get_polygon_bounds(polygon_points, pixel_size_x)
        
        summary = f"""
        Area Summary:
        - Corrected Area: {corrected_area_m2:.2f} m² ({corrected_area_sqft:.1f} sq ft)
        - Apparent Area: {apparent_area_m2:.2f} m²
        - Perimeter: {perimeter_m:.1f} meters
        - Dimensions: {bounds.get('width_meters', 0):.1f}m × {bounds.get('height_meters', 0):.1f}m
        - Points: {len(polygon_points)}
        - Resolution: {pixel_size_x:.3f} m/pixel
        """
        
        if area_results['correction_applied']:
            summary += f"""
        Angle Correction Applied:
        - Correction Factor: {area_results['correction_factor']:.3f}
        - Area Increase: {area_results['area_difference_m2']:.2f} m² ({area_results['area_difference_percent']:.1f}%)
        """
            
            if angle_data:
                summary += f"""
        - Camera Pitch: {angle_data['pitch_angle']:.1f}°
        - Camera Roll: {angle_data['roll_angle']:.1f}°
        """
        
        return summary.strip()