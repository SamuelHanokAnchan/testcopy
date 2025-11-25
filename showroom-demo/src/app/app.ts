import {Component} from '@angular/core';
import {RouterOutlet} from '@angular/router';
import {GridModule} from '@syncfusion/ej2-angular-grids';
import {ImageEditorModule} from '@syncfusion/ej2-angular-image-editor';
import {HeaderComponent} from './shared/layout/header';
import {FooterComponent} from './shared/layout/footer';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, GridModule, ImageEditorModule, HeaderComponent, FooterComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
}
