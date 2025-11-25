import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    watch: {
      // Ignoriere alle Änderungen in android/ und ios/
      ignored: ['**/node_modules/'],
    },
    proxy: {
      // Adjust target to your backend host:port
      '/api': {
      target: 'https://localhost:7178',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
