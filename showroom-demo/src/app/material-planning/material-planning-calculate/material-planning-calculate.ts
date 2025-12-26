import {Component, Input, OnInit, AfterViewInit, ViewChild, ElementRef} from '@angular/core';
import {Router, ActivatedRoute} from '@angular/router'
import {ImageEditorModule} from '@syncfusion/ej2-angular-image-editor';
import {PolygonModel} from '../model/polygon-model';
import {AreaCalculationService} from '../services/area-calculation.service';
import {ImageMetadataDto} from '../model/image-metadata.dto';
import {Area} from '../model/area';
import {AreaList} from '../components/area-list/area-list';
import {FormsModule} from '@angular/forms';
import {MaterialPdfService} from '../../shared/services/pdf/material-pdf.service';
import {MessageModule} from '@syncfusion/ej2-angular-notifications';

interface StateSnapshot {
  clickedPoints: [number, number][];
  areas: Area[];
  selectedArea: number;
}

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
export class MaterialPlanningCalculate implements OnInit, AfterViewInit {
  @Input() image: string = '';
  @ViewChild('canvasElement') canvasElement: ElementRef<HTMLCanvasElement> = undefined!;

  areaSelectionMode: AreaMode = AreaMode.UNSELECTED;
  canvas: HTMLCanvasElement = undefined!;
  context: CanvasRenderingContext2D = undefined!;
  polygonPoints: string = "Noch keine Punkte";
  clickedPoints: [number, number][] = [];
  mouse: { x: number, y: number; };
  last_mouse: { x: number, y: number; };
  areas: Area[] = [];
  selectedArea: number = -1;
  colors: string[];
  protected readonly AreaMode = AreaMode;
  stateHistory: StateSnapshot[] = [];
  isEditMode: boolean = false;
  selectedPointIndex: number = -1;

  private tooltip: HTMLDivElement | null = null;
  private currentHoveredAreaId: number | null = null;
  private polygons: PolygonModel[] = [];
  private rawImg: HTMLImageElement = undefined!;
  private buttonSmart: HTMLButtonElement = undefined!;
  private buttonManual: HTMLButtonElement = undefined!;
  private canvasScaleX: number = 1;
  private canvasScaleY: number = 1;

  constructor(
    private router: Router,
    private activatedRoute: ActivatedRoute,
    private readonly areaCalculationService: AreaCalculationService,
    private readonly materialPdf: MaterialPdfService
  ) {
    this.mouse = {x: 0, y: 0};
    this.last_mouse = {x: 0, y: 0};
    this.polygons = [];
    this.areas = [];
    this.selectedArea = -1;
    this.colors = ["#00d5ff", "#ff8400", "#00ff26", "#ffe100", "#a2ff00", "#00ffbb", "#fc0303", "#00fff2", "#809fff", "#a600ff", "#ee00ff"]
  }

  ngOnInit(): void {
    this.activatedRoute.queryParams.subscribe(params => {
      this.image = params['image'] || '';
    });
  }

  ngAfterViewInit(): void {
    if (!this.canvasElement) {
      console.error("Fehler: Canvas-Element nicht gefunden!");
      return;
    }

    this.canvas = this.canvasElement.nativeElement;

    const ctx = this.canvas.getContext("2d");
    if (!ctx) {
      console.error("Fehler: Kontext nicht gefunden!")
      return;
    }
    this.context = ctx;

    const pictureId = this.calculatePictureId();
    const metadata = this.areaCalculationService.getMetadata(pictureId);
    
    metadata.subscribe((data: ImageMetadataDto) => {
      this.rawImg = new Image(data.width, data.height);
      this.rawImg.src = this.image;
      this.rawImg.onload = () => {
        this.drawImage();
        this.updateCanvasScale();
      }
      this.registerContinuousModeEventListeners();
    });

    this.buttonSmart = document.getElementById("button_smart") as HTMLButtonElement | null || undefined!;
    this.buttonManual = document.getElementById("button_manual") as HTMLButtonElement | null || undefined!;
    this.setSelectionMode(AreaMode.MANUAL);

    this.canvas.addEventListener('mousemove', (event: MouseEvent) => {
      this.onCanvasHover(event);
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.hideTooltip();
    });

    window.addEventListener('resize', () => {
      this.updateCanvasScale();
    });
  }

  private updateCanvasScale(): void {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    this.canvasScaleX = this.canvas.width / rect.width;
    this.canvasScaleY = this.canvas.height / rect.height;
  }

  private getCanvasCoordinates(event: MouseEvent): [number, number] {
    const rect = this.canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) * this.canvasScaleX;
    const y = (event.clientY - rect.top) * this.canvasScaleY;
    return [x, y];
  }

  drawImage(): void {
    this.resize(this.rawImg.width, this.rawImg.height);
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.context?.drawImage(this.rawImg, 0, 0, this.rawImg.width, this.rawImg.height);
  }

  drawScene(): void {
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.drawImage();
    
    for (let i = 0; i < this.areas.length; i++) {
      let area = this.areas[i];
      this.drawPolygon(area.polygon.points, i);
    }

    for (let i = 0; i < this.clickedPoints.length; i++) {
      this.context.beginPath();
      this.context.fillStyle = "#3b82f6";
      this.context.arc(this.clickedPoints[i][0], this.clickedPoints[i][1], 5, 0, 2 * Math.PI);
      this.context.fill();

      if (this.isEditMode) {
        this.context.strokeStyle = "#ffcc00";
        this.context.lineWidth = 2;
        this.context.stroke();
      }

      if (i > 0) {
        this.context.strokeStyle = "#3b82f6";
        this.context.lineWidth = 2;
        this.context.beginPath();
        this.context.moveTo(this.clickedPoints[i - 1][0], this.clickedPoints[i - 1][1]);
        this.context.lineTo(this.clickedPoints[i][0], this.clickedPoints[i][1]);
        this.context.stroke();
      }
    }
  }

  resize(width: number, height: number): void {
    if (!this.canvas) return;
    const biggest = 1024;
    let axis: [number, number];
    let ratio = height > width ?
      height / biggest : width / biggest;
    axis = [height / ratio, width / ratio];
    this.canvas.height = axis[0];
    this.canvas.width = axis[1];
    this.updateCanvasScale();
  }

  onCanvasClick(event: MouseEvent): void {
    const [x, y] = this.getCanvasCoordinates(event);

    if (this.isEditMode) {
      this.selectPointToEdit(x, y);
      return;
    }

    switch (this.areaSelectionMode) {
      case AreaMode.MANUAL:
        this.addNewPoint(x, y);
        break;
      case AreaMode.UNSELECTED:
        for (let area of this.areas) {
          if (area.polygon.pointIsInArea(x, y)) {
            this.selectedArea = this.areas.indexOf(area);
          }
        }
        this.drawScene();
        break;
      case AreaMode.SMART:
        const areaDataDtoObservable = this.areaCalculationService.calculateAreaSmart(
          this.calculatePictureId(), 
          [Math.round(x), Math.round(y)]
        );
        areaDataDtoObservable.subscribe(areaDataDto => {
          this.saveState();
          const smartPolygon = new PolygonModel(areaDataDto.polygon);
          this.addArea(areaDataDto.calculated_area.apparent_area_m2, smartPolygon);
          this.drawScene();
        });
        break;
      case AreaMode.CONTINUOUS:
        break;
    }
  }

  drawPolygon(polygon: [number, number][], areaNumber: number): void {
    const highlight: boolean = areaNumber === this.selectedArea;
    this.context.beginPath();
    const firstPoint = polygon[0];
    this.context.moveTo(firstPoint[0], firstPoint[1]);
    
    for (let i = 1; i < polygon.length; i++) {
      this.context.lineTo(polygon[i][0], polygon[i][1]);
    }
    
    this.context.closePath();
    
    if (highlight) {
      this.context.globalAlpha = 0.8;
    } else {
      this.context.globalAlpha = 0.5;
    }
    
    this.context.fillStyle = this.areas[areaNumber].color;
    this.context.fill();
    
    this.context.strokeStyle = this.areas[areaNumber].color;
    this.context.lineWidth = 2;
    this.context.stroke();
    
    this.context.globalAlpha = 1;
    
    for (let i = 0; i < polygon.length; i++) {
      this.context.beginPath();
      this.context.fillStyle = "black";
      this.context.globalAlpha = 1;
      this.context.arc(polygon[i][0], polygon[i][1], 4, 0, 2 * Math.PI);
      this.context.fill();
      
      if (this.isEditMode) {
        this.context.strokeStyle = "#ffcc00";
        this.context.lineWidth = 2;
        this.context.stroke();
      }
    }
    this.context.globalAlpha = 1;
  }

  addNewPoint(x: number, y: number): void {
    this.saveState();
    
    let finishArea: boolean = false;

    if (this.clickedPoints.length > 0) {
      const firstPoint = this.clickedPoints[0];
      const distance = Math.sqrt(Math.pow(x - firstPoint[0], 2) + Math.pow(y - firstPoint[1], 2));
      const distanceThreshold = 15;

      if (this.clickedPoints.length > 2 && distance < distanceThreshold) {
        finishArea = true;
      }
    }

    this.clickedPoints.push([x, y]);
    this.drawScene();

    if (finishArea) {
      this.finishArea();
    }
  }

  finishArea(): void {
    if (this.clickedPoints.length < 3) {
      console.warn("Bereich kann nicht abgeschlossen werden - mindestens 3 Punkte erforderlich");
      return;
    }

    const polygonPoints: [number, number][] = this.clickedPoints.map(p => [
      Math.round(p[0]),
      Math.round(p[1])
    ]);
    
    const areaDataDtoObservable = this.areaCalculationService.calculateAreaManual(
      this.calculatePictureId(),
      polygonPoints
    );

    areaDataDtoObservable.subscribe(
      areaDataDto => {
        const responsePolygon: [number, number][] = Array.isArray(areaDataDto.polygon) 
          ? areaDataDto.polygon as [number, number][]
          : [];
        
        if (responsePolygon.length < 3) {
          console.error("Ungültiges Polygon vom Backend");
          return;
        }
        
        this.saveState();
        const polygonModel = new PolygonModel(responsePolygon);
        this.addArea(areaDataDto.calculated_area.apparent_area_m2, polygonModel);
        
        this.clickedPoints = [];
        this.drawScene();
      },
      error => {
        console.error("Fehler beim Abschließen des Bereichs:", error);
        this.clickedPoints = [];
        this.drawScene();
      }
    );
  }

  private saveState(): void {
    const snapshot: StateSnapshot = {
      clickedPoints: JSON.parse(JSON.stringify(this.clickedPoints)),
      areas: JSON.parse(JSON.stringify(this.areas)),
      selectedArea: this.selectedArea
    };
    this.stateHistory.push(snapshot);
  }

  undo(): void {
    if (this.stateHistory.length > 0) {
      const previousState = this.stateHistory.pop();
      if (previousState) {
        this.clickedPoints = JSON.parse(JSON.stringify(previousState.clickedPoints));
        this.areas = JSON.parse(JSON.stringify(previousState.areas));
        this.selectedArea = previousState.selectedArea;
        this.drawScene();
      }
    }
  }

  toggleEditMode(): void {
    this.isEditMode = !this.isEditMode;
    this.selectedPointIndex = -1;
    this.drawScene();
  }

  private selectPointToEdit(x: number, y: number): void {
    const clickRadius = 40;
    
    for (let i = 0; i < this.clickedPoints.length; i++) {
      const distance = Math.sqrt(
        Math.pow(x - this.clickedPoints[i][0], 2) + 
        Math.pow(y - this.clickedPoints[i][1], 2)
      );
      if (distance < clickRadius) {
        this.saveState();
        this.selectedPointIndex = i;
        this.clickedPoints[i] = [x, y];
        this.drawScene();
        return;
      }
    }

    for (let areaIdx = 0; areaIdx < this.areas.length; areaIdx++) {
      const polygon = this.areas[areaIdx].polygon.points;
      for (let i = 0; i < polygon.length; i++) {
        const distance = Math.sqrt(
          Math.pow(x - polygon[i][0], 2) + 
          Math.pow(y - polygon[i][1], 2)
        );
        if (distance < clickRadius) {
          this.saveState();
          polygon[i] = [x, y];
          this.drawScene();
          return;
        }
      }
    }
  }

  setSelectionMode(selectionMode: AreaMode): void {
    if (!this.buttonManual || !this.buttonSmart) return;

    switch (selectionMode) {
      case AreaMode.MANUAL:
        this.buttonManual.style.borderWidth = "2px";
        this.buttonSmart.style.borderWidth = "1px";
        break;
      case AreaMode.SMART:
        this.buttonManual.style.borderWidth = "1px";
        this.buttonSmart.style.borderWidth = "2px";
        break;
      case AreaMode.UNSELECTED:
        this.buttonManual.style.borderWidth = "1px";
        this.buttonSmart.style.borderWidth = "1px";
        break;
    }

    if (this.areaSelectionMode === selectionMode) {
      this.buttonManual.style.borderWidth = "1px";
      this.buttonSmart.style.borderWidth = "1px";
      this.areaSelectionMode = AreaMode.UNSELECTED;
    } else {
      this.areaSelectionMode = selectionMode;
    }
  }

  onAreasUpdated(): void {
    this.drawScene();
  }

  onSelectedAreaChange(newSelection: number): void {
    this.selectedArea = newSelection;
    this.drawScene();
  }

  async exportPdf(): Promise<void> {
    try {
      if (!this.image) {
        console.error('Kein Bild gesetzt - PDF-Export abgebrochen');
        return;
      }
      this.drawScene();
      const dataUrl = this.canvas?.toDataURL('image/png') || this.image;
      const blob = await this.materialPdf.buildMaterialReport({imageUrl: dataUrl, areas: this.areas});
      if (blob.size < 10) {
        console.warn('Generiertes PDF ist leer.');
        return;
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'material-calculation.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch (e) {
      console.error('PDF-Exportfehler', e);
    }
  }

  private calculatePictureId(): string {
    let pictureId = this.image.split("/")[1];
    return pictureId.replace("png", "tif").replace("jpg", "tif").replace("jpeg", "tif");
  }

  private addArea(size: number, polygon: PolygonModel): void {
    let areaId = 1;
    if (this.areas.length > 0) {
      const lastArea = this.areas[this.areas.length - 1];
      areaId = lastArea.id + 1;
    }
    
    const newArea: Area = {
      id: areaId,
      name: `Gebiet ${areaId}`,
      size: size,
      polygon: polygon,
      layers: [],
      color: this.colors[areaId % this.colors.length]
    };
    
    this.areas.push(newArea);
    this.selectedArea = this.areas.length - 1;
  }

  private registerContinuousModeEventListeners(): void {
    this.canvas.addEventListener('mousedown', (event: MouseEvent) => {
      if (this.areaSelectionMode === AreaMode.CONTINUOUS) {
        const [x, y] = this.getCanvasCoordinates(event);
        this.mouse.x = x;
        this.mouse.y = y;
        this.clickedPoints.push([this.mouse.x, this.mouse.y]);
        this.context.beginPath();
        this.context.moveTo(this.mouse.x, this.mouse.y);
        this.canvas.addEventListener('mousemove', this.drawLineHandler);
      }
    }, false);

    this.canvas.addEventListener('mouseup', (event: MouseEvent) => {
      if (this.areaSelectionMode === AreaMode.CONTINUOUS) {
        this.last_mouse.x = this.mouse.x;
        this.last_mouse.y = this.mouse.y;

        const [x, y] = this.getCanvasCoordinates(event);
        this.mouse.x = x;
        this.mouse.y = y;

        this.clickedPoints.push([this.mouse.x, this.mouse.y]);
        this.canvas.removeEventListener('mousemove', this.drawLineHandler);
      }
    }, false);
  }

  private drawLineHandler = (event: MouseEvent) => {
    const [x, y] = this.getCanvasCoordinates(event);
    this.context.lineTo(x, y);
    this.context.stroke();
  };

  private onCanvasHover(event: MouseEvent): void {
    const [x, y] = this.getCanvasCoordinates(event);

    let hoveredArea: Area | null = null;
    let hoveredAreaIndex: number = -1;

    for (let i = 0; i < this.areas.length; i++) {
      if (this.areas[i].polygon.pointIsInArea(x, y)) {
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

  private showTooltip(area: Area, clientX: number, clientY: number): void {
    if (!this.tooltip) {
      this.tooltip = document.createElement('div');
      document.body.appendChild(this.tooltip);
    }

    this.tooltip.innerHTML = `
      <div style="background: linear-gradient(135deg, #2564ebde 0%, #1d4fd8b9 100%); padding: 12px 16px; border-radius: 10px 10px 0 0; color: white;">
        <div style="font-weight: 600; font-size: 14px; letter-spacing: 0.2px;">${area.name}</div>
      </div>
      <div style="background: #ffffffcf; padding: 12px 16px; border-radius: 0 0 10px 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 16px;">
          <span style="color: #64748b; font-weight: 500; font-size: 12px;">Größe:</span>
          <span style="color: white; font-weight: 600; font-size: 13px; background-color: #2564ebb2; padding: 4px 10px; border-radius: 5px; white-space: nowrap;">${area.size.toFixed(2)} m²</span>
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
    this.tooltip.style.pointerEvents = 'none';
  }

  private hideTooltip(): void {
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