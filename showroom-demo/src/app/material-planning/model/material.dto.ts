export interface MaterialDto {
  name: string;
  price: number;
  unit: MaterialUnit;
}

export enum MaterialUnit {
  EURO_PER_SQUARE_METER = "Euro/m^2",
  EURO_PER_CUBIC_METER = "Euro/m^3",
  EURO_PER_KILO = "Euro/kg",
  EURO_PER_TON = "Euro/t",
  EURO_PER_METER = "Euro/lfm",
  EURO_PER_LITER = "Euro/l"
}
