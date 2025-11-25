import {Layer} from './layer';
import {PolygonModel} from './polygon-model';

export interface Area {
  id: number;
  name: string;
  size: number;
  polygon: PolygonModel;
  layers: Layer[];
  color: string;
}
