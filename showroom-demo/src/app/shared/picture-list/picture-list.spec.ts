import {ComponentFixture, TestBed} from '@angular/core/testing';

import {PictureList} from './picture-list';
import {provideHttpClient} from '@angular/common/http';

describe('PictureList', () => {
  let component: PictureList;
  let fixture: ComponentFixture<PictureList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PictureList],
      providers: [provideHttpClient()]
    })
      .compileComponents();

    fixture = TestBed.createComponent(PictureList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
