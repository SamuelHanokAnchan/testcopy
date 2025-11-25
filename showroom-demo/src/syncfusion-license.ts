import { registerLicense } from '@syncfusion/ej2-base';
import { environment } from './environments/environment';

// Die Lizenz wird nur registriert, wenn sie vorhanden ist (lokal meist leer; Produktion via Secret injiziert)
if (environment.syncfusionLicense && !environment.syncfusionLicense.startsWith('__')) {
  registerLicense(environment.syncfusionLicense);
}

