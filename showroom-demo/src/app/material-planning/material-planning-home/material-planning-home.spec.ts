import {ComponentFixture, TestBed} from '@angular/core/testing';

import {MaterialPlanningHome} from './material-planning-home';
import {provideHttpClient} from '@angular/common/http';

describe('MaterialPlanningHome', () => {
  let component: MaterialPlanningHome;
  let fixture: ComponentFixture<MaterialPlanningHome>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MaterialPlanningHome],
      providers: [provideHttpClient()]
    })
      .compileComponents();

    fixture = TestBed.createComponent(MaterialPlanningHome);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
