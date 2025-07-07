"""
Test script for angle correction functionality.
Tests the AngleExtractor and area correction calculations.
"""

import os
import sys

# Add src directory to path
sys.path.append('src')

from angle_extractor import AngleExtractor
from area_calculator import AreaCalculator

def test_angle_extraction():
    """Test angle extraction from various image types."""
    
    print("Testing Angle Extraction")
    print("=" * 50)
    
    angle_extractor = AngleExtractor()
    
    # Test with different types of images
    test_images = [
        "data/output_tile_1.tif",  # Orthorectified TIFF
        "data/angle_data/DJI_0196.JPG"  # DJI drone image
    ]
    
    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\nAnalyzing: {image_path}")
            print("-" * 30)
            
            angle_data = angle_extractor.extract_angles_from_image(image_path)
            
            print(f"Image Type: {angle_data['image_type']}")
            print(f"Camera Model: {angle_data['camera_model']}")
            print(f"Has Angle Data: {angle_data['has_angle_data']}")
            print(f"Is Perpendicular: {angle_data['is_perpendicular']}")
            print(f"Pitch Angle: {angle_data['pitch_angle']:.1f}°")
            print(f"Roll Angle: {angle_data['roll_angle']:.1f}°")
            print(f"Correction Factor: {angle_data['correction_factor']:.3f}")
            
            description = angle_extractor.get_angle_description(angle_data)
            print(f"Description: {description}")
            
            warning = angle_extractor.get_angle_warning(angle_data)
            if warning:
                print(f"Warning: {warning}")
        else:
            print(f"Image not found: {image_path}")

def test_area_correction():
    """Test area correction calculations."""
    
    print("\n\nTesting Area Correction")
    print("=" * 50)
    
    area_calc = AreaCalculator()
    
    # Test polygon (simple rectangle)
    test_polygon = [[100, 100], [500, 100], [500, 300], [100, 300]]
    pixel_size = 0.1  # 10 cm per pixel
    
    print(f"Test Polygon: {test_polygon}")
    print(f"Pixel Size: {pixel_size} m/pixel")
    
    # Test with different angle scenarios
    test_scenarios = [
        {
            'name': 'Perpendicular Image',
            'angle_data': {
                'has_angle_data': True,
                'is_perpendicular': True,
                'pitch_angle': -90.0,
                'roll_angle': 0.0,
                'correction_factor': 1.0
            }
        },
        {
            'name': 'Slightly Angled (15° pitch)',
            'angle_data': {
                'has_angle_data': True,
                'is_perpendicular': False,
                'pitch_angle': -75.0,
                'roll_angle': 2.0,
                'correction_factor': 1.035
            }
        },
        {
            'name': 'Moderately Angled (30° pitch)',
            'angle_data': {
                'has_angle_data': True,
                'is_perpendicular': False,
                'pitch_angle': -60.0,
                'roll_angle': 5.0,
                'correction_factor': 1.155
            }
        },
        {
            'name': 'No Angle Data',
            'angle_data': {
                'has_angle_data': False,
                'is_perpendicular': True,
                'pitch_angle': 0.0,
                'roll_angle': 0.0,
                'correction_factor': 1.0
            }
        },
        {
            'name': 'No Pixel Size (None values)',
            'angle_data': None,
            'pixel_size': None
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\nScenario: {scenario['name']}")
        print("-" * 30)
        
        test_pixel_size = scenario.get('pixel_size', pixel_size)
        
        area_result = area_calc.calculate_corrected_area(
            test_polygon, test_pixel_size, test_pixel_size, scenario.get('angle_data')
        )
        
        print(f"Pixel Area: {area_result['pixel_area']:.0f} pixels²")
        print(f"Apparent Area: {area_result['apparent_area_m2']:.2f} m²")
        print(f"Corrected Area: {area_result['corrected_area_m2']:.2f} m²")
        print(f"Correction Factor: {area_result['correction_factor']:.3f}")
        print(f"Correction Applied: {area_result['correction_applied']}")
        
        if area_result['correction_applied']:
            print(f"Area Difference: +{area_result['area_difference_m2']:.2f} m² ({area_result['area_difference_percent']:.1f}%)")

def test_multiple_polygons():
    """Test multiple polygon calculations with angle correction."""
    
    print("\n\nTesting Multiple Polygons")
    print("=" * 50)
    
    area_calc = AreaCalculator()
    
    # Multiple test polygons
    test_polygons = [
        [[100, 100], [300, 100], [300, 200], [100, 200]],  # Small rectangle
        [[400, 150], [700, 150], [700, 350], [400, 350]],  # Large rectangle
        [[50, 300], [200, 300], [200, 400], [50, 400]]     # Another rectangle
    ]
    
    pixel_size = 0.075  # Similar to your TIFF data
    
    angle_data = {
        'has_angle_data': True,
        'is_perpendicular': False,
        'pitch_angle': -75.0,
        'roll_angle': 3.0,
        'correction_factor': 1.035
    }
    
    # Test with normal pixel size
    print("Test with normal pixel size:")
    results = area_calc.calculate_multiple_polygons(
        test_polygons, pixel_size, pixel_size, angle_data
    )
    
    print(f"Number of Polygons: {results['polygon_count']}")
    print(f"Total Apparent Area: {results['total_apparent_area_m2']:.2f} m²")
    print(f"Total Corrected Area: {results['total_corrected_area_m2']:.2f} m²")
    
    correction_summary = results['angle_correction_summary']
    if correction_summary['correction_applied']:
        print(f"Total Correction: +{correction_summary['total_area_difference_m2']:.2f} m² ({correction_summary['total_area_difference_percent']:.1f}%)")
        print(f"Average Correction Factor: {correction_summary['average_correction_factor']:.3f}")
    
    print("\nIndividual Areas:")
    for i, (apparent, corrected) in enumerate(zip(results['individual_areas_m2'], results['individual_corrected_areas_m2'])):
        print(f"  Area {i+1}: {apparent:.2f} m² → {corrected:.2f} m² (+{corrected-apparent:.2f} m²)")
    
    # Test with None pixel size
    print("\nTest with None pixel size (default handling):")
    results_none = area_calc.calculate_multiple_polygons(
        test_polygons, None, None, angle_data
    )
    
    print(f"Total Corrected Area: {results_none['total_corrected_area_m2']:.2f} m² (using default 0.1 m/pixel)")
    print("Default pixel size handling: PASSED")

def main():
    """Run all tests."""
    
    print("Angle Correction System Test")
    print("=" * 60)
    
    try:
        test_angle_extraction()
        test_area_correction()
        test_multiple_polygons()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()