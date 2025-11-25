import {Component, EventEmitter, Input, OnInit, Output, signal} from '@angular/core';
import {CommonModule, NgOptimizedImage} from '@angular/common';
import {ImageService} from '../services/image.service';
import {ListViewModule} from '@syncfusion/ej2-angular-lists';

@Component({
  selector: 'app-picture-list',
  standalone: true,
  imports: [CommonModule, NgOptimizedImage, ListViewModule],
  templateUrl: './picture-list.html',
  styleUrl: './picture-list.css'
})
export class PictureList implements OnInit {
  @Input() type: PictureListType = PictureListType.MATERIAL_PLANNING;
  @Input() count = 12;
  @Output() imageSelected = new EventEmitter<string>();
  protected readonly images = signal<string[]>([]);

  constructor(private readonly imageService: ImageService) {
  }

  ngOnInit(): void {
    this.imageService.getImages(this.type, this.count).subscribe((imgs) => this.images.set(imgs));
  }

  onImageClick(url: string) {
    this.imageSelected.emit(url);
  }
}

export enum PictureListType {
  MATERIAL_PLANNING,
  APARTMENT_DAMAGES
}
