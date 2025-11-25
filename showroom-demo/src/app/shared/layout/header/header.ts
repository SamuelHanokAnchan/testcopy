import {Component} from '@angular/core';
import {Router} from '@angular/router';

@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.html',
  styleUrl: './header.css'
})
export class HeaderComponent {
  constructor(private router: Router) {}

  goToRating() {
    this.router.navigate(['/rating']);
  }

  goHome() {
    // Nur navigieren wenn nicht bereits auf der Home-Route
    if (this.router.url !== '/home') {
      this.router.navigate(['/home']);
    }
  }
}
