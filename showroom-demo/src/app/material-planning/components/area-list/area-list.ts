import {Component, Input, model, ModelSignal, OnInit, output} from '@angular/core';
import {Area} from '../../model/area';
import {ButtonModule} from '@syncfusion/ej2-angular-buttons';
import {Layer} from '../../model/layer';
import {ChangeEventArgs, DropDownListModule, FieldSettingsModel} from '@syncfusion/ej2-angular-dropdowns';
import {MaterialCalculationService} from '../../services/material-calculation.service';
import {MaterialDto, MaterialUnit} from '../../model/material.dto';

@Component({
  selector: 'app-area-list',
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

  // maps the appropriate column to fields property
  public fields: FieldSettingsModel = {text: 'name', value: 'name'};
  // set the height of the popup element
  public height: string = '220px';
  // the default value in dropdown
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

  setBorderColor() {
    let cardList = document.getElementsByClassName("e-card");
    for (let i = 0; i < cardList.length; i++) {
      (cardList[i] as HTMLElement).style = `border-color = ${this.areas[i].color}`;
    }
  }

  addLayer(area: Area) {
    const lastLayer = area.layers[area.layers.length - 1];
    let id = 0;
    if (lastLayer) {
      id = lastLayer.id + 1;
    }
    area.layers.push({id: id, name: `Neue Schicht ${id}`, material: null, depth: 0.1})
  }

  calculateCost(area: Area): number {
    let cost = 0;
    for (let i = 0; i < area.layers.length; i++) {
      cost += this.calculateLayerCost(area, area.layers[i])
    }
    return cost;
  }

  calculateLayerCost(area: Area, layer: Layer): number {
    const material = layer.material;
    let cost = 0;
    if (material) {
      switch (material.unit) {
        default:
          cost = material.price * area.size;
          break;
        case MaterialUnit.EURO_PER_CUBIC_METER:
          cost = area.size * layer.depth * material.price;
          break;
        case MaterialUnit.EURO_PER_LITER:
          cost = area.size * layer.depth * 1000 * material.price; // 1m^3 = 1000l
          break;
      }
    }
    return cost;
  }

  deleteArea(area: Area) {
    const areaIndex = this.areas.indexOf(area);
    if (areaIndex > -1) {
      this.areas.splice(areaIndex, 1);
    }
    this.areasUpdated.emit();
  }

  deleteLayer(area: Area, layer: Layer) {
    const layerIndex = area.layers.indexOf(layer);
    if (layerIndex > -1) {
      area.layers.splice(layerIndex, 1);
    }
  }

  onAreaNameChange($event: Event, area: Area) {
    const data = (($event as InputEvent).target as HTMLInputElement).value;
    if (area && data) {
      area.name = data;
    }
    this.areasUpdated.emit();
  }

  onLayerNameChange(event: Event, area: Area, layer: Layer) {
    const data = ((event as InputEvent).target as HTMLInputElement).value;
    if (layer && data) {
      layer.name = data;
    }
  }

  onLayerDepthChange(event: Event, area: Area, layer: Layer) {
    const data = ((event as InputEvent).target as HTMLInputElement).value;
    if (layer && data) {
      layer.depth = parseFloat(data) / 100;
    }
  }

  onLayerTypeDropdownChange($event: any, layer: Layer) {
    layer.material = ($event as ChangeEventArgs).value as MaterialDto;
    layer.name = layer.name + " " + layer.material.name;
  }

  onFiltering($event: any) {

  }

  onSelectArea(area: Area) {
    this.selectedArea.update(() => this.areas.indexOf(area));
  }

  isAreaSelected(area: Area): boolean {
    return this.selectedArea() == this.areas.indexOf(area);
  }
}
