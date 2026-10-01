import fs from 'fs';
import path from 'path';
import { JSDOM } from 'jsdom';

const files = [
  'API/Fundamentals/01_api_fundamentals.md',
  'API/Fundamentals/02_http_and_web_foundations.md',
  'API/Fundamentals/03_cross_cutting_concerns.md',
  'API/Fundamentals/04_choosing_the_right_api.md',
  'API/REST/Theory.md',
  'API/GraphQL/Theory.md',
  'API/SOAP/Theory.md',
  'API/WebSockets/Theory.md',
  'API/Webhooks/Theory.md',
  'API/gRPC/Theory.md',
  'API/Protobuf/Theory.md',
];

const dom = new JSDOM('<!DOCTYPE html><body></body>', { pretendToBeVisual: true });
global.window = dom.window;
global.document = dom.window.document;
global.SVGElement = dom.window.SVGElement || class {};
if (!global.navigator) {
  Object.defineProperty(global, 'navigator', { value: dom.window.navigator, configurable: true });
}

const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });

let totalBlocks = 0, failures = 0;

for (const rel of files) {
  const full = path.join('/Users/njasm/Njasm/AI/DSA-Practice', rel);
  if (!fs.existsSync(full)) { console.log(`SKIP (missing): ${rel}`); continue; }
  const text = fs.readFileSync(full, 'utf8');
  const re = /```mermaid\n([\s\S]*?)```/g;
  let m, i = 0;
  while ((m = re.exec(text))) {
    i++; totalBlocks++;
    const code = m[1];
    try {
      await mermaid.parse(code);
      console.log(`OK   ${rel} block #${i}`);
    } catch (e) {
      failures++;
      console.log(`FAIL ${rel} block #${i}: ${e.message.split('\n')[0]}`);
      console.log('  --- offending source ---');
      console.log(code.split('\n').map(l => '    ' + l).join('\n'));
    }
  }
}

console.log(`\n${totalBlocks} mermaid blocks checked, ${failures} failed.`);
process.exit(failures ? 1 : 0);
