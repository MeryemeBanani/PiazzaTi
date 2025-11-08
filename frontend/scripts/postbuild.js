import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

function copyIndexForRoutes(distDir) {
  const index = path.join(distDir, 'index.html');
  if (!fs.existsSync(index)) {
    console.error('build output index.html not found in', distDir);
    const errMsg = `build output index.html not found in ${distDir}`;
    // avoid referencing `process` directly in environments where it's undefined
    if (typeof globalThis !== 'undefined' && typeof globalThis.process !== 'undefined' && typeof globalThis.process.exit === 'function') {
        globalThis.process.exit(1);
    }
    throw new Error(errMsg);
  }

  // ensure /parse/index.html exists
  const parseDir = path.join(distDir, 'parse');
  if (!fs.existsSync(parseDir)) fs.mkdirSync(parseDir, { recursive: true });
  fs.copyFileSync(index, path.join(parseDir, 'index.html'));

  // ensure /home.html exists (copy of index)
  fs.copyFileSync(index, path.join(distDir, 'home.html'));

  console.log('postbuild: created parse/index.html and home.html in', distDir);
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const distDir = path.resolve(__dirname, '..', 'dist');
copyIndexForRoutes(distDir);
