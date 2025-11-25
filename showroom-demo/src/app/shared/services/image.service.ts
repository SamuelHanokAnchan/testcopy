import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable, of} from 'rxjs';
import {PictureListType} from '../picture-list/picture-list';

// Simple image service that returns a list of image URLs from assets
@Injectable({providedIn: 'root'})
export class ImageService {
  constructor(private readonly http: HttpClient) {
  }

  // Fetch a list of random images from Picsum; return sized URLs for consistency
  getImages(type: PictureListType, count: number = 6): Observable<string[]> {
    if (type === PictureListType.MATERIAL_PLANNING) {
      return of(["assets/output_tile_1.jpeg", "assets/output_tile_2.jpeg", "assets/output_tile_3.jpeg", "assets/output_tile_4.jpeg", "assets/output_tile_5.jpeg", "assets/output_tile_6.jpeg"]);
    } else {
      return of([
        "assets/damage/schimmel.jpeg",
        "assets/damage/schimmelschaden-unter-leiste.jpeg",
        "assets/damage/streichen-spachteln.jpeg",
        "assets/damage/wasserschaden-mit-putz.jpeg",
        "assets/damage/wasserschaden-pakett.jpeg",
        "assets/damage/wasser.jpeg"
      ]);
    }
  }
}
