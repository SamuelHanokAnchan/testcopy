import { Routes } from '@angular/router';

export const MATERIAL_ROUTES: Routes = [
  {
    path: "",
    loadComponent: () => import("./material-planning-home/material-planning-home").then((m) => m.MaterialPlanningHome)
  },
  {
    path: "calculate",
    loadComponent: () => import("./material-planning-calculate/material-planning-calculate").then((m) => m.MaterialPlanningCalculate)
  },
];

