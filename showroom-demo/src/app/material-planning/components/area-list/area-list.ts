import {Component, Input, model, ModelSignal, OnInit, output} from '@angular/core';
import {Area} from '../../model/area';
import {ButtonModule} from '@syncfusion/ej2-angular-buttons';
import {Layer} from '../../model/layer';
import {ChangeEventArgs, DropDownListModule, FieldSettingsModel} from '@syncfusion/ej2-angular-dropdowns';
import {MaterialCalculationService} from '../../services/material-calculation.service';
import {MaterialDto, MaterialUnit} from '../../model/material.dto';

@Component({
  selector: 'app-area-list',
  standalone: true,
  imports: [
    ButtonModule,
    DropDownListModule
  ],
  templateUrl: './area-list.html',
  styleUrl: './area-list.css'
})
export class AreaList implements OnInit {
  @Input()
  areas: Area[] = [];
  areasUpdated = output<void>();
  selectedArea: ModelSignal<number> = model.required<number>();

  public fields: FieldSettingsModel = {text: 'name', value: 'name'};
  public height: string = '220px';
  public waterMark: string = 'Wähle ein Material aus:';
  public debounceDelay: number = 300;
  public filterPlaceholder: string = 'Search';

  public materials: MaterialDto[];
  protected readonly MaterialUnit = MaterialUnit;

  constructor(private readonly materialCalculationService: MaterialCalculationService) {
    this.materials = materialCalculationService.getMaterials();
  }

  ngOnInit(): void {
    this.setBorderColor();
  }

  setBorderColor(): void {
    let cardList = document.getElementsByClassName("e-card");
    for (let i = 0; i < cardList.length; i++) {
      if (this.areas[i]) {
        (cardList[i] as HTMLElement).style.borderColor = this.areas[i].color;
      }
    }
  }

  addLayer(area: Area): void {
    const lastLayer = area.layers[area.layers.length - 1];
    let id = 0;
    if (lastLayer) {
      id = lastLayer.id + 1;
    }
    area.layers.push({id: id, name: `Schicht ${id}`, material: null, depth: 0.1});
  }

  calculateCost(area: Area): number {
    let cost = 0;
    for (let i = 0; i < area.layers.length; i++) {
      cost += this.calculateLayerCost(area, area.layers[i]);
    }
    return cost;
  }

  calculateLayerCost(area: Area, layer: Layer): number {
    const material = layer.material;
    let cost = 0;
    if (material) {
      switch (material.unit) {
        case MaterialUnit.EURO_PER_SQUARE_METER:
          cost = material.price * area.size;
          break;
        case MaterialUnit.EURO_PER_CUBIC_METER:
          cost = area.size * layer.depth * material.price;
          break;
        case MaterialUnit.EURO_PER_LITER:
          cost = area.size * layer.depth * 1000 * material.price;
          break;
        case MaterialUnit.EURO_PER_METER:
          cost = material.price * area.size;
          break;
        default:
          cost = material.price * area.size;
          break;
      }
    }
    return cost;
  }

  deleteArea(area: Area): void {
    const areaIndex = this.areas.indexOf(area);
    if (areaIndex > -1) {
      this.areas.splice(areaIndex, 1);
    }
    this.areasUpdated.emit();
  }

  deleteLayer(area: Area, layer: Layer): void {
    const layerIndex = area.layers.indexOf(layer);
    if (layerIndex > -1) {
      area.layers.splice(layerIndex, 1);
    }
  }

  onAreaNameChange(event: Event, area: Area): void {
    const data = ((event as InputEvent).target as HTMLInputElement).value;
    if (area && data) {
      area.name = data;
    }
    this.areasUpdated.emit();
  }

  onLayerNameChange(event: Event, area: Area, layer: Layer): void {
    const data = ((event as InputEvent).target as HTMLInputElement).value;
    if (layer && data) {
      layer.name = data;
    }
  }

  onLayerDepthChange(event: Event, area: Area, layer: Layer): void {
    const data = ((event as InputEvent).target as HTMLInputElement).value;
    if (layer && data) {
      layer.depth = parseFloat(data) / 100;
    }
  }

  onLayerTypeDropdownChange(event: ChangeEventArgs, layer: Layer): void {
    layer.material = event.value as MaterialDto;
  }

  onFiltering(event: any): void {
  }

  onSelectArea(area: Area): void {
    this.selectedArea.update(() => this.areas.indexOf(area));
  }

  isAreaSelected(area: Area): boolean {
    return this.selectedArea() === this.areas.indexOf(area);
  }
}