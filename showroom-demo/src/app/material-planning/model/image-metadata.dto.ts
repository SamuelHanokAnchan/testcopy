export interface ImageMetadataDto {
  width: number;
  height: number;
  count: number;
  dtype: string;
  crs: string;
  bounds: {lowerLeftX: number,lowerLeftY: number, upperRightX: number, upperRightY: number};
}
