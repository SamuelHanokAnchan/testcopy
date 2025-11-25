export const environment = {
  production: false,
  api: {
    baseUrl: '/api', // via dev proxy/Vite/Angular dev server
    pythonApiUrl: '/area', // via Proxy
    apiKey: 'dev-demo-key-change-me', // local dev fallback; do NOT use real secrets here
  },
  syncfusionLicense: '' // left empty locally; can be injected if needed
};
