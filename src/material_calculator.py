"""
Material calculation module for construction resource planning.
All materials converted to cubic meter pricing with same interface.
"""

import json
from typing import Dict, List, Tuple


class MaterialCalculator:
    """
    Handles material calculations for construction projects.
    All materials now priced per m³ for consistency.
    """
    
    def __init__(self):
        self.material_profiles = self._initialize_material_profiles()
    
    def _initialize_material_profiles(self) -> Dict:
        """
        Initialize material profiles - ALL converted to cubic meter pricing.
        
        Returns:
            dict: Material profiles with properties and costs per m³
        """
        return {
            "concrete_tiles": {
                "name": "Concrete Tiles",
                "category": "paving",
                "unit": "m³",
                "cost_per_unit": 416.67,  # €25/m² ÷ 0.06m = €416.67/m³
                "waste_factor": 1.10,
                "thickness_m": 0.06,
                "minimum_thickness_m": 0.06,
                "weight_kg_per_m3": 2400.0,
                "description": "Standard concrete paving tiles",
                "installation_cost_per_m2": 15.00,
                "additional_materials": {
                    "sand_base": {
                        "amount_per_m2": 0.05,
                        "unit": "m³",
                        "cost_per_unit": 30.00
                    },
                    "cement_mortar": {
                        "amount_per_m2": 0.02,
                        "unit": "m³", 
                        "cost_per_unit": 120.00
                    }
                }
            },
            "asphalt": {
                "name": "Asphalt",
                "category": "paving",
                "unit": "m³",
                "cost_per_unit": 300.00,  # €15/m² ÷ 0.05m = €300/m³
                "waste_factor": 1.05,
                "thickness_m": 0.05,
                "minimum_thickness_m": 0.05,
                "weight_kg_per_m3": 2300.0,
                "description": "Hot mix asphalt paving",
                "installation_cost_per_m2": 8.00,
                "additional_materials": {
                    "base_course": {
                        "amount_per_m2": 0.10,
                        "unit": "m³",
                        "cost_per_unit": 25.00
                    }
                }
            },
            "concrete_slab": {
                "name": "Concrete Slab",
                "category": "concrete",
                "unit": "m³",
                "cost_per_unit": 180.00,  # Already in m³
                "waste_factor": 1.08,
                "thickness_m": 0.15,
                "minimum_thickness_m": 0.10,
                "weight_kg_per_m3": 2400.0,
                "description": "Poured concrete slab",
                "installation_cost_per_m2": 25.00,
                "additional_materials": {
                    "rebar": {
                        "amount_per_m2": 8.0,
                        "unit": "kg",
                        "cost_per_unit": 1.20
                    },
                    "formwork": {
                        "amount_per_m2": 1.0,
                        "unit": "m²",
                        "cost_per_unit": 8.00
                    }
                }
            },
            "brick_pavers": {
                "name": "Brick Pavers",
                "category": "paving",
                "unit": "m³",
                "cost_per_unit": 583.33,  # €35/m² ÷ 0.06m = €583.33/m³
                "waste_factor": 1.15,
                "thickness_m": 0.06,
                "minimum_thickness_m": 0.06,
                "weight_kg_per_m3": 1800.0,
                "description": "Clay brick pavers",
                "installation_cost_per_m2": 20.00,
                "additional_materials": {
                    "sand_base": {
                        "amount_per_m2": 0.05,
                        "unit": "m³",
                        "cost_per_unit": 30.00
                    },
                    "joint_sand": {
                        "amount_per_m2": 0.01,
                        "unit": "m³",
                        "cost_per_unit": 35.00
                    }
                }
            },
            "gravel": {
                "name": "Gravel",
                "category": "aggregate",
                "unit": "m³",
                "cost_per_unit": 40.00,  # Already in m³
                "waste_factor": 1.20,
                "thickness_m": 0.10,
                "minimum_thickness_m": 0.05,
                "weight_kg_per_m3": 1600.0,
                "description": "Crushed gravel base",
                "installation_cost_per_m2": 5.00,
                "additional_materials": {}
            }
        }
    
    def get_material_profile(self, material_key: str) -> Dict:
        """Get material profile by key."""
        return self.material_profiles.get(material_key, {})
    
    def get_available_materials(self) -> List[Dict]:
        """Get list of available materials with basic info."""
        materials = []
        for key, profile in self.material_profiles.items():
            materials.append({
                'key': key,
                'name': profile['name'],
                'category': profile['category'],
                'cost_per_unit': profile['cost_per_unit'],
                'unit': profile['unit'],
                'description': profile['description']
            })
        return materials
    
    def calculate_material_quantity(self, area_m2: float, material_key: str, 
                                  custom_thickness: float = None, is_volume: bool = False) -> Dict:
        """
        Calculate material quantity needed for given area.
        Now uses volume-based calculations for all materials.
        
        Args:
            area_m2: Area in square meters OR volume in m³ if is_volume=True
            material_key: Material identifier
            custom_thickness: Override default thickness in meters
            is_volume: If True, area_m2 is treated as volume
            
        Returns:
            dict: Quantity calculation results
        """
        profile = self.get_material_profile(material_key)
        if not profile:
            return {"error": f"Material '{material_key}' not found"}
        
        if is_volume:
            # If volume is provided directly
            volume_m3 = area_m2  # area_m2 is actually volume
            effective_volume = volume_m3 * profile['waste_factor']
            area_for_installation = volume_m3 / (custom_thickness or profile.get('thickness_m', 0.1))
        else:
            # Calculate volume from area and thickness
            thickness = custom_thickness or profile.get('thickness_m', 0.1)
            min_thickness = profile.get('minimum_thickness_m', 0.05)
            
            # Enforce minimum thickness
            actual_thickness = max(thickness, min_thickness)
            
            volume_m3 = area_m2 * actual_thickness
            effective_volume = volume_m3 * profile['waste_factor']
            area_for_installation = area_m2
        
        return {
            'material_name': profile['name'],
            'base_area_m2': area_for_installation,
            'volume_m3': volume_m3,
            'effective_volume_m3': effective_volume,
            'waste_factor': profile['waste_factor'],
            'primary_quantity': effective_volume,  # All materials now calculated by volume
            'unit': profile['unit'],
            'thickness_used_m': custom_thickness or profile.get('thickness_m', 0)
        }
    
    def calculate_material_cost(self, area_m2: float, material_key: str,
                              custom_thickness: float = None, is_volume: bool = False) -> Dict:
        """
        Calculate total material cost using volume-based pricing.
        
        Args:
            area_m2: Area in square meters OR volume in m³ if is_volume=True
            material_key: Material identifier
            custom_thickness: Override default thickness in meters
            is_volume: If True, area_m2 is treated as volume
            
        Returns:
            dict: Complete cost breakdown
        """
        profile = self.get_material_profile(material_key)
        if not profile:
            return {"error": f"Material '{material_key}' not found"}
        
        # Get quantity calculation
        quantity_result = self.calculate_material_quantity(area_m2, material_key, custom_thickness, is_volume)
        
        if 'error' in quantity_result:
            return quantity_result
        
        # Calculate primary material cost using volume
        primary_cost = quantity_result['effective_volume_m3'] * profile['cost_per_unit']
        
        # Installation cost based on surface area
        installation_area = quantity_result['base_area_m2']
        installation_cost = installation_area * profile.get('installation_cost_per_m2', 0)
        
        # Calculate additional materials cost
        additional_costs = {}
        total_additional_cost = 0.0
        
        for material_name, material_data in profile.get('additional_materials', {}).items():
            if material_data['unit'] == 'm²':
                quantity = installation_area * material_data['amount_per_m2']
            elif material_data['unit'] == 'm³':
                quantity = installation_area * material_data['amount_per_m2']
            elif material_data['unit'] == 'kg':
                quantity = installation_area * material_data['amount_per_m2']
            else:
                quantity = material_data['amount_per_m2']
            
            cost = quantity * material_data['cost_per_unit']
            additional_costs[material_name] = {
                'quantity': quantity,
                'unit': material_data['unit'],
                'cost_per_unit': material_data['cost_per_unit'],
                'total_cost': cost
            }
            total_additional_cost += cost
        
        # Calculate totals
        subtotal = primary_cost + total_additional_cost
        total_cost = subtotal + installation_cost
        
        return {
            'material_name': profile['name'],
            'area_m2': installation_area,
            'volume_m3': quantity_result['volume_m3'],
            'effective_volume_m3': quantity_result['effective_volume_m3'],
            'primary_material': {
                'quantity': quantity_result['effective_volume_m3'],
                'unit': profile['unit'],
                'cost_per_unit': profile['cost_per_unit'],
                'total_cost': primary_cost
            },
            'additional_materials': additional_costs,
            'installation_cost': installation_cost,
            'subtotal_materials': subtotal,
            'total_cost': total_cost,
            'cost_per_m2': total_cost / installation_area if installation_area > 0 else 0,
            'cost_per_m3': total_cost / quantity_result['volume_m3'] if quantity_result['volume_m3'] > 0 else 0
        }
    
    def calculate_project_totals(self, areas_and_materials: List[Tuple[float, str]]) -> Dict:
        """
        Calculate totals for multiple areas with different materials.
        
        Args:
            areas_and_materials: List of (area_m2, material_key) tuples
            
        Returns:
            dict: Project totals and breakdown
        """
        project_results = {
            'total_area_m2': 0.0,
            'total_cost': 0.0,
            'area_breakdown': [],
            'material_summary': {},
            'area_count': len(areas_and_materials)
        }
        
        for i, (area_m2, material_key) in enumerate(areas_and_materials):
            # Calculate for this area
            cost_result = self.calculate_material_cost(area_m2, material_key)
            
            if 'error' not in cost_result:
                # Add to project totals
                project_results['total_area_m2'] += area_m2
                project_results['total_cost'] += cost_result['total_cost']
                
                # Store area breakdown
                project_results['area_breakdown'].append({
                    'area_index': i + 1,
                    'area_m2': area_m2,
                    'material': cost_result['material_name'],
                    'cost': cost_result['total_cost'],
                    'cost_per_m2': cost_result['cost_per_m2']
                })
                
                # Update material summary
                material_name = cost_result['material_name']
                if material_name not in project_results['material_summary']:
                    project_results['material_summary'][material_name] = {
                        'total_area_m2': 0.0,
                        'total_cost': 0.0,
                        'usage_count': 0
                    }
                
                project_results['material_summary'][material_name]['total_area_m2'] += area_m2
                project_results['material_summary'][material_name]['total_cost'] += cost_result['total_cost']
                project_results['material_summary'][material_name]['usage_count'] += 1
        
        return project_results
    
    def get_material_recommendations(self, area_m2: float, usage_type: str = "general") -> List[Dict]:
        """Get material recommendations based on area size and usage type."""
        recommendations = []
        
        if usage_type == "driveway":
            if area_m2 < 50:
                recommendations = [
                    {
                        'material_key': 'concrete_tiles',
                        'rating': 4,
                        'reason': 'Attractive and durable for small driveways',
                        'pros': ['Attractive appearance', 'Easy to replace individual tiles'],
                        'cons': ['Higher initial cost', 'More joints to maintain']
                    },
                    {
                        'material_key': 'asphalt',
                        'rating': 5,
                        'reason': 'Most cost-effective option',
                        'pros': ['Low cost', 'Quick installation', 'Smooth surface'],
                        'cons': ['Less attractive', 'Requires regular sealing']
                    }
                ]
            else:
                recommendations = [
                    {
                        'material_key': 'asphalt',
                        'rating': 5,
                        'reason': 'Most economical for large areas',
                        'pros': ['Very cost effective', 'Fast installation', 'Good durability'],
                        'cons': ['Appearance', 'Temperature sensitivity']
                    },
                    {
                        'material_key': 'concrete_slab',
                        'rating': 4,
                        'reason': 'Long-term durability',
                        'pros': ['Very durable', 'Low maintenance', 'Can be decorative'],
                        'cons': ['Higher initial cost', 'Can crack over time']
                    }
                ]
        
        elif usage_type == "sidewalk":
            recommendations = [
                {
                    'material_key': 'concrete_slab',
                    'rating': 5,
                    'reason': 'Standard for pedestrian areas',
                    'pros': ['ADA compliant', 'Long-lasting', 'Low maintenance'],
                    'cons': ['Initial cost']
                },
                {
                    'material_key': 'brick_pavers',
                    'rating': 4,
                    'reason': 'Attractive option for pedestrian areas',
                    'pros': ['Attractive', 'Permeable options available', 'Easy repair'],
                    'cons': ['Higher cost', 'More maintenance']
                }
            ]
        
        elif usage_type == "patio":
            recommendations = [
                {
                    'material_key': 'brick_pavers',
                    'rating': 5,
                    'reason': 'Ideal for outdoor living spaces',
                    'pros': ['Beautiful appearance', 'Many design options', 'Good drainage'],
                    'cons': ['Higher cost', 'Weed growth in joints']
                },
                {
                    'material_key': 'concrete_tiles',
                    'rating': 4,
                    'reason': 'Modern and clean appearance',
                    'pros': ['Contemporary look', 'Consistent appearance', 'Good durability'],
                    'cons': ['Can be slippery when wet', 'Limited design options']
                }
            ]
        
        else:  # general
            recommendations = [
                {
                    'material_key': 'concrete_slab',
                    'rating': 4,
                    'reason': 'Versatile and durable',
                    'pros': ['Good all-around choice', 'Durable', 'Cost-effective'],
                    'cons': ['Basic appearance']
                },
                {
                    'material_key': 'asphalt',
                    'rating': 3,
                    'reason': 'Budget-friendly option',
                    'pros': ['Low cost', 'Quick installation'],
                    'cons': ['Limited applications', 'Appearance']
                }
            ]
        
        return sorted(recommendations, key=lambda x: x['rating'], reverse=True)
    
    def export_calculation_summary(self, project_results: Dict, filename: str = None) -> str:
        """Export calculation summary to JSON format."""
        summary = {
            'project_summary': project_results,
            'calculation_timestamp': 'N/A',
            'software': 'Image Resource Planner',
            'version': '3.0 - Cubic Meter Materials'
        }
        
        json_output = json.dumps(summary, indent=2, default=str)
        
        if filename:
            with open(filename, 'w') as f:
                f.write(json_output)
        
        return json_output