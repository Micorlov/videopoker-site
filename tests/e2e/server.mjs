// Static server for _site/ that behaves like GitHub Pages: case-sensitive paths,
// directory -> index.html, and 404.html with a real 404 status on a miss.
// (build.py --serve uses Python's server, which on macOS is case-insensitive and
// would hide the wrong-case URLs that 404.html exists to redirect.)
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../_site')
const PORT = Number(process.env.PORT || 4173)
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.xml': 'application/xml', '.txt': 'text/plain',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp',
}

function resolveExact(urlPath) {
  let current = ROOT
  for (const part of decodeURIComponent(urlPath).split('/').filter(Boolean)) {
    if (part === '..' || !fs.statSync(current).isDirectory()) return null
    if (!fs.readdirSync(current).includes(part)) return null
    current = path.join(current, part)
  }
  if (fs.statSync(current).isDirectory()) {
    current = path.join(current, 'index.html')
    if (!fs.existsSync(current)) return null
  }
  return current
}

http.createServer((req, res) => {
  const { pathname } = new URL(req.url, 'http://localhost')
  const file = resolveExact(pathname)
  const target = file ?? path.join(ROOT, '404.html')
  res.writeHead(file ? 200 : 404, { 'Content-Type': TYPES[path.extname(target)] ?? 'application/octet-stream' })
  fs.createReadStream(target).pipe(res)
}).listen(PORT, () => console.log(`serving _site on http://localhost:${PORT}`))
