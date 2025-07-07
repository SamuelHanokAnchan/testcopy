"""
SAM (Segment Anything Model) integration for automatic area detection.
Provides state-of-the-art AI-powered area detection for construction planning.
"""

import cv2
import numpy as np
import os
from typing import List, Tuple, Optional
import streamlit as st


class SAMAutoDetection:
    """
    Handles automatic detection using Meta's Segment Anything Model (SAM).
    Falls back to basic computer vision if SAM is not available.
    """
    
    def __init__(self):
        self.sam_available = False
        self.predictor = None
        self.model = None
        self._initialize_sam()
    
    def _initialize_sam(self):
        """Initialize SAM model if available."""
        try:
            import torch
            from segment_anything import sam_model_registry, SamPredictor
            
            # Check if CUDA is available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Look for available SAM model files
            models_dir = "models"
            available_models = []
            
            if os.path.exists(models_dir):
                for filename in os.listdir(models_dir):
                    if filename.startswith("sam_vit_") and filename.endswith(".pth"):
                        available_models.append(filename)
            
            if not available_models:
                st.warning("No SAM model weights found. Please download SAM weights to enable AI detection.")
                st.info("Run: python setup_sam.py")
                self._setup_fallback()
                return
            
            # Use the first available model (prefer smaller models)
            model_priority = ["sam_vit_b_01ec64.pth", "sam_vit_l_0b3195.pth", "sam_vit_h_4b8939.pth"]
            selected_model = None
            
            for preferred_model in model_priority:
                if preferred_model in available_models:
                    selected_model = preferred_model
                    break
            
            if not selected_model:
                selected_model = available_models[0]  # Use any available model
            
            # Extract model type from filename
            if "vit_b" in selected_model:
                model_type = "vit_b"
            elif "vit_l" in selected_model:
                model_type = "vit_l"
            elif "vit_h" in selected_model:
                model_type = "vit_h"
            else:
                st.error(f"Unknown SAM model type in file: {selected_model}")
                self._setup_fallback()
                return
            
            checkpoint_path = os.path.join(models_dir, selected_model)
            
            try:
                self.model = sam_model_registry[model_type](checkpoint=checkpoint_path)
                self.model.to(device=device)
                self.predictor = SamPredictor(self.model)
                self.sam_available = True
                st.success(f"SAM model loaded: {selected_model} on {device}")
                
            except FileNotFoundError:
                st.error(f"SAM model file not found: {checkpoint_path}")
                self._setup_fallback()
                
            except Exception as e:
                st.error(f"Failed to load SAM model: {e}")
                self._setup_fallback()
                
        except ImportError:
            st.warning("SAM package not installed. Using basic computer vision detection.")
            st.info("Install with: pip install git+https://github.com/facebookresearch/segment-anything.git")
            self._setup_fallback()
            
        except Exception as e:
            st.warning(f"SAM initialization failed: {e}. Using fallback detection.")
            self._setup_fallback()
    
    def _setup_fallback(self):
        """Setup fallback detection methods."""
        self.sam_available = False
        self.predictor = None
    
    def detect_everything(self, image_array: np.ndarray, min_area: int = 1000, 
                         max_areas: int = 10) -> List[List[List[int]]]:
        """
        Detect all significant areas in the image automatically.
        
        Args:
            image_array: Input image as numpy array
            min_area: Minimum area threshold in pixels
            max_areas: Maximum number of areas to return
            
        Returns:
            List of polygons representing detected areas
        """
        
        if self.sam_available:
            return self._sam_detect_everything(image_array, min_area, max_areas)
        else:
            return self._fallback_detect_everything(image_array, min_area, max_areas)
    
    def detect_with_points(self, image_array: np.ndarray, 
                          point_coords: List[Tuple[int, int]],
                          point_labels: List[int] = None) -> List[List[List[int]]]:
        """
        Detect areas based on user-provided point prompts.
        
        Args:
            image_array: Input image
            point_coords: List of (x, y) coordinates where user clicked
            point_labels: List of labels (1 for foreground, 0 for background)
            
        Returns:
            List of polygons for detected areas
        """
        
        if not point_coords:
            return []
        
        if point_labels is None:
            point_labels = [1] * len(point_coords)  # All foreground points
        
        if self.sam_available:
            return self._sam_detect_with_points(image_array, point_coords, point_labels)
        else:
            return self._fallback_detect_with_points(image_array, point_coords)
    
    def _sam_detect_everything(self, image_array: np.ndarray, min_area: int, 
                              max_areas: int) -> List[List[List[int]]]:
        """Use SAM to detect all areas automatically."""
        
        try:
            from segment_anything import SamAutomaticMaskGenerator
            
            # Set up automatic mask generator
            mask_generator = SamAutomaticMaskGenerator(
                model=self.model,
                points_per_side=32,
                pred_iou_thresh=0.7,
                stability_score_thresh=0.85,
                crop_n_layers=1,
                crop_n_points_downscale_factor=2,
                min_mask_region_area=min_area
            )
            
            # Generate masks
            masks = mask_generator.generate(image_array)
            
            # Convert masks to polygons
            polygons = []
            for mask_data in masks:
                mask = mask_data['segmentation']
                
                # Find contours of the mask
                contours, _ = cv2.findContours(
                    mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > min_area:
                        # Simplify contour
                        epsilon = 0.02 * cv2.arcLength(contour, True)
                        approx = cv2.approxPolyDP(contour, epsilon, True)
                        
                        if len(approx) >= 3:
                            polygon = [[int(point[0][0]), int(point[0][1])] for point in approx]
                            polygons.append((polygon, area, mask_data.get('stability_score', 0)))
            
            # Sort by stability score and area, return top results
            polygons.sort(key=lambda x: (x[2], x[1]), reverse=True)
            return [polygon for polygon, _, _ in polygons[:max_areas]]
            
        except Exception as e:
            st.error(f"SAM detection failed: {e}")
            return self._fallback_detect_everything(image_array, min_area, max_areas)
    
    def _sam_detect_with_points(self, image_array: np.ndarray, 
                               point_coords: List[Tuple[int, int]], 
                               point_labels: List[int]) -> List[List[List[int]]]:
        """Use SAM to detect areas based on point prompts."""
        
        try:
            # Set image for predictor
            self.predictor.set_image(image_array)
            
            # Convert points to numpy arrays
            input_points = np.array(point_coords)
            input_labels = np.array(point_labels)
            
            # Predict masks
            masks, scores, logits = self.predictor.predict(
                point_coords=input_points,
                point_labels=input_labels,
                multimask_output=True
            )
            
            # Convert best mask to polygon
            best_mask_idx = np.argmax(scores)
            best_mask = masks[best_mask_idx]
            
            # Find contours
            contours, _ = cv2.findContours(
                best_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            polygons = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area threshold
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    if len(approx) >= 3:
                        polygon = [[int(point[0][0]), int(point[0][1])] for point in approx]
                        polygons.append(polygon)
            
            return polygons
            
        except Exception as e:
            st.error(f"SAM point detection failed: {e}")
            return self._fallback_detect_with_points(image_array, point_coords)
    
    def _fallback_detect_everything(self, image_array: np.ndarray, min_area: int, 
                                   max_areas: int) -> List[List[List[int]]]:
        """Fallback detection using basic computer vision."""
        
        # Convert to grayscale
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Morphological operations
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        polygons = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                if len(approx) >= 3:
                    polygon = [[int(point[0][0]), int(point[0][1])] for point in approx]
                    polygons.append((polygon, area))
        
        # Sort by area and return top results
        polygons.sort(key=lambda x: x[1], reverse=True)
        return [polygon for polygon, _ in polygons[:max_areas]]
    
    def _fallback_detect_with_points(self, image_array: np.ndarray, 
                                    point_coords: List[Tuple[int, int]]) -> List[List[List[int]]]:
        """Fallback point-based detection using watershed."""
        
        try:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Create markers for watershed
            markers = np.zeros(gray.shape, dtype=np.int32)
            
            # Add foreground markers at click points
            for i, (x, y) in enumerate(point_coords):
                cv2.circle(markers, (x, y), 5, i + 1, -1)
            
            # Add background markers at image borders
            h, w = gray.shape
            cv2.rectangle(markers, (0, 0), (w-1, h-1), len(point_coords) + 1, 3)
            
            # Apply watershed
            markers = cv2.watershed(image_array, markers)
            
            polygons = []
            
            # Extract each watershed region
            for i in range(1, len(point_coords) + 1):
                mask = (markers == i).astype(np.uint8)
                
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 500:
                        epsilon = 0.02 * cv2.arcLength(contour, True)
                        approx = cv2.approxPolyDP(contour, epsilon, True)
                        
                        if len(approx) >= 3:
                            polygon = [[int(point[0][0]), int(point[0][1])] for point in approx]
                            polygons.append(polygon)
            
            return polygons
            
        except Exception as e:
            st.error(f"Fallback detection failed: {e}")
            return []
    
    def get_detection_info(self) -> dict:
        """Get information about current detection capabilities."""
        
        return {
            'sam_available': self.sam_available,
            'detection_methods': [
                'Automatic area detection',
                'Point-based detection',
                'Interactive segmentation'
            ] if self.sam_available else [
                'Basic edge detection',
                'Point-based watershed',
                'Contour detection'
            ],
            'model_info': 'Meta SAM (Segment Anything Model)' if self.sam_available else 'OpenCV Computer Vision',
            'accuracy': 'High (AI-powered)' if self.sam_available else 'Medium (Traditional CV)'
        }
    
    def download_sam_instructions(self) -> str:
        """Get instructions for downloading SAM model."""
        
        return """
        **To enable SAM AI Detection:**
        
        1. **Install SAM package:**
        ```bash
        pip install git+https://github.com/facebookresearch/segment-anything.git
        ```
        
        2. **Download model weights:**
        ```bash
        mkdir models
        cd models
        wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
        ```
        
        3. **Restart the application**
        
        **Model Options:**
        - `sam_vit_h_4b8939.pth` (2.6GB) - Highest accuracy
        - `sam_vit_l_0b3195.pth` (1.2GB) - Good balance  
        - `sam_vit_b_01ec64.pth` (375MB) - Fastest
        
        **Alternative:** Upload weights to your project's `models/` folder.
        """