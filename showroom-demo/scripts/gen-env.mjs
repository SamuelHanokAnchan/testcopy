#!/usr/bin/env node
import { writeFileSync } from 'node:fs';

// Liest benötigte Variablen aus Prozess-Env (GitHub Actions: env / secrets werden exportiert)
const { API_BASE_URL, API_KEY, SYNCFUSION_LICENSE } = process.env;

if (!API_BASE_URL || !API_KEY || !SYNCFUSION_LICENSE) {
  console.error('[gen-env] Fehlende Variablen. Benötigt: API_BASE_URL, API_KEY, SYNCFUSION_LICENSE');
  process.exit(1);
}

const content = `// automatisch erzeugt – nicht einchecken
export const environment = {
  production: true,
  api: {
    baseUrl: '${API_BASE_URL}',
    apiKey: '${API_KEY}'
  },
  syncfusionLicense: '${SYNCFUSION_LICENSE}'
};\n`;

writeFileSync('src/environments/environment.prod.ts', content, 'utf8');
console.log('[gen-env] environment.prod.ts geschrieben');
