#!/usr/bin/env node
// Cross-platform starter for the Python image-calculation service.
// Mirrors logic from image-calculation/startup.sh
// Requirements: Python with uvicorn installed per image-calculation/requirements.txt

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const projectRoot = path.resolve(__dirname, '..', '..');
const serviceDir = path.join(projectRoot, 'image-calculation');

// Environment
process.env.API_KEY = process.env.API_KEY || 'dev-demo-key-change-me';

// SSL files
const keyFile = path.join(serviceDir, 'key.pem');
const certFile = path.join(serviceDir, 'cert.pem');

if (!fs.existsSync(keyFile) || !fs.existsSync(certFile)) {
  console.warn('[start-image-service] SSL key/cert not found, starting WITHOUT TLS on http://localhost:8000');
}

// Determine python executable (prefer venv if present)
function resolvePython() {
  const candidates = process.platform === 'win32'
    ? ['python', 'python3', 'py']
    : ['python3', 'python'];
  for (const c of candidates) {
    // We rely on PATH; a more elaborate check could spawn --version sync.
    return c; // first is fine; if it fails user will see error
  }
}

const python = resolvePython();
const args = ['-m', 'uvicorn', 'main:app', '--port=8000'];
if (fs.existsSync(keyFile) && fs.existsSync(certFile)) {
  args.push(`--ssl-keyfile=${keyFile}`);
  args.push(`--ssl-certfile=${certFile}`);
}

console.log('[start-image-service] Starting image calculation service...');
const proc = spawn(python, args, {
  cwd: serviceDir,
  stdio: 'inherit',
  env: process.env
});

proc.on('close', (code) => {
  console.log(`[start-image-service] Service exited with code ${code}`);
  process.exit(code);
});
