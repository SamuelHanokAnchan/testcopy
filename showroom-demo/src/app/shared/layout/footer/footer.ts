import {Component} from '@angular/core';

@Component({
  selector: 'app-footer',
  standalone: true,
  templateUrl: './footer.html',
  styleUrl: './footer.css'
})
export class FooterComponent {
  // current year for copyright
  get year(): number { return new Date().getFullYear(); }
}
