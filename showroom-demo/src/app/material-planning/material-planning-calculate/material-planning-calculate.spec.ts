import {ComponentFixture, TestBed} from '@angular/core/testing';

import {MaterialPlanningCalculate} from './material-planning-calculate';
import {provideLocationMocks} from '@angular/common/testing';

describe('MaterialPlanningCalculate', () => {
  let component: MaterialPlanningCalculate;
  let fixture: ComponentFixture<MaterialPlanningCalculate>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MaterialPlanningCalculate],
      providers: [provideLocationMocks()]
    })
      .compileComponents();

    fixture = TestBed.createComponent(MaterialPlanningCalculate);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
