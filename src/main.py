import streamlit as st
import rasterio
import numpy as np
from PIL import Image
import tempfile
import os
import cv2
from streamlit_image_coordinates import streamlit_image_coordinates

# Import our custom modules
from area_calculator import AreaCalculator
from material_calculator import MaterialCalculator
from auto_detection import SAMAutoDetection
from angle_extractor import AngleExtractor

st.set_page_config(
    page_title="Image Resource Planner",
    page_icon="🏗️",
    layout="wide"
)

def load_tiff_image(uploaded_file):
    """
    Load TIFF image with geospatial data using rasterio.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        dict: Image data and metadata
    """
    tmp_path = None
    try:
        file_content = uploaded_file.getbuffer()
        
        if len(file_content) < 1000 and b'version https://git-lfs.github.com' in file_content:
            st.error("This appears to be a Git LFS pointer file, not the actual image. Please run 'git lfs pull' to download the actual files.")
            return None
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tiff') as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        file_size = os.path.getsize(tmp_path)
        if file_size < 1000:
            st.error(f"File appears to be too small ({file_size} bytes). This might be a Git LFS pointer file.")
            return None
        
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
                    display_array = normalize_image_array(display_array)
                
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
            st.warning(f"Rasterio failed ({str(rasterio_error)}), trying with PIL...")
            return load_standard_image_from_path(tmp_path)
            
    except Exception as e:
        st.error(f"Error processing TIFF file: {str(e)}")
        return None
        
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass

def load_standard_image(uploaded_file):
    """
    Load standard image formats (PNG, JPG, etc.) with angle extraction.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        dict: Image data and metadata
    """
    tmp_path = None
    try:
        # Save uploaded file to temporary location for angle extraction
        file_content = uploaded_file.getbuffer()
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
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
        st.error(f"Error loading image: {str(e)}")
        return None

def load_standard_image_from_path(file_path):
    """
    Load standard image from file path.
    
    Args:
        file_path: Path to image file
        
    Returns:
        dict: Image data
    """
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
        st.error(f"Error loading image from path: {str(e)}")
        return None

def normalize_image_array(array):
    """
    Normalize image array to 0-255 uint8 range.
    """
    if array.max() <= 1.0:
        return (array * 255).astype(np.uint8)
    elif array.max() <= 255:
        return array.astype(np.uint8)
    else:
        array_min = array.min()
        array_max = array.max()
        normalized = ((array - array_min) / (array_max - array_min) * 255)
        return normalized.astype(np.uint8)

def extract_and_display_angle_info(image_data):
    """
    Extract and display angle information from image.
    
    Args:
        image_data: Image data dictionary
        
    Returns:
        dict: Angle data from AngleExtractor
    """
    angle_extractor = st.session_state.angle_extractor
    
    if 'file_path' not in image_data or not image_data['file_path']:
        return None
    
    try:
        angle_data = angle_extractor.extract_angles_from_image(image_data['file_path'])
        
        # Display angle information
        st.subheader("Camera Angle Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Image Type:** {angle_data['image_type'].replace('_', ' ').title()}")
            if angle_data['camera_model']:
                st.write(f"**Camera:** {angle_data['camera_model']}")
        
        with col2:
            if angle_data['has_angle_data']:
                st.write(f"**Pitch Angle:** {angle_data['pitch_angle']:.1f}°")
                st.write(f"**Roll Angle:** {angle_data['roll_angle']:.1f}°")
                st.write(f"**Correction Factor:** {angle_data['correction_factor']:.3f}")
        
        # Display angle description and warnings
        description = angle_extractor.get_angle_description(angle_data)
        if angle_data['is_perpendicular']:
            st.success(description)
        elif angle_data['image_type'] == 'orthorectified':
            st.info(description)
        else:
            st.warning(description)
        
        # Show warning if significant correction needed
        warning = angle_extractor.get_angle_warning(angle_data)
        if warning:
            st.warning(warning)
        
        return angle_data
        
    except Exception as e:
        st.error(f"Error extracting angle data: {str(e)}")
        return None

def display_image_metadata(metadata, has_geospatial, pixel_size_x=None, pixel_size_y=None):
    """
    Display image metadata in formatted way.
    """
    st.subheader("Image Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Dimensions:** {metadata['width']} x {metadata['height']} pixels")
        if 'count' in metadata:
            st.write(f"**Bands:** {metadata['count']}")
        if 'dtype' in metadata:
            st.write(f"**Data Type:** {metadata['dtype']}")
    
    with col2:
        if has_geospatial:
            st.write(f"**Coordinate System:** {metadata['crs']}")
            if pixel_size_x and pixel_size_y:
                st.write(f"**Pixel Size:** {pixel_size_x:.6f} x {pixel_size_y:.6f} meters")
        else:
            st.write("**Coordinate System:** None")
    
    if has_geospatial and 'bounds' in metadata:
        bounds = metadata['bounds']
        with st.expander("Spatial Bounds"):
            st.write(f"**Left:** {bounds.left:.6f}")
            st.write(f"**Bottom:** {bounds.bottom:.6f}")
            st.write(f"**Right:** {bounds.right:.6f}")
            st.write(f"**Top:** {bounds.top:.6f}")

def display_area_selection_interface():
    """Display the area selection interface with clickable image and auto-detection."""
    
    st.subheader("Area Selection")
    
    image_data = st.session_state.current_image
    auto_detector = st.session_state.auto_detector
    
    col_a, col_b, col_c, col_d = st.columns(4)
    
    with col_a:
        if st.button("Start New Area"):
            st.session_state.current_polygon = []
            st.rerun()
    
    with col_b:
        if st.button("Complete Area"):
            if len(st.session_state.current_polygon) >= 3:
                st.session_state.polygons.append(st.session_state.current_polygon.copy())
                st.session_state.current_polygon = []
                st.success("Area completed!")
                st.rerun()
            else:
                st.warning("Need at least 3 points to complete an area")
    
    with col_c:
        if st.button("Auto Detect Areas"):
            with st.spinner("Detecting areas using AI..."):
                detected_areas = auto_detector.detect_everything(
                    image_data['array'], 
                    min_area=2000, 
                    max_areas=5
                )
                
                if detected_areas:
                    for area in detected_areas:
                        st.session_state.polygons.append(area)
                    st.success(f"Detected {len(detected_areas)} areas!")
                    st.rerun()
                else:
                    st.warning("No areas detected. Try manual selection.")
    
    with col_d:
        if st.button("Clear All Areas"):
            st.session_state.polygons = []
            st.session_state.current_polygon = []
            st.rerun()
    
    detection_info = auto_detector.get_detection_info()
    if detection_info['sam_available']:
        st.success("AI Detection: SAM Model Active")
    else:
        st.warning("AI Detection: Basic CV Mode")
        with st.expander("Enable SAM AI Detection"):
            st.markdown(auto_detector.download_sam_instructions())
    
    st.info("Click on the image to add points manually, or use 'Auto Detect Areas' for AI detection")
    
    if st.session_state.current_polygon:
        st.write("**Current Area Points:**")
        for i, point in enumerate(st.session_state.current_polygon):
            st.text(f"Point {i+1}: ({point[0]}, {point[1]})")
    
    display_interactive_image(image_data)

def display_interactive_image(image_data):
    """Display the interactive image with click detection and polygon overlays."""
    
    display_array = image_data['array'].copy()
    
    for i, polygon in enumerate(st.session_state.polygons):
        if len(polygon) >= 3:
            overlay = display_array.copy()
            points = np.array(polygon, dtype=np.int32)
            
            cv2.fillPoly(overlay, [points], (0, 255, 0))
            display_array = cv2.addWeighted(display_array, 0.7, overlay, 0.3, 0)
            
            cv2.polylines(display_array, [points], True, (0, 200, 0), 2)
            
            for point in polygon:
                cv2.circle(display_array, tuple(point), 4, (0, 255, 0), -1)
            
            center_x = int(np.mean([p[0] for p in polygon]))
            center_y = int(np.mean([p[1] for p in polygon]))
            cv2.putText(display_array, f"Area {i+1}", (center_x-30, center_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    if len(st.session_state.current_polygon) >= 2:
        points = np.array(st.session_state.current_polygon, dtype=np.int32)
        cv2.polylines(display_array, [points], False, (255, 0, 0), 2)
    
    for point in st.session_state.current_polygon:
        cv2.circle(display_array, tuple(point), 4, (255, 0, 0), -1)
    
    pil_image = Image.fromarray(display_array)
    
    coordinates = streamlit_image_coordinates(
        pil_image,
        key="image_coordinates"
    )
    
    if coordinates is not None:
        x, y = int(coordinates["x"]), int(coordinates["y"])
        
        if [x, y] not in st.session_state.current_polygon:
            st.session_state.current_polygon.append([x, y])
            st.success(f"Point added: ({x}, {y})")
            st.rerun()

def display_calculation_panel():
    """Display the calculation and material estimation panel with angle correction."""
    
    st.header("Calculations & Materials")
    
    if not st.session_state.polygons:
        st.info("Draw areas on the image to see calculations")
        return
    
    image_data = st.session_state.current_image
    if not image_data:
        return
    
    area_calc = st.session_state.area_calculator
    material_calc = st.session_state.material_calculator
    angle_data = st.session_state.get('current_angle_data', None)
    
    pixel_size_x = image_data.get('pixel_size_x')
    pixel_size_y = image_data.get('pixel_size_y')
    
    # Handle missing pixel size with default and warning
    if pixel_size_x is None:
        pixel_size_x = 0.1
        pixel_size_y = 0.1
        st.warning("No geospatial data found. Using default scale: 10cm per pixel.")
        
        # Add manual scale calibration option
        with st.expander("Manual Scale Calibration"):
            st.info("For accurate measurements, set the scale based on known distances in your image.")
            manual_scale = st.number_input(
                "Meters per pixel", 
                min_value=0.001, 
                max_value=10.0, 
                value=0.1, 
                step=0.001,
                format="%.3f",
                help="Estimate based on known objects in the image (e.g., car = ~4.5m, building width, etc.)"
            )
            pixel_size_x = manual_scale
            pixel_size_y = manual_scale
            
    elif pixel_size_y is None:
        pixel_size_y = pixel_size_x
    
    # Calculate areas with angle correction
    area_results = area_calc.calculate_multiple_polygons(
        st.session_state.polygons, 
        pixel_size_x, 
        pixel_size_y,
        angle_data
    )
    
    # Display area summary
    st.subheader("Area Summary")
    
    # Show both apparent and corrected areas if correction applied
    if area_results['angle_correction_summary']['correction_applied']:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Apparent Area", f"{area_results['total_apparent_area_m2']:.1f} m²")
            st.metric("Apparent Area (sq ft)", f"{area_results['total_apparent_area_sqft']:.1f} ft²")
        
        with col2:
            st.metric("Corrected Area", f"{area_results['total_corrected_area_m2']:.1f} m²")
            st.metric("Corrected Area (sq ft)", f"{area_results['total_corrected_area_sqft']:.1f} ft²")
        
        # Show correction summary
        correction_summary = area_results['angle_correction_summary']
        st.info(f"Angle Correction Applied: +{correction_summary['total_area_difference_m2']:.1f} m² "
               f"({correction_summary['total_area_difference_percent']:.1f}% increase)")
    else:
        st.metric("Total Area", f"{area_results['total_corrected_area_m2']:.1f} m²")
        st.metric("Total Area (sq ft)", f"{area_results['total_corrected_area_sqft']:.1f} ft²")
    
    st.metric("Number of Areas", area_results['polygon_count'])
    
    # Material selection and calculation using corrected areas
    st.subheader("Material Selection")
    
    while len(st.session_state.polygon_materials) < len(st.session_state.polygons):
        st.session_state.polygon_materials.append('asphalt')
    
    available_materials = material_calc.get_available_materials()
    material_options = {mat['key']: f"{mat['name']} (${mat['cost_per_unit']}/{mat['unit']})" 
                       for mat in available_materials}
    
    materials_changed = False
    for i in range(len(st.session_state.polygons)):
        current_material = st.session_state.polygon_materials[i]
        
        new_material = st.selectbox(
            f"Material for Area {i+1}",
            options=list(material_options.keys()),
            format_func=lambda x: material_options[x],
            index=list(material_options.keys()).index(current_material) if current_material in material_options else 0,
            key=f"material_{i}"
        )
        
        if new_material != current_material:
            st.session_state.polygon_materials[i] = new_material
            materials_changed = True
    
    if materials_changed:
        st.rerun()
    
    # Calculate costs using corrected areas
    st.subheader("Cost Breakdown")
    
    total_project_cost = 0.0
    area_costs = []
    
    # Use corrected areas for cost calculations
    corrected_areas = area_results['individual_corrected_areas_m2']
    
    for i, (area_m2, material_key) in enumerate(zip(corrected_areas, st.session_state.polygon_materials)):
        
        cost_result = material_calc.calculate_material_cost(area_m2, material_key)
        
        if 'error' not in cost_result:
            area_costs.append(cost_result)
            total_project_cost += cost_result['total_cost']
            
            with st.expander(f"Area {i+1} - {cost_result['material_name']}"):
                st.write(f"**Corrected Area:** {area_m2:.1f} m²")
                
                # Show apparent vs corrected if different
                apparent_area = area_results['individual_areas_m2'][i]
                if abs(area_m2 - apparent_area) > 0.1:
                    st.write(f"**Apparent Area:** {apparent_area:.1f} m²")
                    st.write(f"**Angle Correction:** +{(area_m2 - apparent_area):.1f} m²")
                
                st.write(f"**Material Cost:** ${cost_result['primary_material']['total_cost']:.2f}")
                st.write(f"**Installation:** ${cost_result['installation_cost']:.2f}")
                
                if cost_result['additional_materials']:
                    st.write("**Additional Materials:**")
                    for mat_name, mat_data in cost_result['additional_materials'].items():
                        st.write(f"- {mat_name}: {mat_data['quantity']:.1f} {mat_data['unit']} = ${mat_data['total_cost']:.2f}")
                
                st.write(f"**Total for Area:** ${cost_result['total_cost']:.2f}")
        else:
            st.error(f"Area {i+1}: {cost_result['error']}")
    
    # Project totals
    st.subheader("Project Totals")
    st.metric("Total Project Cost", f"${total_project_cost:.2f}")
    
    if area_results['total_corrected_area_m2'] > 0:
        cost_per_m2 = total_project_cost / area_results['total_corrected_area_m2']
        st.metric("Average Cost per m²", f"${cost_per_m2:.2f}")

def create_demo_image():
    """Create a simple demo image for testing."""
    try:
        height, width = 600, 800
        demo_array = np.ones((height, width, 3), dtype=np.uint8) * 120
        
        cv2.rectangle(demo_array, (100, 200), (700, 350), (80, 80, 80), -1)
        cv2.rectangle(demo_array, (150, 50), (400, 180), (60, 60, 60), -1)
        cv2.rectangle(demo_array, (50, 350), (750, 400), (100, 100, 100), -1)
        
        cv2.putText(demo_array, "CONSTRUCTION SITE", (250, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return {
            'array': demo_array,
            'metadata': {
                'width': width,
                'height': height,
                'mode': 'RGB',
                'source': 'Demo Image'
            },
            'has_geospatial': False,
            'pixel_size_x': 0.1,
            'pixel_size_y': 0.1,
            'file_path': None
        }
        
    except Exception as e:
        st.error(f"Error creating demo image: {e}")
        return None

def main():
    """Main application function."""
    
    st.title("Image Resource Planner")
    st.markdown("Upload and preview geospatial images for construction resource planning")
    
    # Initialize calculators and extractors
    if 'area_calculator' not in st.session_state:
        st.session_state.area_calculator = AreaCalculator()
    if 'material_calculator' not in st.session_state:
        st.session_state.material_calculator = MaterialCalculator()
    if 'auto_detector' not in st.session_state:
        st.session_state.auto_detector = SAMAutoDetection()
    if 'angle_extractor' not in st.session_state:
        st.session_state.angle_extractor = AngleExtractor()
    
    # Initialize session state
    if 'current_image' not in st.session_state:
        st.session_state.current_image = None
    if 'current_angle_data' not in st.session_state:
        st.session_state.current_angle_data = None
    if 'polygons' not in st.session_state:
        st.session_state.polygons = []
    if 'current_polygon' not in st.session_state:
        st.session_state.current_polygon = []
    if 'polygon_materials' not in st.session_state:
        st.session_state.polygon_materials = []
    if 'pixel_warning_shown' not in st.session_state:
        st.session_state.pixel_warning_shown = False
    
    # Create layout with three columns
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.header("Image Upload and Area Selection")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['tiff', 'tif', 'png', 'jpg', 'jpeg'],
            help="Upload TIFF files (with geospatial data) or standard image formats"
        )
        
        if uploaded_file is not None:
            st.success(f"File uploaded: {uploaded_file.name}")
            file_size_mb = uploaded_file.size / (1024*1024)
            st.info(f"File size: {file_size_mb:.2f} MB")
            
            file_extension = uploaded_file.name.lower().split('.')[-1]
            
            if file_extension in ['tiff', 'tif']:
                st.write("Loading TIFF image...")
                image_data = load_tiff_image(uploaded_file)
            else:
                st.write("Loading standard image...")
                image_data = load_standard_image(uploaded_file)
            
            if image_data is not None:
                st.session_state.current_image = image_data
                
                # Extract and display angle information
                angle_data = extract_and_display_angle_info(image_data)
                st.session_state.current_angle_data = angle_data
                
                # Display metadata
                display_image_metadata(
                    image_data['metadata'],
                    image_data['has_geospatial'],
                    image_data.get('pixel_size_x'),
                    image_data.get('pixel_size_y')
                )
        
        # Display image and area selection interface
        if st.session_state.current_image is not None:
            display_area_selection_interface()
        
        else:
            # Demo option
            if st.button("Create Demo Image"):
                demo_image = create_demo_image()
                if demo_image:
                    st.session_state.current_image = demo_image
                    st.session_state.current_angle_data = None
                    st.success("Demo image created!")
                    st.rerun()
            
            st.info("Please upload an image file to begin")
            
            with st.expander("Supported Formats"):
                st.markdown("""
                **TIFF/TIF files:**
                - Supports georeferenced images with spatial data
                - Automatic scale detection from metadata
                - Preferred format for accurate measurements
                
                **Standard formats (PNG, JPG, JPEG):**
                - Basic image support
                - Manual scale calibration required
                - Good for testing and demos
                """)
    
    with col2:
        st.header("Area Management")
        
        st.subheader("Status")
        st.write(f"**Completed Areas:** {len(st.session_state.polygons)}")
        st.write(f"**Current Area Points:** {len(st.session_state.current_polygon)}")
        
        if st.session_state.polygons and st.session_state.current_image:
            st.subheader("Area Details")
            
            area_calc = st.session_state.area_calculator
            image_data = st.session_state.current_image
            angle_data = st.session_state.current_angle_data
            pixel_size_x = image_data.get('pixel_size_x')
            
            # Handle missing pixel size with default and warning
            if pixel_size_x is None:
                pixel_size_x = 0.1
                if not hasattr(st.session_state, 'pixel_warning_shown'):
                    st.warning("No geospatial data found. Using default scale: 10cm per pixel. Measurements may be inaccurate.")
                    st.session_state.pixel_warning_shown = True
            
            for i, polygon in enumerate(st.session_state.polygons):
                area_result = area_calc.calculate_corrected_area(
                    polygon, pixel_size_x, pixel_size_x, angle_data
                )
                
                corrected_area_m2 = area_result['corrected_area_m2']
                
                with st.expander(f"Area {i+1} - {corrected_area_m2:.1f} m²"):
                    st.write(f"**Points:** {len(polygon)}")
                    st.write(f"**Corrected Area:** {corrected_area_m2:.1f} m² ({corrected_area_m2 * 10.764:.1f} ft²)")
                    
                    if area_result['correction_applied']:
                        apparent_area = area_result['apparent_area_m2']
                        st.write(f"**Apparent Area:** {apparent_area:.1f} m²")
                        st.write(f"**Correction:** +{area_result['area_difference_m2']:.1f} m² ({area_result['area_difference_percent']:.1f}%)")
                    
                    for j, point in enumerate(polygon[:3]):
                        st.text(f"Point {j+1}: ({point[0]}, {point[1]})")
                    if len(polygon) > 3:
                        st.text(f"... and {len(polygon) - 3} more points")
                    
                    if st.button(f"Delete Area {i+1}", key=f"delete_{i}"):
                        st.session_state.polygons.pop(i)
                        if i < len(st.session_state.polygon_materials):
                            st.session_state.polygon_materials.pop(i)
                        st.rerun()
    
    with col3:
        display_calculation_panel()

if __name__ == "__main__":
    main()