import {Injectable} from '@angular/core';
import {MaterialDto, MaterialUnit} from '../model/material.dto';

@Injectable({providedIn: 'root'})
export class MaterialCalculationService {

// 1 Liter = 0.001 m^3
  getMaterials(): MaterialDto[] {
    return [
      {name: "Feiner Sand", unit: MaterialUnit.EURO_PER_CUBIC_METER, price: 30},
      {name: "Grober Sand", unit: MaterialUnit.EURO_PER_CUBIC_METER, price: 30},
      {name: "Kies", unit: MaterialUnit.EURO_PER_KILO, price: 0.5},
      {name: "Erde", unit: MaterialUnit.EURO_PER_LITER, price: 0.1},
      {name: "Randstein", unit: MaterialUnit.EURO_PER_METER, price: 4},
      {name: "Zement", unit: MaterialUnit.EURO_PER_KILO, price: 10},
      {name: "Pflasterstein", unit: MaterialUnit.EURO_PER_SQUARE_METER, price: 20},
      {name: "Asphalt", unit: MaterialUnit.EURO_PER_SQUARE_METER, price: 30},
      {name: "Dachziegel (schräg)", unit: MaterialUnit.EURO_PER_SQUARE_METER, price: 20},
      {name: "Schindeln (Bitumen)", unit: MaterialUnit.EURO_PER_SQUARE_METER, price: 10},
    ]
  }
}
