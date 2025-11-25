import {HttpInterceptorFn} from '@angular/common/http';
import {environment} from '../../../environments/environment';

// Fügt für Backend-Requests (beginnend mit baseUrl) den API Key Header hinzu, sofern nicht bereits vorhanden.
export const apiKeyInterceptor: HttpInterceptorFn = (req, next) => {
  const baseUrl = environment.api.baseUrl || '/api';
  const pythonBaseUrl = environment.api.pythonApiUrl || '/area';

  if ((req.url.startsWith(baseUrl) || req.url.startsWith(pythonBaseUrl)) && !req.headers.has('X-Api-Key') && environment.api.apiKey) {
    req = req.clone({
      setHeaders: {
        'X-Api-Key': environment.api.apiKey
      }
    });
  }
  return next(req);
};
