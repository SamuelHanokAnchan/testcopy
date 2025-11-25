export interface AreaDataDto {
  calculated_area: {
    pixel_area: number;
    apparent_area_m2: number;
    corrected_area_m2: number;
    correction_factor: number;
    correction_applied: number;
    area_difference_m2: number;
    area_difference_percent: number;
  };
  polygon: [number, number][];
}
