import {Routes} from '@angular/router';

export const routes: Routes = [
  {
    path: "",
    redirectTo: "/home",
    pathMatch: "full"
  },
  {
    path: "home",
    loadChildren: () => import("./home/home.routes").then((m) => m.HOME_ROUTES)
  },
  {
    path: "material",
    loadChildren: () => import("./material-planning/material-planning.routes").then((m) => m.MATERIAL_ROUTES)
  }
];

