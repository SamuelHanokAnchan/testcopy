import {Component} from '@angular/core';
import {PictureList, PictureListType} from "../../shared/picture-list/picture-list";
import {Router} from '@angular/router';

@Component({
  selector: 'app-material-planning-home',
  standalone: true,
  imports: [PictureList],
  templateUrl: './material-planning-home.html',
  styleUrl: './material-planning-home.css'
})
export class MaterialPlanningHome {
  protected readonly PictureList = PictureList;
  protected readonly PictureListType = PictureListType;
  private selectedImage: string = "";

  constructor(private router: Router) {
  }

  onImageSelected($event: string) {
    this.selectedImage = $event;
    this.router.navigate(['/material/calculate'], {queryParams: {image: this.selectedImage}});
  }
}
