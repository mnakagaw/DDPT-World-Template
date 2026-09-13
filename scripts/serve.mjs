import http from 'node:http';
import path from 'node:path';
import { stat, realpath } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { parseArgs, isMain, reportError } from '../lib/cli.mjs';
const mime = { '.html':'text/html; charset=utf-8', '.mjs':'text/javascript; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.css':'text/css; charset=utf-8', '.json':'application/json; charset=utf-8', '.md':'text/markdown; charset=utf-8', '.csv':'text/csv; charset=utf-8', '.txt':'text/plain; charset=utf-8', '.svg':'image/svg+xml', '.png':'image/png', '.pdf':'application/pdf' };
export async function serveDirectory(directory, port = 4173) {
  const root = await realpath(path.resolve(directory));
  const inside = file => { const relative = path.relative(root, file); return relative === '' || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative)); };
  const server = http.createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'self'");
    if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405, { Allow: 'GET, HEAD' }); res.end(); return; }
    try {
      const name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      if (name.includes('\0') || name.includes('\\')) throw new Error('Invalid path');
      let file = path.resolve(root, '.' + name);
      if (!inside(file)) throw new Error('Outside site directory');
      let info = await stat(file);
      if (info.isDirectory()) { file = path.join(file, 'index.html'); info = await stat(file); }
      const actual = await realpath(file);
      if (!inside(actual) || !info.isFile()) throw new Error('Invalid file');
      res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream', 'Content-Length': info.size });
      if (req.method === 'HEAD') res.end();
      else createReadStream(actual).on('error', () => res.destroy()).pipe(res);
    } catch { res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }); res.end('Not found'); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', resolve); });
  return server;
}
if (isMain(import.meta.url)) {
  try {
    const args = parseArgs(process.argv.slice(2), ['dir', 'port']);
    if (args.help) console.log('node scripts/serve.mjs --dir generated/uganda/site [--port 4173]');
    else {
      if (!args.dir) throw new Error('Provide --dir <site directory>');
      const port = Number(args.port || 4173);
      if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Port must be 1–65535');
      const server = await serveDirectory(args.dir, port);
      console.log(`Preview: http://127.0.0.1:${server.address().port}/`);
    }
  } catch (error) { reportError(error); }
}
