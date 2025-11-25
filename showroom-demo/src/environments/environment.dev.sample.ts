// Beispiel-Datei für lokale Entwicklung. Kopiere sie nach environment.dev.ts und
// trage lokale Werte ein. Diese Datei wird versioniert; die echte dev-Datei NICHT.
// ACHTUNG: Keine echten produktiven Secrets hier eintragen.
export const environment = {
  production: false,
  api: {
    baseUrl: '/api', // via Proxy
    pythonApiUrl: '/area', // via Proxy
    apiKey: 'dev-demo-key-change-me' // nur Dummy – echten Key lokal in environment.dev.ts pflegen
  },
  syncfusionLicense: '' // lokal optional direkt setzen oder via Runtime-Injection
};
