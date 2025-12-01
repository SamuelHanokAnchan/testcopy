import {Component, Input, OnInit} from '@angular/core';
import {Router} from '@angular/router'
import {ImageEditorModule} from '@syncfusion/ej2-angular-image-editor';
import {PolygonModel} from '../model/polygon-model';
import {AreaCalculationService} from '../services/area-calculation.service';
import {ImageMetadataDto} from '../model/image-metadata.dto';
import {Area} from '../model/area';
import {AreaList} from '../components/area-list/area-list';
import {FormsModule} from '@angular/forms';
import {MaterialPdfService} from '../../shared/services/pdf/material-pdf.service';
import {MessageModule} from '@syncfusion/ej2-angular-notifications';

@Component({
  selector: 'app-material-planning-calculate',
  standalone: true,
  imports: [
    ImageEditorModule,
    AreaList,
    FormsModule,
    MessageModule
  ],
  templateUrl: './material-planning-calculate.html',
  styleUrl: './material-planning-calculate.css'
})
export class MaterialPlanningCalculate implements OnInit {
  // @ts-ignore
  @Input() image: string;

  areaSelectionMode: AreaMode = AreaMode.UNSELECTED;
  // @ts-ignore
  canvas: HTMLCanvasElement;
  // @ts-ignore
  context: CanvasRenderingContext2D;
  polygonPoints: string = "No points yet";
  clickedPoints: [number, number][] = [];
  mouse: { x: number, y: number; };
  last_mouse: { x: number, y: number; };
  areas: Area[];
  selectedArea: number;
  colors: string[];
  protected readonly AreaMode = AreaMode;

  private tooltip: HTMLDivElement | null = null;

  private currentHoveredAreaId: number | null = null;

  private polygons: PolygonModel[];
  // @ts-ignore
  private rawImg: HTMLImageElement;
  // @ts-ignore
  private buttonContinuous: HTMLButtonElement;
  // @ts-ignore
  private buttonSmart: HTMLButtonElement;
  // @ts-ignore
  private buttonManual: HTMLButtonElement;

  constructor(private router: Router,
              private readonly areaCalculationService: AreaCalculationService,
              private readonly materialPdf: MaterialPdfService) {
    this.mouse = {x: 0, y: 0};
    this.last_mouse = {x: 0, y: 0};
    this.polygons = [];
    this.areas = [];
    this.selectedArea = -1;
    this.colors = ["#00d5ff", "#ff8400", "#00ff26", "#ffe100", "#a2ff00", "#00ffbb", "#fc0303", "#00fff2", "#809fff", "#a600ff", "#ee00ff"]
  }

  ngOnInit(): void {
    this.canvas = <HTMLCanvasElement>document.querySelector("canvas")
    if (!this.canvas) {
      console.error("Error: Canvas not found!")
    }
    this.context = <CanvasRenderingContext2D>this.canvas.getContext("2d");
    if (!this.context) {
      console.error("Error: Context not found!")
    }
    let pictureId = this.calculatePictureId();
    const metadata = this.areaCalculationService.getMetadata(pictureId);
    metadata.subscribe((data: ImageMetadataDto) => {
      this.rawImg = new Image(data.width, data.height);
      this.rawImg.src = this.image
      this.rawImg.onload = () => {
        this.drawImage();
      }
      this.registerContinuousModeEventListeners();
    })
    // @ts-ignore
    //this.buttonContinuous = document.getElementById("button_continuous");
    // @ts-ignore
    this.buttonSmart = document.getElementById("button_smart");
    // @ts-ignore
    this.buttonManual = document.getElementById("button_manual");
    this.setSelectionMode(AreaMode.MANUAL);
    // Add hover tooltip listener
    this.canvas.addEventListener('mousemove', (event: MouseEvent) => {
      this.onCanvasHover(event);
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.hideTooltip();
    });
  }

  drawLine(this: HTMLCanvasElement, ev: MouseEvent): any {
    const context = <CanvasRenderingContext2D>this.getContext("2d");
    context.lineTo(ev.offsetX, ev.offsetY);
    context.stroke();
  }

  drawImage() {
    this.resize(this.rawImg.width, this.rawImg.height)
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height)
    this.context?.drawImage(this.rawImg, 0, 0, this.rawImg.width, this.rawImg.height);
  }

  drawScene() {
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.drawImage();
    for (let i = 0; i < this.areas.length; i++) {
      let area = this.areas[i];
      this.drawPolygon(area.polygon.points, i);
      // TEXT LABEL REMOVED - will show on hover instead
    }
  }

  resize(width: number, height: number) {
    if (this.canvas) {
      const biggest = 1024;
      let axis
      // so that the biggest axis is always {biggest} px
      let ratio = height > width ? height / biggest : width / biggest
      axis = [height / ratio, width / ratio]
      this.canvas.height = axis[0]
      this.canvas.width = axis[1]
    }
  }

  onCanvasClick($event: MouseEvent) {
    switch (this.areaSelectionMode) {
      case AreaMode.MANUAL:
        this.addNewPoint($event.offsetX, $event.offsetY);
        break;
      case AreaMode.UNSELECTED:
        for (let area of this.areas) {
          if (area.polygon.pointIsInArea($event.offsetX, $event.offsetY)) {
            this.selectedArea = this.areas.indexOf(area);
          }
        }
        this.drawScene();
        break;
      case AreaMode.SMART:
        const areaDataDtoObservable = this.areaCalculationService.calculateAreaSmart(this.calculatePictureId(), [$event.offsetX, $event.offsetY]);
        areaDataDtoObservable.subscribe(areaDataDto => {
          this.addArea(areaDataDto.calculated_area.apparent_area_m2, new PolygonModel(areaDataDto.polygon));
          this.setSelectionMode(AreaMode.UNSELECTED);
          this.drawScene();
        });
        // todo: autodetect are based on click
        break;
      case AreaMode.CONTINUOUS:
        // do nothing, handled via listeners
        break;
    }
  }

  drawPolygon(polygon: [number, number][], areaNumber: number) {
    const highlight: boolean = areaNumber === this.selectedArea;
    this.context.beginPath();
    const firstPoint = polygon[0];
    this.context.moveTo(firstPoint[0], firstPoint[1]);
    for (let i = 1; i < polygon.length; i++) {
      this.context.lineTo(polygon[i][0], polygon[i][1]);
    }
    if (highlight) {
      this.context.globalAlpha = 0.8;
    } else {
      this.context.globalAlpha = 0.5;
    }
    this.context.fillStyle = this.areas[areaNumber].color;
    this.context.fill();
    for (let i = 0; i < polygon.length; i++) {
      this.context.beginPath();
      this.context.fillStyle = "black";
      this.context.globalAlpha = 1;
      this.context.arc(polygon[i][0], polygon[i][1], 4, 0, 2 * Math.PI);
      this.context.fill();
    }
  }

  addNewPoint(x: number, y: number) {
    let finishArea: boolean = false;
    this.context.beginPath()
    if (this.clickedPoints.length > 0) {
      const lastPoint = this.clickedPoints[this.clickedPoints.length - 1];
      let distance = PolygonModel.distance([x, y], [this.clickedPoints[0][0], this.clickedPoints[0][1]]);
      let distanceThreshold = 10;
      if (this.clickedPoints.length > 2 && distance < distanceThreshold) {
        finishArea = true;
      }
      this.context.moveTo(lastPoint[0], lastPoint[1]);
      this.context.lineTo(x, y);
      this.context.stroke();
      this.context.beginPath();
    }
    this.context.arc(x, y, 4, 0, 2 * Math.PI);
    this.context.fill()

    this.clickedPoints.push([x, y]);
    if (this.polygonPoints === "No points yet") {
      this.polygonPoints = "";
    }
    this.polygonPoints = this.polygonPoints + `[${x},${y}]`;

    if (finishArea) {
      this.finishArea();
    }
  }

  deletePointsClick() {
    this.polygonPoints = "No points yet";
    this.clickedPoints = [];
    this.drawScene();
  }

  finishArea() {
    const polygon = new PolygonModel(this.clickedPoints);
    this.polygons.push(polygon);
    let areaDataModelObservable = this.areaCalculationService.calculateAreaManual(this.calculatePictureId(), this.clickedPoints);
    areaDataModelObservable.subscribe(areaDataDto => {
      this.addArea(areaDataDto.calculated_area.apparent_area_m2, polygon);
      this.clickedPoints = [];
      this.polygonPoints = "No points yet";
      this.drawScene();
    })
  }

  setSelectionMode(selectionMode: AreaMode) {
    switch (selectionMode) {
      case AreaMode.CONTINUOUS:
        // this.buttonContinuous?.style && (this.buttonContinuous.style.border = "solid");
        this.buttonManual?.style && (this.buttonManual.style.border = "1px solid");
        this.buttonSmart?.style && (this.buttonSmart.style.border = "1px solid");
        break;
      case AreaMode.MANUAL:
        // this.buttonContinuous?.style && (this.buttonContinuous.style.border = "1px solid");
        this.buttonManual?.style && (this.buttonManual.style.border = "solid");
        this.buttonSmart?.style && (this.buttonSmart.style.border = "1px solid");
        break;
      case AreaMode.SMART:
        // this.buttonContinuous?.style && (this.buttonContinuous.style.border = "1px solid");
        this.buttonManual?.style && (this.buttonManual.style.border = "1px solid");
        this.buttonSmart?.style && (this.buttonSmart.style.border = "solid");
        break;
      case AreaMode.UNSELECTED:
        // this.buttonContinuous?.style && (this.buttonContinuous.style.border = "1px solid");
        this.buttonManual?.style && (this.buttonManual.style.border = "1px solid");
        this.buttonSmart?.style && (this.buttonSmart.style.border = "1px solid");
        break;
    }
    if (this.areaSelectionMode === selectionMode) {
      // this.buttonContinuous?.style && (this.buttonContinuous.style.border = "1px solid");
      this.buttonManual?.style && (this.buttonManual.style.border = "1px solid");
      this.buttonSmart?.style && (this.buttonSmart.style.border = "1px solid");
      this.areaSelectionMode = AreaMode.UNSELECTED;
    } else {
      this.areaSelectionMode = selectionMode;
    }
  }

  onAreasUpdated() {
    this.drawScene();
  }

  onSelectedAreaChange(newSelection: number) {
    this.selectedArea = newSelection;
    this.drawScene();
  }

  async exportPdf() {
    try {
      if (!this.image) {
        console.error('Kein Bild gesetzt – PDF Export abgebrochen');
        return;
      }
      // Canvas aktualisieren damit Auswahl sichtbar ist
      this.drawScene();
      const dataUrl = this.canvas?.toDataURL('image/png') || this.image;
      const blob = await this.materialPdf.buildMaterialReport({imageUrl: dataUrl, areas: this.areas});
      if (blob.size < 10) {
        console.warn('Erzeugtes PDF ist leer.');
        return;
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'material-kalkulation.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch (e) {
      console.error('Fehler beim PDF Export', e);
    }
  }

  private calculatePictureId() {
    let pictureId = this.image.split("/")[1]
    // todo: Use proper IDs for images!
    return pictureId.replace("png", "tif").replace("jpg", "tif").replace("jpeg", "tif");
  }

  private addArea(size: number, polygon: PolygonModel) {
    const lastArea = this.areas[this.areas.length - 1];
    let areaId = 0;
    if (lastArea) {
      areaId = lastArea.id + 1;
    }
    this.selectedArea = this.areas.push({
      id: areaId,
      name: `neues Gebiet ${areaId}`,
      size: size,
      polygon: polygon,
      layers: [],
      color: this.colors[areaId]
    }) - 1;
  }

  private registerContinuousModeEventListeners() {
    this.canvas.addEventListener('mousedown', ($event: MouseEvent) => {
      if (this.areaSelectionMode === AreaMode.CONTINUOUS) {
        this.mouse.x = $event.offsetX;
        this.mouse.y = $event.offsetY;
        this.clickedPoints.push([this.mouse.x, this.mouse.y]);
        this.context.beginPath();
        this.context.moveTo(this.mouse.x, this.mouse.y);
        this.canvas.addEventListener('mousemove', this.drawLine, false);
      }
    }, false)
    this.canvas.addEventListener('mouseup', ($event: MouseEvent) => {
      if (this.areaSelectionMode === AreaMode.CONTINUOUS) {
        this.last_mouse.x = this.mouse.x;
        this.last_mouse.y = this.mouse.y;

        this.mouse.x = $event.offsetX;
        this.mouse.y = $event.offsetY;

        this.clickedPoints.push([this.mouse.x, this.mouse.y]);
        this.canvas.removeEventListener('mousemove', this.drawLine, false);
      }
    }, false)
  }

  // added a on hover tooltip for the area map - samuel
  private onCanvasHover(event: MouseEvent) {
    const rect = this.canvas.getBoundingClientRect();
    const canvasX = event.clientX - rect.left;
    const canvasY = event.clientY - rect.top;

    let hoveredArea: Area | null = null;
    let hoveredAreaIndex: number = -1;
    
    for (let i = 0; i < this.areas.length; i++) {
      if (this.areas[i].polygon.pointIsInArea(canvasX, canvasY)) {
        hoveredArea = this.areas[i];
        hoveredAreaIndex = i;
        break;
      }
    }

    if (hoveredArea) {
      this.currentHoveredAreaId = hoveredAreaIndex;
      this.showTooltip(hoveredArea, event.clientX, event.clientY);
    } else {
      this.hideTooltip();
    }
  }

  private showTooltip(area: Area, clientX: number, clientY: number) {
    if (!this.tooltip) {
      this.tooltip = document.createElement('div');
      document.body.appendChild(this.tooltip);
    }

    this.tooltip.innerHTML = `
      <div style="background: linear-gradient(135deg, #2564ebde 0%, #1d4fd8b9 100%); padding: 12px 16px; border-radius: 10px 10px 0 0; color: white;">
        <div style="font-weight: 700; font-size: 14px; letter-spacing: 0.2px;">${area.name}</div>
      </div>
      <div style="background: #ffffffcf; padding: 12px 16px; border-radius: 0 0 10px 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 16px;">
          <span style="color: #64748b; font-weight: 500; font-size: 12px;">Größe:</span>
          <span style="color: white; font-weight: 700; font-size: 13px; background-color: #2564ebb2; padding: 4px 10px; border-radius: 5px; white-space: nowrap;">${area.size.toFixed(2)} m²</span>
        </div>
      </div>
    `;
    
    this.tooltip.style.position = 'fixed';
    this.tooltip.style.left = (clientX + 15) + 'px';
    this.tooltip.style.top = (clientY - 10) + 'px';
    this.tooltip.style.display = 'block';
    this.tooltip.style.visibility = 'visible';
    this.tooltip.style.opacity = '1';
    this.tooltip.style.zIndex = '99999';
    this.tooltip.style.minWidth = '220px';
    this.tooltip.style.whiteSpace = 'normal';
    this.tooltip.style.overflow = 'hidden';
    this.tooltip.style.borderRadius = '10px';
    this.tooltip.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.2)';
    this.tooltip.style.border = 'none';
    this.tooltip.style.fontFamily = 'system-ui, -apple-system, sans-serif';
  }

  private hideTooltip() {
    if (this.tooltip) {
      this.tooltip.style.display = 'none';
      this.tooltip.style.visibility = 'hidden';
    }
  }
}

export enum AreaMode {
  SMART,
  MANUAL,
  CONTINUOUS,
  UNSELECTED
}
