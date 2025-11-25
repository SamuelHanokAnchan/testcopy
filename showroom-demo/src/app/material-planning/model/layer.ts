import {MaterialDto} from './material.dto';

export interface Layer {
  id: number;
  name: string;
  material: MaterialDto | null;
  depth: number;
}
