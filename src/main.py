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
    layout="wide"
)

def load_tiff_image(uploaded_file):
    """Load TIFF image with geospatial data using rasterio."""
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
    """Load standard image formats (PNG, JPG, etc.) with angle extraction."""
    tmp_path = None
    try:
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
        st.error(f"Error loading image from path: {str(e)}")
        return None

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

def extract_and_display_angle_info(image_data):
    """Extract and display angle information from image."""
    angle_extractor = st.session_state.angle_extractor
    
    if 'file_path' not in image_data or not image_data['file_path']:
        return None
    
    try:
        angle_data = angle_extractor.extract_angles_from_image(image_data['file_path'])
        
        # Only show angle information if there's actual angle data
        if angle_data['has_angle_data']:
            st.subheader("Camera Angle Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Image Type:** {angle_data['image_type'].replace('_', ' ').title()}")
                if angle_data['camera_model']:
                    st.write(f"**Camera:** {angle_data['camera_model']}")
            
            with col2:
                st.write(f"**Pitch Angle:** {angle_data['pitch_angle']:.1f}°")
                st.write(f"**Roll Angle:** {angle_data['roll_angle']:.1f}°")
                st.write(f"**Correction Factor:** {angle_data['correction_factor']:.3f}")
            
            description = angle_extractor.get_angle_description(angle_data)
            if angle_data['is_perpendicular']:
                st.success(description)
            elif angle_data['image_type'] == 'orthorectified':
                st.info(description)
            else:
                st.warning(description)
            
            warning = angle_extractor.get_angle_warning(angle_data)
            if warning:
                st.warning(warning)
        
        return angle_data
        
    except Exception as e:
        st.error(f"Error extracting angle data: {str(e)}")
        return None

def display_image_metadata(metadata, has_geospatial, pixel_size_x=None, pixel_size_y=None):
    """Display image metadata in formatted way."""
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
    """Display the area selection interface with smart/manual detection modes."""
    
    st.subheader("Area Selection")
    
    image_data = st.session_state.current_image
    auto_detector = st.session_state.auto_detector
    
    # Initialize selection mode if not exists
    if 'selection_mode' not in st.session_state:
        st.session_state.selection_mode = 'smart'
    
    # Initialize edit mode
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'editing_area_index' not in st.session_state:
        st.session_state.editing_area_index = -1
    
    # Selection mode toggle
    st.write("**Selection Mode:**")
    col_mode1, col_mode2 = st.columns(2)
    
    with col_mode1:
        if st.button("Smart Mode", 
                    type="primary" if st.session_state.selection_mode == 'smart' else "secondary",
                    use_container_width=True):
            st.session_state.selection_mode = 'smart'
            st.session_state.current_polygon = []
            st.session_state.edit_mode = False
            st.rerun()
    
    with col_mode2:
        if st.button("Manual Mode", 
                    type="primary" if st.session_state.selection_mode == 'manual' else "secondary",
                    use_container_width=True):
            st.session_state.selection_mode = 'manual'
            st.session_state.edit_mode = False
            st.rerun()
    
    # Edit mode controls
    if st.session_state.edit_mode:
        st.write("**Edit Mode:** Adjusting corners for Area", st.session_state.editing_area_index + 1)
        col_edit1, col_edit2 = st.columns(2)
        
        with col_edit1:
            if st.button("Save Changes", type="primary", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.editing_area_index = -1
                st.success("Area updated successfully")
                st.rerun()
        
        with col_edit2:
            if st.button("Cancel Edit", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.editing_area_index = -1
                st.rerun()
    
    # Mode-specific controls
    elif st.session_state.selection_mode == 'manual':
        # Manual mode controls
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("Start New Area", use_container_width=True):
                st.session_state.current_polygon = []
                st.rerun()
        
        with col_b:
            if st.button("Complete Area", use_container_width=True):
                if len(st.session_state.current_polygon) >= 3:
                    st.session_state.polygons.append(st.session_state.current_polygon.copy())
                    st.session_state.current_polygon = []
                    st.success("Area completed successfully")
                    st.rerun()
                else:
                    st.warning("Need at least 3 points to complete an area")
        
        with col_c:
            if st.button("Clear All Areas", use_container_width=True):
                st.session_state.polygons = []
                st.session_state.current_polygon = []
                st.rerun()
    
    else:
        # Smart mode controls
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Clear All Areas", use_container_width=True):
                st.session_state.polygons = []
                st.session_state.current_polygon = []
                st.rerun()
        
        with col_b:
            # Show area count
            st.metric("Areas Selected", len(st.session_state.polygons))
    
    # Show detection capability status
    detection_info = auto_detector.get_detection_info()
    if detection_info['sam_available']:
        st.success("AI Detection: SAM Model Active")
    else:
        st.warning("AI Detection: Basic CV Mode")
        with st.expander("Enable SAM AI Detection"):
            st.markdown(auto_detector.download_sam_instructions())
    
    # Mode-specific instructions
    if st.session_state.edit_mode:
        st.info("**Edit Mode:** Click and drag corner points to adjust the area boundaries")
    elif st.session_state.selection_mode == 'smart':
        st.info("**Smart Mode:** Click once on any area to automatically detect it. Click on area corners to edit boundaries.")
    else:
        st.info("**Manual Mode:** Click multiple points to draw polygon, then click 'Complete Area'")
        
        if st.session_state.current_polygon:
            st.write("**Current Area Points:**")
            for i, point in enumerate(st.session_state.current_polygon):
                st.text(f"Point {i+1}: ({point[0]}, {point[1]})")
    
    display_interactive_image(image_data)

def display_interactive_image(image_data):
    """Display the interactive image with click detection, polygon overlays, and drag-to-edit corners."""
    
    display_array = image_data['array'].copy()
    auto_detector = st.session_state.auto_detector
    
    # Initialize click tracking and drag state
    if 'processing_click' not in st.session_state:
        st.session_state.processing_click = False
    if 'last_processed_click' not in st.session_state:
        st.session_state.last_processed_click = None
    if 'selected_corner' not in st.session_state:
        st.session_state.selected_corner = None  # (area_index, corner_index)
    if 'dragging_corner' not in st.session_state:
        st.session_state.dragging_corner = False
    
    # Draw completed polygons
    for i, polygon in enumerate(st.session_state.polygons):
        if len(polygon) >= 3:
            overlay = display_array.copy()
            points = np.array(polygon, dtype=np.int32)
            
            # Fill polygon with different colors for edit mode
            if st.session_state.edit_mode and i == st.session_state.editing_area_index:
                cv2.fillPoly(overlay, [points], (255, 255, 0))  # Yellow for editing
                display_array = cv2.addWeighted(display_array, 0.6, overlay, 0.4, 0)
                cv2.polylines(display_array, [points], True, (255, 200, 0), 3)  # Thicker yellow outline
            else:
                cv2.fillPoly(overlay, [points], (0, 255, 0))  # Green for completed
                display_array = cv2.addWeighted(display_array, 0.7, overlay, 0.3, 0)
                cv2.polylines(display_array, [points], True, (0, 200, 0), 2)
            
            # Draw corner points with enhanced visibility
            for j, point in enumerate(polygon):
                if st.session_state.edit_mode and i == st.session_state.editing_area_index:
                    # Check if this corner is selected
                    is_selected = (st.session_state.selected_corner == (i, j))
                    
                    if is_selected:
                        # Selected corner - larger and different color
                        cv2.circle(display_array, tuple(point), 12, (0, 0, 255), -1)  # Blue center
                        cv2.circle(display_array, tuple(point), 12, (255, 255, 255), 3)  # White border
                        cv2.circle(display_array, tuple(point), 15, (0, 0, 0), 2)  # Black outer border
                    else:
                        # Regular editable corners
                        cv2.circle(display_array, tuple(point), 8, (255, 0, 0), -1)  # Red corners
                        cv2.circle(display_array, tuple(point), 8, (255, 255, 255), 2)  # White border
                else:
                    cv2.circle(display_array, tuple(point), 4, (0, 255, 0), -1)
            
            # Add area label
            center_x = int(np.mean([p[0] for p in polygon]))
            center_y = int(np.mean([p[1] for p in polygon]))
            label_color = (0, 0, 255) if st.session_state.edit_mode and i == st.session_state.editing_area_index else (255, 255, 255)
            cv2.putText(display_array, f"Area {i+1}", (center_x-30, center_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, label_color, 2)
    
    # Draw current polygon being created (manual mode only)
    if st.session_state.selection_mode == 'manual' and len(st.session_state.current_polygon) >= 2:
        points = np.array(st.session_state.current_polygon, dtype=np.int32)
        cv2.polylines(display_array, [points], False, (255, 0, 0), 2)
    
    # Draw current polygon points (manual mode only)
    if st.session_state.selection_mode == 'manual':
        for point in st.session_state.current_polygon:
            cv2.circle(display_array, tuple(point), 4, (255, 0, 0), -1)
    
    # Convert to PIL Image for streamlit_image_coordinates
    pil_image = Image.fromarray(display_array)
    
    # Display interactive image with click detection
    coordinates = streamlit_image_coordinates(
        pil_image,
        key="image_coordinates"
    )
    
    # Handle click events based on selection mode
    if coordinates is not None and not st.session_state.processing_click:
        x, y = int(coordinates["x"]), int(coordinates["y"])
        current_click = f"{x}_{y}"
        
        # Prevent processing the same click multiple times
        if st.session_state.last_processed_click == current_click:
            return
        
        st.session_state.last_processed_click = current_click
        st.session_state.processing_click = True
        
        try:
            if st.session_state.edit_mode:
                # Edit mode: Handle corner selection and dragging
                editing_polygon = st.session_state.polygons[st.session_state.editing_area_index]
                area_index = st.session_state.editing_area_index
                
                # Check if user clicked on a corner point
                corner_clicked = False
                for j, corner in enumerate(editing_polygon):
                    distance = np.sqrt((x - corner[0])**2 + (y - corner[1])**2)
                    if distance <= 15:  # Within 15 pixels of corner for easier selection
                        if st.session_state.selected_corner == (area_index, j):
                            # Clicking on already selected corner - deselect it
                            st.session_state.selected_corner = None
                            st.session_state.dragging_corner = False
                            st.info("Corner deselected. Click on a corner to select it for dragging.")
                        else:
                            # Select this corner for dragging
                            st.session_state.selected_corner = (area_index, j)
                            st.session_state.dragging_corner = True
                            st.success(f"Corner {j+1} selected. Click anywhere to move it to that position.")
                        corner_clicked = True
                        break
                
                if not corner_clicked:
                    # Clicked somewhere else - if a corner is selected, move it here
                    if st.session_state.selected_corner is not None:
                        selected_area, selected_corner_idx = st.session_state.selected_corner
                        
                        # Move the selected corner to the new position
                        st.session_state.polygons[selected_area][selected_corner_idx] = [x, y]
                        
                        # Clear selection after moving
                        st.session_state.selected_corner = None
                        st.session_state.dragging_corner = False
                        
                        st.success(f"Corner moved to ({x}, {y})")
                    else:
                        st.info("Click on a corner point (red circles) to select it, then click where you want to move it.")
            
            elif st.session_state.selection_mode == 'smart':
                # Smart mode: Check if user clicked on existing area corner or new area
                clicked_on_existing = False
                
                # Check if clicked on corner of existing polygon for editing
                for poly_index, polygon in enumerate(st.session_state.polygons):
                    for corner in polygon:
                        distance = np.sqrt((x - corner[0])**2 + (y - corner[1])**2)
                        if distance <= 10:  # Within 10 pixels of corner
                            st.session_state.edit_mode = True
                            st.session_state.editing_area_index = poly_index
                            st.session_state.selected_corner = None  # Clear any previous selection
                            st.session_state.dragging_corner = False
                            clicked_on_existing = True
                            st.info(f"Editing Area {poly_index + 1}. Click on corner points to select and drag them.")
                            break
                    if clicked_on_existing:
                        break
                
                # If not clicking on existing corner, detect new area
                if not clicked_on_existing:
                    # Check if clicking inside an existing area to prevent overlaps
                    clicked_inside_existing = False
                    for polygon in st.session_state.polygons:
                        if len(polygon) >= 3:
                            points = np.array(polygon, dtype=np.int32)
                            if cv2.pointPolygonTest(points, (x, y), False) >= 0:
                                clicked_inside_existing = True
                                st.warning("Clicked inside existing area. Click outside existing areas to detect new ones.")
                                break
                    
                    if not clicked_inside_existing:
                        # Show brief loading message
                        status_placeholder = st.empty()
                        status_placeholder.info(f"Detecting area at ({x}, {y})...")
                        
                        try:
                            detected_areas = auto_detector.detect_with_points(
                                image_data['array'],
                                [(x, y)],
                                [1]  # Foreground point
                            )
                            
                            status_placeholder.empty()  # Clear loading message
                            
                            if detected_areas and len(detected_areas) > 0:
                                # Take only the first detected area to prevent multiples
                                area = detected_areas[0]
                                if len(area) >= 3:  # Valid polygon
                                    st.session_state.polygons.append(area)
                                    st.success("Area detected and added successfully")
                                else:
                                    st.warning("Detected area was too small or invalid")
                            else:
                                st.warning(f"No area detected at ({x}, {y}). Try clicking on a different part of the object.")
                        
                        except Exception as e:
                            status_placeholder.empty()
                            st.error(f"Detection failed: {str(e)}")
            
            else:
                # Manual mode: Multi-point polygon creation
                if [x, y] not in st.session_state.current_polygon:
                    st.session_state.current_polygon.append([x, y])
                    st.success(f"Point added: ({x}, {y})")
        
        finally:
            # Reset processing flag after a short delay
            st.session_state.processing_click = False
            if not st.session_state.edit_mode or not st.session_state.dragging_corner:
                # Only rerun if not in active dragging mode to prevent interruption
                st.rerun()

def display_calculation_panel():
    """Display calculation and material estimation panel with corrected cubic meter calculations."""
    
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
    st.subheader("Material Selection & Volume Calculations")
    
    # Initialize material and depth lists
    while len(st.session_state.polygon_materials) < len(st.session_state.polygons):
        st.session_state.polygon_materials.append('asphalt')
    
    # Initialize depth list for volume calculations
    if 'polygon_depths' not in st.session_state:
        st.session_state.polygon_depths = []
    while len(st.session_state.polygon_depths) < len(st.session_state.polygons):
        st.session_state.polygon_depths.append(0.10)  # Default 10cm depth
    
    available_materials = material_calc.get_available_materials()
    material_options = {mat['key']: f"{mat['name']} (€{mat['cost_per_unit']:.0f}/m³)" 
                       for mat in available_materials}
    
    materials_changed = False
    for i in range(len(st.session_state.polygons)):
        st.write(f"**Area {i+1} Configuration:**")
        
        # Material selection
        current_material = st.session_state.polygon_materials[i]
        new_material = st.selectbox(
            f"Material for Area {i+1}",
            options=list(material_options.keys()),
            format_func=lambda x: material_options[x],
            index=list(material_options.keys()).index(current_material) if current_material in material_options else 0,
            key=f"material_{i}",
            label_visibility="collapsed"
        )
        
        if new_material != current_material:
            st.session_state.polygon_materials[i] = new_material
            materials_changed = True
        
        # Get material info for depth recommendations
        material_profile = material_calc.get_material_profile(new_material)
        min_thickness = material_profile.get('minimum_thickness_m', 0.05)
        default_thickness = material_profile.get('thickness_m', 0.10)
        
        # Custom cost input option
        default_cost = material_profile.get('cost_per_unit', 0)
        
        col_cost1, col_cost2 = st.columns([2, 1])
        with col_cost1:
            # Initialize custom costs if not exists
            if 'polygon_custom_costs' not in st.session_state:
                st.session_state.polygon_custom_costs = {}
            
            current_cost = st.session_state.polygon_custom_costs.get(f"{i}_{new_material}", default_cost)
            new_cost = st.number_input(
                f"Custom Cost (€/m³)",
                min_value=0.01,
                max_value=2000.0,
                value=float(current_cost),
                step=1.0,
                format="%.0f",
                key=f"cost_{i}",
                help=f"Default: €{default_cost:.0f}/m³"
            )
            
            if abs(new_cost - current_cost) > 0.1:
                st.session_state.polygon_custom_costs[f"{i}_{new_material}"] = new_cost
                materials_changed = True
        
        with col_cost2:
            if st.button(f"Reset to Default", key=f"reset_cost_{i}"):
                if f"{i}_{new_material}" in st.session_state.polygon_custom_costs:
                    del st.session_state.polygon_custom_costs[f"{i}_{new_material}"]
                materials_changed = True
        
        # Depth/Height input with minimum enforcement
        col1, col2 = st.columns([2, 1])
        
        with col1:
            current_depth = st.session_state.polygon_depths[i]
            new_depth = st.number_input(
                f"Thickness for Area {i+1} (meters)",
                min_value=min_thickness,  # Enforce minimum
                max_value=5.0,
                value=max(current_depth, min_thickness),  # Ensure we're above minimum
                step=0.01,
                format="%.3f",
                key=f"depth_{i}",
                help=f"Minimum {min_thickness*100:.0f}cm for {material_profile['name']}. Default: {default_thickness*100:.0f}cm"
            )
            
            if abs(new_depth - current_depth) > 0.001:
                st.session_state.polygon_depths[i] = new_depth
                materials_changed = True
            
            # Show thickness info
            if new_depth == min_thickness:
                st.info(f"Using minimum thickness: {min_thickness*100:.0f}cm")
            elif new_depth == default_thickness:
                st.success(f"Using default thickness: {default_thickness*100:.0f}cm")
        
        with col2:
            # Show volume preview
            if i < len(area_results['individual_corrected_areas_m2']):
                area_m2 = area_results['individual_corrected_areas_m2'][i]
                volume_m3 = area_m2 * new_depth
                st.metric("Volume", f"{volume_m3:.2f} m³")
        
        st.write("---")  # Separator between areas
    
    if materials_changed:
        st.rerun()
    
    # Calculate costs using corrected areas and volumes
    st.subheader("Cost Breakdown")
    
    total_project_cost = 0.0
    area_costs = []
    
    # Use corrected areas for cost calculations
    corrected_areas = area_results['individual_corrected_areas_m2']
    
    for i, (area_m2, material_key) in enumerate(zip(corrected_areas, st.session_state.polygon_materials)):
        
        # Get depth for volume calculation
        depth_m = st.session_state.polygon_depths[i] if i < len(st.session_state.polygon_depths) else 0.1
        
        # Get custom cost if set
        custom_cost_key = f"{i}_{material_key}"
        material_profile = material_calc.get_material_profile(material_key)
        original_cost = material_profile.get('cost_per_unit', 0)
        custom_cost = st.session_state.polygon_custom_costs.get(custom_cost_key, original_cost)
        
        # Temporarily update material profile with custom cost
        if abs(custom_cost - original_cost) > 0.1:
            material_calc.material_profiles[material_key]['cost_per_unit'] = custom_cost
        
        # Calculate cost using area and custom thickness (NOT volume)
        # This ensures proper minimum thickness enforcement
        cost_result = material_calc.calculate_material_cost(area_m2, material_key, depth_m, is_volume=False)
        
        # Restore original cost
        if abs(custom_cost - original_cost) > 0.1:
            material_calc.material_profiles[material_key]['cost_per_unit'] = original_cost
        
        if 'error' not in cost_result:
            area_costs.append(cost_result)
            total_project_cost += cost_result['total_cost']
            
            with st.expander(f"Area {i+1} - {cost_result['material_name']} ({cost_result['effective_volume_m3']:.2f} m³)"):
                st.write(f"**Surface Area:** {area_m2:.1f} m²")
                st.write(f"**Thickness:** {depth_m:.3f} m")
                st.write(f"**Volume:** {cost_result['volume_m3']:.2f} m³")
                st.write(f"**Effective Volume (with waste):** {cost_result['effective_volume_m3']:.2f} m³")
                
                # Show apparent vs corrected if different
                if i < len(area_results['individual_areas_m2']):
                    apparent_area = area_results['individual_areas_m2'][i]
                    if abs(area_m2 - apparent_area) > 0.1:
                        st.write(f"**Apparent Area:** {apparent_area:.1f} m²")
                        st.write(f"**Angle Correction:** +{(area_m2 - apparent_area):.1f} m²")
                
                # Show calculation breakdown
                effective_vol = cost_result['effective_volume_m3']
                unit_cost = cost_result['primary_material']['cost_per_unit']
                material_cost = cost_result['primary_material']['total_cost']
                
                st.write(f"**Calculation:** {effective_vol:.2f} m³ × €{unit_cost:.0f}/m³ = €{material_cost:.2f}")
                
                if abs(custom_cost - original_cost) > 0.1:
                    st.write(f"**Custom Cost:** €{custom_cost:.0f}/m³ (Default: €{original_cost:.0f}/m³)")
                
                st.write(f"**Material Cost:** €{cost_result['primary_material']['total_cost']:.2f}")
                st.write(f"**Installation:** €{cost_result['installation_cost']:.2f}")
                
                if cost_result['additional_materials']:
                    st.write("**Additional Materials:**")
                    for mat_name, mat_data in cost_result['additional_materials'].items():
                        st.write(f"- {mat_name}: {mat_data['quantity']:.1f} {mat_data['unit']} = €{mat_data['total_cost']:.2f}")
                
                st.write(f"**Total for Area:** €{cost_result['total_cost']:.2f}")
                st.write(f"**Cost per m²:** €{cost_result['cost_per_m2']:.2f}")
                st.write(f"**Cost per m³:** €{cost_result['cost_per_m3']:.2f}")
        else:
            st.error(f"Area {i+1}: {cost_result['error']}")
    
    # Project totals
    st.subheader("Project Totals")
    st.metric("Total Project Cost", f"€{total_project_cost:.2f}")
    
    if area_results['total_corrected_area_m2'] > 0:
        cost_per_m2 = total_project_cost / area_results['total_corrected_area_m2']
        st.metric("Average Cost per m²", f"€{cost_per_m2:.2f}")

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
    if 'polygon_depths' not in st.session_state:
        st.session_state.polygon_depths = []
    if 'polygon_custom_costs' not in st.session_state:
        st.session_state.polygon_custom_costs = {}
    if 'selection_mode' not in st.session_state:
        st.session_state.selection_mode = 'smart'  # Default to smart mode
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'editing_area_index' not in st.session_state:
        st.session_state.editing_area_index = -1
    if 'processing_click' not in st.session_state:
        st.session_state.processing_click = False
    if 'last_processed_click' not in st.session_state:
        st.session_state.last_processed_click = None
    
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
                image_data = load_tiff_image(uploaded_file)
            else:
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
            pixel_size_x = image_data.get('pixel_size_x', 0.1)
            
            for i, polygon in enumerate(st.session_state.polygons):
                area_result = area_calc.calculate_corrected_area(
                    polygon, pixel_size_x, pixel_size_x, angle_data
                )
                
                corrected_area_m2 = area_result['corrected_area_m2']
                
                # Get depth if available
                depth_m = st.session_state.polygon_depths[i] if i < len(st.session_state.polygon_depths) else 0.1
                volume_m3 = corrected_area_m2 * depth_m
                
                with st.expander(f"Area {i+1} - {corrected_area_m2:.1f} m² × {depth_m:.3f}m = {volume_m3:.2f} m³"):
                    st.write(f"**Points:** {len(polygon)}")
                    st.write(f"**Corrected Area:** {corrected_area_m2:.1f} m²")
                    st.write(f"**Thickness:** {depth_m:.3f} m")
                    st.write(f"**Volume:** {volume_m3:.2f} m³")
                    
                    if area_result['correction_applied']:
                        apparent_area = area_result['apparent_area_m2']
                        st.write(f"**Apparent Area:** {apparent_area:.1f} m²")
                        st.write(f"**Correction:** +{area_result['area_difference_m2']:.1f} m² ({area_result['area_difference_percent']:.1f}%)")
                    
                    for j, point in enumerate(polygon[:3]):
                        st.text(f"Point {j+1}: ({point[0]}, {point[1]})")
                    if len(polygon) > 3:
                        st.text(f"... and {len(polygon) - 3} more points")
                    
                    # Area management buttons
                    col_edit, col_delete = st.columns(2)
                    
                    with col_edit:
                        if st.button(f"Edit Area {i+1}", key=f"edit_area_{i}", use_container_width=True):
                            st.session_state.edit_mode = True
                            st.session_state.editing_area_index = i
                            st.session_state.selection_mode = 'smart'  # Switch to smart mode for editing
                            st.rerun()
                    
                    with col_delete:
                        if st.button(f"Delete Area {i+1}", key=f"delete_{i}", use_container_width=True):
                            # Clean up all associated data
                            st.session_state.polygons.pop(i)
                            if i < len(st.session_state.polygon_materials):
                                material_key = st.session_state.polygon_materials[i]
                                st.session_state.polygon_materials.pop(i)
                                # Clean up custom cost for this area
                                cost_key = f"{i}_{material_key}"
                                if cost_key in st.session_state.polygon_custom_costs:
                                    del st.session_state.polygon_custom_costs[cost_key]
                            if i < len(st.session_state.polygon_depths):
                                st.session_state.polygon_depths.pop(i)
                            # Reset edit mode if editing this area
                            if st.session_state.editing_area_index == i:
                                st.session_state.edit_mode = False
                                st.session_state.editing_area_index = -1
                            st.rerun()
    
    with col3:
        display_calculation_panel()

if __name__ == "__main__":
    main()