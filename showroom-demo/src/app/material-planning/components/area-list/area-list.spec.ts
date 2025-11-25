import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AreaList } from './area-list';

describe('AreaList', () => {
  let component: AreaList;
  let fixture: ComponentFixture<AreaList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AreaList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AreaList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
