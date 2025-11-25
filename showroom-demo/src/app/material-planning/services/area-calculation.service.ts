import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {ImageMetadataDto} from '../model/image-metadata.dto';
import {Observable} from "rxjs";
import {AreaDataDto} from '../model/area-data.dto';
import {environment} from '../../../environments/environment';

@Injectable({providedIn: 'root'})
export class AreaCalculationService {

  // base url consists of environment.api.baseUrl
  private readonly baseUrl = (() => {
    const root = environment.api.pythonApiUrl.replace(/\/$/, '');
    return `${root}`;
  })();

  constructor(private readonly http: HttpClient) {
  }

  getMetadata(pictureId: string): Observable<ImageMetadataDto> {
    return this.http.get<ImageMetadataDto>(`${this.baseUrl}/metadata/${pictureId}`);
  }

  calculateAreaManual(pictureId: string, polygon: [number, number][]): Observable<AreaDataDto> {
    return this.http.post<AreaDataDto>(`${this.baseUrl}/custom/${pictureId}`, polygon);
  }

  calculateAreaSmart(pictureId: string, point: [number, number]): Observable<AreaDataDto> {
    return this.http.post<AreaDataDto>(`${this.baseUrl}/smart/${pictureId}`, point);
    /*const polygon: [number, number][] = [[point[0] - 100, point[1] - 100], [point[0] + 100, point[1] - 100],[point[0] + 100,point[1] + 100],[point[0] - 100,point[1] + 100]];
    return  this.calculateAreaManual(pictureId, polygon);*/
  }
}
