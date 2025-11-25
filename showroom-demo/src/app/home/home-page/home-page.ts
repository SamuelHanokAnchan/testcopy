import { Component } from '@angular/core';
import {NgOptimizedImage} from '@angular/common';
import {Router} from '@angular/router';

@Component({
  selector: 'app-home-page',
  imports: [
    NgOptimizedImage
  ],
  templateUrl: './home-page.html',
  styleUrl: './home-page.css'
})
export class HomePage {

  constructor(private router: Router) {
  }

  onMaterialPlanningClick() {
    this.router.navigate(["/material"]);
  }

  onDamageProtokollClick() {
    this.router.navigate(["/damage"]);
  }
}
