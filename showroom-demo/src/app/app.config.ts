import {ApplicationConfig, provideBrowserGlobalErrorListeners, provideZoneChangeDetection} from '@angular/core';
import {provideRouter, Routes, withComponentInputBinding} from '@angular/router';

import {routes} from './app.routes';
import {provideHttpClient, withFetch, withInterceptors} from '@angular/common/http';
import { apiKeyInterceptor } from './shared/interceptors/api-key.interceptor';

const appRoutes: Routes = [];
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({eventCoalescing: true}),
  provideRouter(routes),
    provideHttpClient(withFetch(), withInterceptors([apiKeyInterceptor])),
    provideRouter(appRoutes, withComponentInputBinding())
  ]
};
