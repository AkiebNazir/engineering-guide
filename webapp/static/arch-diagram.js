/* arch-diagram.js — renders ```arch blocks as AWS-style architecture diagrams.

   Why not mermaid: its layout engines (dagre, elk, architecture-beta's fcose)
   place boxes for you, and on real system diagrams that means crossing lines,
   groups that overlap, and nodes flung to the far edge. Here the author places
   every node on a grid cell, groups become tinted panels sized to their members,
   and edges are routed orthogonally through the gutters between cells (A* with
   bend, overlap and crossing penalties). Same input, same picture, every time.

   The syntax (full reference: webapp/ARCH_DIAGRAMS.md):

     %% caption: One sentence under the figure.
     grid 180x130                              optional cell size (px)
     group r1 "Region 1" icon=region color=purple
     group vpc "VPC" in r1 color=green style=solid
     node lb  "Load Balancer" at 1,0 in vpc icon=lb
     node app "App servers"   at 1,1 in vpc icon=server sub="autoscaled"
     lb -> app
     app ..> cache : "async fill"
     a:R -> b:L                                force the ports (T/B/L/R)

   Works in the browser (window.ArchDiagram) and in Node (require) so the repo
   validator and screenshot tool render exactly what the reader shows. */
(function (root) {
  'use strict';

  /* ------------------------------------------------------------ palette -- */
  // name → [light-mode, dark-mode] accent. Groups tint with it; tiles use CAT.
  const COLORS = {
    blue: ['#2563eb', '#6ea8ff'], purple: ['#7c3aed', '#b196ff'], green: ['#15803d', '#4fcf8e'],
    orange: ['#c2410c', '#f59e5b'], red: ['#c81e3a', '#f2727c'], pink: ['#be185d', '#f28ac0'],
    teal: ['#0f766e', '#4fc1b0'], slate: ['#475569', '#9ba6b9'], amber: ['#a16207', '#f5b453'],
    indigo: ['#4338ca', '#8b93ff'], cyan: ['#0e7490', '#5cc8e0'],
  };
  // tile category → gradient (AWS console colours). Same in both themes.
  const CAT = {
    compute: ['#F78E04', '#D05C17', 'orange'], network: ['#A166FF', '#5A30B5', 'purple'],
    storage: ['#7AA116', '#3F8624', 'green'], database: ['#4D72F3', '#3334B9', 'blue'],
    security: ['#F54749', '#BE0917', 'red'], messaging: ['#FF4F8B', '#BC1356', 'pink'],
    client: ['#78909C', '#455A64', 'slate'], ai: ['#2EBB9F', '#0B6E5A', 'teal'],
    observe: ['#E7157B', '#9E1159', 'pink'], analytics: ['#945DF2', '#4D27AA', 'indigo'],
    generic: ['#5B8DEF', '#2F5BB7', 'blue'], dev: ['#F2B632', '#B27A06', 'amber'],
  };

  /* -------------------------------------------------------------- icons -- */
  // Short name → [glyph, category]. Glyph bodies live in arch-icons.json
  // (built by webapp/build_arch_icons.mjs). 'logos:*' glyphs are full-colour
  // brand marks and are drawn as-is, not on a tinted tile.
  const ICONS = {
    // people & clients
    user: ['mdi:account', 'client'], users: ['mdi:account-group', 'client'], admin: ['mdi:account-tie', 'client'],
    client: ['mdi:monitor', 'client'], browser: ['mdi:web', 'client'], mobile: ['mdi:cellphone', 'client'],
    desktop: ['mdi:desktop-tower', 'client'], cli: ['mdi:console', 'client'], developer: ['mdi:code-braces', 'client'],
    // network & edge
    internet: ['mdi:earth', 'network'], dns: ['mdi:dns', 'network'], cdn: ['mdi:earth', 'network'],
    lb: ['mdi:call-split', 'network'], gateway: ['mdi:router-network', 'network'], api: ['mdi:api', 'network'],
    network: ['mdi:lan', 'network'], firewall: ['mdi:wall', 'security'], proxy: ['mdi:swap-horizontal', 'network'],
    mesh: ['mdi:hexagon-multiple-outline', 'network'], region: ['mdi:map-marker-path', 'network'],
    cloud: ['mdi:cloud-outline', 'network'], wifi: ['mdi:wifi', 'network'], link: ['mdi:link-variant', 'network'],
    connection: ['mdi:connection', 'network'], edge: ['mdi:access-point-network', 'network'],
    // compute
    server: ['mdi:server', 'compute'], service: ['mdi:cube-outline', 'compute'], app: ['mdi:application-cog-outline', 'compute'],
    worker: ['mdi:cogs', 'compute'], process: ['mdi:cog', 'compute'], function: ['mdi:lambda', 'compute'],
    container: ['mdi:docker', 'compute'], k8s: ['mdi:kubernetes', 'compute'], cpu: ['mdi:chip', 'compute'],
    memory: ['mdi:memory', 'compute'], scheduler: ['mdi:calendar-clock', 'compute'], cron: ['mdi:clock-outline', 'compute'],
    thread: ['mdi:format-list-bulleted', 'compute'], code: ['mdi:file-code-outline', 'dev'], package: ['mdi:package-variant-closed', 'dev'],
    rocket: ['mdi:rocket-launch-outline', 'dev'], git: ['mdi:source-branch', 'dev'], plugin: ['mdi:puzzle-outline', 'dev'],
    // data
    db: ['mdi:database', 'database'], sql: ['mdi:database', 'database'], nosql: ['mdi:database-outline', 'database'],
    replica: ['mdi:database-sync', 'database'], index: ['mdi:database-search', 'database'], table: ['mdi:table', 'database'],
    cache: ['mdi:flash', 'database'], kv: ['mdi:key-variant', 'database'], search: ['mdi:magnify', 'analytics'],
    storage: ['mdi:bucket-outline', 'storage'], blob: ['mdi:bucket-outline', 'storage'], disk: ['mdi:harddisk', 'storage'],
    file: ['mdi:file-outline', 'storage'], doc: ['mdi:file-document-outline', 'storage'], folder: ['mdi:folder-outline', 'storage'],
    archive: ['mdi:archive-outline', 'storage'], layers: ['mdi:layers-triple-outline', 'storage'],
    vector: ['mdi:vector-triangle', 'ai'], graph: ['mdi:graph', 'analytics'], tree: ['mdi:family-tree', 'analytics'],
    matrix: ['mdi:matrix', 'analytics'], grid: ['mdi:grid', 'analytics'], counter: ['mdi:counter', 'analytics'],
    sort: ['mdi:sort-ascending', 'analytics'], filter: ['mdi:filter-outline', 'analytics'], sigma: ['mdi:sigma', 'analytics'],
    // messaging & integration
    queue: ['mdi:tray-full', 'messaging'], stream: ['mdi:transit-connection-variant', 'messaging'], topic: ['mdi:inbox-multiple', 'messaging'],
    event: ['mdi:lightning-bolt', 'messaging'], webhook: ['mdi:webhook', 'messaging'], email: ['mdi:email-outline', 'messaging'],
    notify: ['mdi:bell-outline', 'messaging'], message: ['mdi:message-text-outline', 'messaging'], chat: ['mdi:chat-outline', 'messaging'],
    sync: ['mdi:sync', 'messaging'], workflow: ['mdi:state-machine', 'messaging'], sitemap: ['mdi:sitemap-outline', 'messaging'],
    // security
    auth: ['mdi:shield-lock', 'security'], lock: ['mdi:lock-outline', 'security'], key: ['mdi:key-variant', 'security'],
    secrets: ['mdi:safe', 'security'], identity: ['mdi:account-key-outline', 'security'], shield: ['mdi:shield-check', 'security'],
    alert: ['mdi:shield-alert-outline', 'security'],
    // observability
    metrics: ['mdi:chart-line', 'observe'], dashboard: ['mdi:view-dashboard-outline', 'observe'], logs: ['mdi:text-box-outline', 'observe'],
    monitor: ['mdi:heart-pulse', 'observe'], gauge: ['mdi:gauge', 'observe'], trace: ['mdi:binoculars', 'observe'],
    timer: ['mdi:timer-sand', 'observe'], speed: ['mdi:speedometer', 'observe'], eye: ['mdi:eye-outline', 'observe'],
    // AI
    llm: ['mdi:brain', 'ai'], model: ['mdi:brain', 'ai'], agent: ['mdi:robot-outline', 'ai'], bot: ['mdi:robot', 'ai'],
    tool: ['mdi:wrench', 'ai'], prompt: ['mdi:format-text', 'ai'], embed: ['mdi:vector-triangle', 'ai'], idea: ['mdi:lightbulb-outline', 'ai'],
    // commerce & misc
    payment: ['mdi:credit-card-outline', 'generic'], cart: ['mdi:cart-outline', 'generic'], store: ['mdi:store-outline', 'generic'],
    delivery: ['mdi:truck-fast-outline', 'generic'], map: ['mdi:map-outline', 'generic'], video: ['mdi:video-outline', 'generic'],
    image: ['mdi:image-outline', 'generic'], music: ['mdi:music-note-outline', 'generic'], news: ['mdi:newspaper-variant-outline', 'generic'],
    feed: ['mdi:newspaper-variant-outline', 'generic'], tag: ['mdi:tag-outline', 'generic'], id: ['mdi:identifier', 'generic'],
    decision: ['mdi:arrow-decision', 'generic'], check: ['mdi:check-circle-outline', 'storage'], error: ['mdi:close-circle-outline', 'security'],
    warn: ['mdi:alert-outline', 'dev'], question: ['mdi:help-circle-outline', 'generic'], start: ['mdi:play-circle-outline', 'storage'],
    stop: ['mdi:stop-circle-outline', 'security'], edit: ['mdi:pencil-outline', 'generic'], delete: ['mdi:delete-outline', 'security'],
    flag: ['mdi:flag-outline', 'generic'], learn: ['mdi:school-outline', 'generic'], group: ['mdi:select-group', 'generic'],
    text: ['mdi:text-search', 'analytics'], number: ['mdi:numeric', 'analytics'], forum: ['mdi:forum-outline', 'messaging'],
    time: ['mdi:clock-outline', 'observe'],
  };
  // brand marks, usable as icon=<name> (the 'logos:' prefix is optional)
  const LOGOS = ['aws-api-gateway', 'aws-aurora', 'aws-cloudfront', 'aws-cloudwatch', 'aws-cognito', 'aws-dynamodb', 'aws-ec2',
    'aws-ecs', 'aws-eks', 'aws-elasticache', 'aws-elb', 'aws-eventbridge', 'aws-fargate', 'aws-glacier', 'aws-iam', 'aws-kinesis',
    'aws-kms', 'aws-lambda', 'aws-msk', 'aws-open-search', 'aws-rds', 'aws-redshift', 'aws-route53', 'aws-s3', 'aws-secrets-manager',
    'aws-sns', 'aws-sqs', 'aws-step-functions', 'aws-vpc', 'aws-waf', 'aws-athena', 'aws-glue', 'aws-neptune', 'aws-timestream',
    'kafka-icon', 'redis', 'postgresql', 'mongodb-icon', 'cassandra', 'elasticsearch', 'rabbitmq-icon', 'nginx', 'docker-icon',
    'kubernetes', 'grpc', 'graphql', 'openai-icon', 'anthropic-icon', 'prometheus', 'grafana', 'python', 'go', 'react',
    'cloudflare-icon', 'google-cloud', 'google-gemini-icon', 'mysql-icon', 'sqlite', 'etcd', 'consul', 'vault-icon',
    'terraform-icon', 'github-icon', 'git-icon', 'jenkins', 'nodejs-icon', 'java', 'rust', 'linux-tux', 'apache-spark',
    'apache-flink-icon', 'hadoop', 'memcached', 'datadog-icon', 'stripe', 'slack-icon', 'twilio-icon', 'envoy',
    'meta-icon', 'mistral-ai-icon', 'pinecone-icon', 'swagger', 'postman-icon',
    'websocket', 'json', 'html-5', 'chrome', 'android-icon', 'apple', 'fastapi-icon', 'flask', 'django-icon'];

  function resolveIcon(name) {
    if (!name) return null;
    if (ICONS[name]) return { glyph: ICONS[name][0], cat: ICONS[name][1] };
    const bare = name.replace(/^logos:/, '');
    if (LOGOS.includes(bare)) return { glyph: 'logos:' + bare, logo: true };
    if (/^mdi:/.test(name)) return { glyph: name, cat: 'generic' };
    return null;
  }

  /* ------------------------------------------------------------- parsing -- */
  const ARROWS = {
    '->': { end: true }, '<->': { start: true, end: true }, '--': {},
    '..>': { end: true, dashed: true }, '<..>': { start: true, end: true, dashed: true }, '..': { dashed: true },
    '==>': { end: true, thick: true }, '<==>': { start: true, end: true, thick: true }, '==': { thick: true },
  };
  const SIDES = { T: 'T', B: 'B', L: 'L', R: 'R' };
  const SHAPES = ['tile', 'card', 'box', 'circle', 'pill', 'diamond', 'text', 'cyl'];

  function tokenize(line) {
    const out = [];
    const re = /"((?:[^"\\]|\\.)*)"|(\S+)/g;
    let m;
    while ((m = re.exec(line))) out.push(m[1] !== undefined ? { q: true, v: m[1].replace(/\\"/g, '"').replace(/\\n/g, '\n') } : { q: false, v: m[2] });
    return out;
  }
  // key=value pairs where value may be a quoted string split across tokens
  function readOpts(toks, i, lineNo) {
    const o = {}, flags = [];
    for (; i < toks.length; i++) {
      const t = toks[i];
      if (t.q) throw err(lineNo, `unexpected quoted text "${t.v}"`);
      const eq = t.v.indexOf('=');
      if (eq < 0) { flags.push(t.v); continue; }
      const k = t.v.slice(0, eq);
      let v = t.v.slice(eq + 1);
      if (v === '' && toks[i + 1] && toks[i + 1].q) { v = toks[++i].v; }
      else if (v.startsWith('"')) {                // key="multi word" that the tokenizer split
        let s = v;
        while (!/"$/.test(s) || s.length < 2) { if (!toks[i + 1]) break; s += ' ' + (toks[++i].q ? `"${toks[i].v}"` : toks[i].v); }
        v = s.replace(/^"|"$/g, '');
      }
      o[k] = v;
    }
    return { o, flags };
  }
  function err(lineNo, msg) { const e = new Error(`line ${lineNo}: ${msg}`); e.line = lineNo; return e; }

  function parse(src) {
    const model = { cw: 160, ch: 120, route: 'ortho', groups: [], nodes: [], edges: [], caption: '', warnings: [] };
    const gById = {}, nById = {};
    const lines = String(src).split('\n');
    lines.forEach((raw, li) => {
      const lineNo = li + 1;
      const line = raw.trim();
      if (!line) return;
      const cap = line.match(/^%%\s*caption:\s*(.+)$/);
      if (cap) { model.caption = cap[1].trim(); return; }
      if (line.startsWith('%%')) return;
      const toks = tokenize(line);
      const head = toks[0].v;
      if (head === 'grid') {
        const m = toks.slice(1).map(t => t.v).join(' ').match(/^(\d+)\s*[x ]\s*(\d+)$/);
        if (!m) throw err(lineNo, 'grid needs WIDTHxHEIGHT, e.g. grid 180x130');
        model.cw = +m[1]; model.ch = +m[2];
        return;
      }
      if (head === 'route') {
        if (!['ortho', 'straight'].includes(toks[1] && toks[1].v)) throw err(lineNo, 'route is ortho or straight');
        model.route = toks[1].v;
        return;
      }
      if (head === 'group') {
        const id = toks[1] && toks[1].v, label = toks[2] && toks[2].q ? toks[2].v : null;
        if (!id || label === null) throw err(lineNo, 'group needs an id and a "Label"');
        if (gById[id] || nById[id]) throw err(lineNo, `duplicate id "${id}"`);
        let i = 3, parent = null;
        if (toks[i] && toks[i].v === 'in') { parent = toks[i + 1] && toks[i + 1].v; i += 2; }
        const { o } = readOpts(toks, i, lineNo);
        const g = { id, label, parent, color: o.color || 'slate', icon: o.icon || null, style: o.style || null, line: lineNo, kids: [], nodes: [] };
        if (!COLORS[g.color]) throw err(lineNo, `unknown color "${g.color}" (${Object.keys(COLORS).join(', ')})`);
        if (g.icon && !resolveIcon(g.icon)) throw err(lineNo, `unknown icon "${g.icon}"`);
        if (g.style && !['dashed', 'solid'].includes(g.style)) throw err(lineNo, 'group style is dashed or solid');
        gById[id] = g; model.groups.push(g);
        return;
      }
      if (head === 'node') {
        const id = toks[1] && toks[1].v, label = toks[2] && toks[2].q ? toks[2].v : null;
        if (!id || label === null) throw err(lineNo, 'node needs an id and a "Label"');
        if (gById[id] || nById[id]) throw err(lineNo, `duplicate id "${id}"`);
        let i = 3, at = null, parent = null;
        while (toks[i] && (toks[i].v === 'at' || toks[i].v === 'in')) {
          if (toks[i].v === 'at') {
            const m = (toks[i + 1] && toks[i + 1].v || '').match(/^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/);
            if (!m) throw err(lineNo, 'at needs COL,ROW, e.g. at 2,1');
            at = [+m[1], +m[2]];
          } else parent = toks[i + 1] && toks[i + 1].v;
          i += 2;
        }
        if (!at) throw err(lineNo, `node "${id}" needs a position: at COL,ROW`);
        const { o } = readOpts(toks, i, lineNo);
        const icon = o.icon ? resolveIcon(o.icon) : null;
        if (o.icon && !icon) throw err(lineNo, `unknown icon "${o.icon}"`);
        const shape = o.shape || (icon ? 'tile' : 'box');
        if (!SHAPES.includes(shape)) throw err(lineNo, `unknown shape "${shape}" (${SHAPES.join(', ')})`);
        if (shape === 'tile' && !icon) throw err(lineNo, 'shape=tile needs an icon');
        const color = o.color || (icon && icon.cat ? CAT[icon.cat][2] : 'slate');
        if (!COLORS[color]) throw err(lineNo, `unknown color "${color}"`);
        const n = { id, label, col: at[0], row: at[1], parent, icon, shape, color, sub: o.sub || '', w: o.w ? +o.w : 0, line: lineNo };
        nById[id] = n; model.nodes.push(n);
        return;
      }
      // edge (possibly a chain): a -> b -> c [: "label"] [flags]
      const parts = [];
      let i = 0;
      const endpoint = t => {
        const m = t && !t.q && t.v.match(/^([A-Za-z_][\w-]*)(?::([TBLR]))?$/);
        if (!m) throw err(lineNo, `expected a node id, got "${t ? t.v : 'end of line'}"`);
        return { id: m[1], side: m[2] || null };
      };
      parts.push(endpoint(toks[i++]));
      while (toks[i] && ARROWS[toks[i].v]) {
        const arrow = toks[i++].v;
        parts.push(arrow, endpoint(toks[i++]));
      }
      if (parts.length < 3) throw err(lineNo, `not a group, node or edge: "${line}"`);
      let label = '';
      if (toks[i] && toks[i].v === ':') {
        if (!toks[i + 1] || !toks[i + 1].q) throw err(lineNo, 'edge label must be quoted: a -> b : "label"');
        label = toks[i + 1].v; i += 2;
      }
      const { o, flags } = readOpts(toks, i, lineNo);
      for (let k = 0; k + 2 < parts.length; k += 2) {
        const a = parts[k], b = parts[k + 2], kind = ARROWS[parts[k + 1]];
        model.edges.push({
          from: a.id, to: b.id, fromSide: a.side, toSide: b.side,
          label: parts.length === 3 ? label : '', start: !!kind.start, end: !!kind.end,
          dashed: !!kind.dashed || flags.includes('dashed'), thick: !!kind.thick || flags.includes('thick'),
          straight: flags.includes('straight'), color: o.color || null, line: lineNo,
        });
      }
      if (label && parts.length > 3) model.edges[model.edges.length - 1].label = label;
    });
    // resolve references
    for (const g of model.groups) {
      if (g.parent) {
        if (!gById[g.parent]) throw err(g.line, `unknown parent group "${g.parent}"`);
        gById[g.parent].kids.push(g);
      }
    }
    for (const g of model.groups) {           // cycle check
      const seen = new Set();
      for (let p = g; p; p = p.parent ? gById[p.parent] : null) {
        if (seen.has(p.id)) throw err(g.line, `group "${g.id}" is nested inside itself`);
        seen.add(p.id);
      }
    }
    for (const n of model.nodes) {
      if (n.parent) {
        if (!gById[n.parent]) throw err(n.line, `unknown group "${n.parent}"`);
        gById[n.parent].nodes.push(n);
      }
    }
    for (const e of model.edges) {
      for (const id of [e.from, e.to]) if (!nById[id]) throw err(e.line, `unknown node "${id}"`);
    }
    const cells = {};
    for (const n of model.nodes) {
      const k = `${n.col},${n.row}`;
      if (cells[k]) throw err(n.line, `"${n.id}" and "${cells[k]}" are both at ${k}`);
      cells[k] = n.id;
    }
    for (const g of model.groups) if (!g.nodes.length && !g.kids.length) throw err(g.line, `group "${g.id}" is empty`);
    model.gById = gById; model.nById = nById;
    return model;
  }

  /* ------------------------------------------------------ text measuring -- */
  // No DOM in Node, so an average-advance table for IBM Plex Sans. Close
  // enough to wrap labels; boxes carry a little slack for the error.
  function textW(s, size, bold) {
    let w = 0;
    for (const ch of s) {
      if ('il.,:;\'|!`'.includes(ch)) w += 0.27;
      else if ('fjrtI()[]{} -/'.includes(ch)) w += 0.36;
      else if ('mwMW@%'.includes(ch)) w += 0.86;
      else if (ch >= 'A' && ch <= 'Z') w += 0.66;
      else if (ch >= '0' && ch <= '9') w += 0.57;
      else if (ch.charCodeAt(0) > 0x2000) w += 0.8;
      else w += 0.54;
    }
    return w * size * (bold ? 1.06 : 1);
  }
  function wrap(s, size, maxW, bold) {
    const out = [];
    for (const para of String(s).split('\n')) {
      let cur = '';
      for (const word of para.split(/\s+/).filter(Boolean)) {
        const t = cur ? cur + ' ' + word : word;
        if (cur && textW(t, size, bold) > maxW) { out.push(cur); cur = word; } else cur = t;
      }
      out.push(cur);
    }
    return out;
  }

  /* -------------------------------------------------------------- layout -- */
  const FONT = 13, SUB = 11.5, LH = 17, SLH = 14.5, TILE = 48, PADX = 16, PADY = 14, HEAD = 28, MARGIN = 16;

  function sizeNode(n, cw) {
    const maxW = n.w || (n.shape === 'card' ? Math.max(cw - 24, 210) : n.shape === 'box' || n.shape === 'pill' || n.shape === 'cyl' ? Math.max(cw - 24, 170) : Math.max(cw - 26, 120));
    if (n.shape === 'tile') {
      n.lines = wrap(n.label, FONT, maxW, true);
      n.subLines = n.sub ? wrap(n.sub, SUB, maxW) : [];
      const tw = Math.max(TILE, ...n.lines.map(l => textW(l, FONT, true)), ...n.subLines.map(l => textW(l, SUB)));
      n.bw = tw + 8;
      n.bh = TILE + 8 + n.lines.length * LH + n.subLines.length * SLH;
    } else if (n.shape === 'circle') {
      n.lines = wrap(n.label, FONT, 90, true);
      n.subLines = n.sub ? wrap(n.sub, SUB, maxW) : [];
      const inner = Math.max(...n.lines.map(l => textW(l, FONT, true)), n.lines.length * LH);
      n.r = Math.max(22, inner / 2 + 10);
      n.bw = n.r * 2; n.bh = n.r * 2;
    } else if (n.shape === 'text') {
      n.lines = wrap(n.label, FONT, maxW);
      n.subLines = n.sub ? wrap(n.sub, SUB, maxW) : [];
      n.bw = Math.max(...n.lines.map(l => textW(l, FONT)), ...n.subLines.map(l => textW(l, SUB))) + 8;
      n.bh = n.lines.length * LH + n.subLines.length * SLH + 6;
    } else {
      if (n.shape === 'diamond') {             // text box must fit inside: tw/W + th/H <= 1
        n.lines = wrap(n.label, FONT, n.w ? n.w / 2 : 118, true);
        n.subLines = n.sub ? wrap(n.sub, SUB, n.w ? n.w / 2 : 118) : [];
        const tw = Math.max(...n.lines.map(l => textW(l, FONT, true)), ...n.subLines.map(l => textW(l, SUB)));
        const th = n.lines.length * LH + n.subLines.length * SLH;
        n.bw = Math.max(n.w || 0, tw * 1.75 + 30, 90); n.bh = Math.max(th * 2 + 14, 56);
        n.iconW = 0;
        return;
      }
      const iconW = n.shape === 'card' && n.icon ? 36 : 0;
      const padX = n.shape === 'pill' ? 20 : 14;
      const inner = maxW - iconW - padX * 2;
      n.lines = wrap(n.label, FONT, Math.max(60, inner), true);
      n.subLines = n.sub ? wrap(n.sub, SUB, Math.max(60, inner)) : [];
      const tw = Math.max(...n.lines.map(l => textW(l, FONT, true)), ...n.subLines.map(l => textW(l, SUB)));
      const th = n.lines.length * LH + n.subLines.length * SLH;
      n.bw = Math.max(n.w || 0, tw + iconW + padX * 2, n.shape === 'card' ? 120 : 64);
      n.bh = Math.max(n.shape === 'card' ? 50 : 38, th + 18);
      if (n.shape === 'cyl') n.bh += 12;
      n.iconW = iconW;
    }
  }

  function layout(model) {
    const { cw, ch, nodes, groups, gById } = model;
    nodes.forEach(n => sizeNode(n, cw));
    // column/row extent of every group, members of child groups included
    const ext = g => {
      if (g.ext) return g.ext;
      let c0 = Infinity, c1 = -Infinity, r0 = Infinity, r1 = -Infinity;
      for (const n of g.nodes) { c0 = Math.min(c0, n.col); c1 = Math.max(c1, n.col); r0 = Math.min(r0, n.row); r1 = Math.max(r1, n.row); }
      for (const k of g.kids) { const e = ext(k); c0 = Math.min(c0, e[0]); c1 = Math.max(c1, e[1]); r0 = Math.min(r0, e[2]); r1 = Math.max(r1, e[3]); }
      return (g.ext = [c0, c1, r0, r1]);
    };
    groups.forEach(ext);
    // every group boundary widens the gutter it sits in, so nested and
    // neighbouring panels never overlap and stay aligned to the grid
    // Distinct column (row) positions are laid out left to right: the gap is
    // the grid pitch, or more if the two neighbours are too big for it, plus
    // one padding step per group edge that falls in between. Sibling groups
    // that open on the same column share a step; only nesting stacks them.
    const chainAt = (k, v) => g => { let d = 0; for (let p = g; p && p.ext[k] === v; p = p.parent ? gById[p.parent] : null) d++; return d; };
    const levels = k => {
      const m = new Map();
      for (const g of groups) { const v = g.ext[k]; m.set(v, Math.max(m.get(v) || 0, chainAt(k, v)(g))); }
      return [...m];
    };
    const axis = (key, pitch, lo, hi, startK, endK, padS, padE, gap) => {
      const vals = [...new Set(nodes.map(n => n[key]))].sort((p, q) => p - q);
      const st = levels(startK), en = levels(endK), pos = new Map();
      const loOf = v => Math.max(...nodes.filter(n => n[key] === v).map(lo)), hiOf = v => Math.max(...nodes.filter(n => n[key] === v).map(hi));
      let at = pitch / 2 + st.reduce((s, [v, d]) => s + (v <= vals[0] ? d * padS : 0), 0);
      vals.forEach((v, i) => {
        if (i) {
          const u = vals[i - 1];
          const extra = st.reduce((s, [w, d]) => s + (w > u && w <= v ? d * padS : 0), 0) + en.reduce((s, [w, d]) => s + (w >= u && w < v ? d * padE : 0), 0);
          at += Math.max(pitch * (v - u), hiOf(u) + loOf(v) + gap) + extra;
        }
        pos.set(v, at);
      });
      return v => pos.get(v);
    };
    const tileTop = n => (n.shape === 'tile' ? TILE / 2 + 4 : n.bh / 2), tileBot = n => (n.shape === 'tile' ? n.bh - TILE / 2 - 4 : n.bh / 2);
    const X = axis('col', cw, n => n.bw / 2, n => n.bw / 2, 0, 1, PADX, PADX, 28);
    const Y = axis('row', ch, tileTop, tileBot, 2, 3, PADY + HEAD, PADY, 36);
    for (const n of nodes) {
      n.cx = Math.round(X(n.col)); n.cy = Math.round(Y(n.row));
      n.bw = Math.round(n.bw / 2) * 2; n.bh = Math.round(n.bh / 2) * 2;
      n.x0 = n.cx - n.bw / 2; n.x1 = n.cx + n.bw / 2;
      if (n.shape === 'tile') { n.y0 = n.cy - (TILE / 2) - 4; n.y1 = n.y0 + n.bh; n.py = n.y0 + 4 + TILE / 2; }
      else { n.y0 = n.cy - n.bh / 2; n.y1 = n.cy + n.bh / 2; n.py = n.cy; }
    }
    // group rectangles, innermost first
    const depth = g => (g.parent ? 1 + depth(gById[g.parent]) : 0);
    const order = groups.slice().sort((a, b) => depth(b) - depth(a));
    for (const g of order) {
      let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      for (const n of g.nodes) { x0 = Math.min(x0, n.x0); x1 = Math.max(x1, n.x1); y0 = Math.min(y0, n.y0); y1 = Math.max(y1, n.y1); }
      for (const k of g.kids) { x0 = Math.min(x0, k.x0); x1 = Math.max(x1, k.x1); y0 = Math.min(y0, k.y0); y1 = Math.max(y1, k.y1); }
      g.x0 = x0 - PADX; g.x1 = x1 + PADX; g.y0 = y0 - PADY - HEAD + 6; g.y1 = y1 + PADY;
      const lw = textW(g.label, 12.5, true) * 1.04 + (g.icon ? 36 : 16);
      if (g.x1 - g.x0 < lw) { const d = (lw - (g.x1 - g.x0)) / 2; g.x0 -= d; g.x1 += d; }
      g.hw = Math.min(lw + 6, g.x1 - g.x0);
    }
  }

  /* ------------------------------------------------------------- routing -- */
  function ports(n) {
    if (n.shape === 'circle') return { T: [n.cx, n.cy - n.r], B: [n.cx, n.cy + n.r], L: [n.cx - n.r, n.cy], R: [n.cx + n.r, n.cy] };
    if (n.shape === 'tile') {
      const half = TILE / 2 + (n.icon && n.icon.logo ? 0 : 0);
      return { T: [n.cx, n.py - half], B: [n.cx, n.y1 + 2], L: [n.cx - half, n.py], R: [n.cx + half, n.py] };
    }
    return { T: [n.cx, n.y0], B: [n.cx, n.y1], L: [n.x0, n.cy], R: [n.x1, n.cy] };
  }
  // tiles are two obstacles, the icon square and the label block under it, so
  // side ports at icon height are usable even when the label is wide
  function nodeRects(n) {
    if (n.shape !== 'tile') return [[n, n.x0, n.y0, n.x1, n.y1]];
    const lw = Math.max(...n.lines.map(l => textW(l, FONT, true)), ...n.subLines.map(l => textW(l, SUB)), 1) + 4;
    return [[n, n.cx - TILE / 2, n.py - TILE / 2, n.cx + TILE / 2, n.py + TILE / 2], [n, n.cx - lw / 2, n.py + TILE / 2, n.cx + lw / 2, n.y1]];
  }
  const NORM = { T: [0, -1], B: [0, 1], L: [-1, 0], R: [1, 0] };
  const STUB = 14;

  function routeAll(model) {
    const { nodes, edges } = model;
    const obst = nodes.flatMap(nodeRects).map(([n, x0, y0, x1, y1]) => ({ n, x0: x0 - 6, y0: y0 - 6, x1: x1 + 6, y1: y1 + 6 }));
    // group titles are obstacles too: lines enter a panel beside its title, not through it
    const soft = model.groups.map(g => ({ x0: g.x0 - 4, y0: g.y0 - 4, x1: g.x0 + g.hw + 4, y1: g.y0 + 26 }));
    const inSoft = (x, y) => soft.some(o => x > o.x0 && x < o.x1 && y > o.y0 && y < o.y1);
    const xsSet = new Set(), ysSet = new Set();
    for (const n of nodes) {
      const p = ports(n);
      xsSet.add(n.cx); ysSet.add(n.py);
      for (const s of 'TBLR') { xsSet.add(p[s][0] + NORM[s][0] * STUB); ysSet.add(p[s][1] + NORM[s][1] * STUB); }
      xsSet.add(n.x0 - 16); xsSet.add(n.x1 + 16); ysSet.add(n.y0 - 16); ysSet.add(n.y1 + 16);
    }
    for (const g of model.groups) { xsSet.add(g.x0 - 12); xsSet.add(g.x1 + 12); xsSet.add(g.x0 + g.hw + 14); ysSet.add(g.y0 - 12); ysSet.add(g.y1 + 12); ysSet.add(g.y0 + 34); }
    const addMids = set => {
      const a = [...set].sort((p, q) => p - q);
      for (let i = 0; i + 1 < a.length; i++) if (a[i + 1] - a[i] > 24) set.add((a[i] + a[i + 1]) / 2);
    };
    // gutter midlines between node columns/rows are the preferred lanes
    const colC = [...new Set(nodes.map(n => n.cx))].sort((a, b) => a - b);
    const rowC = [...new Set(nodes.map(n => n.cy))].sort((a, b) => a - b);
    const gutX = [], gutY = [];
    for (let i = 0; i + 1 < colC.length; i++) {
      const l = Math.max(...nodes.filter(n => n.cx === colC[i]).map(n => n.x1)), r = Math.min(...nodes.filter(n => n.cx === colC[i + 1]).map(n => n.x0));
      if (r > l) { xsSet.add((l + r) / 2); gutX.push((l + r) / 2); }
    }
    for (let i = 0; i + 1 < rowC.length; i++) {
      const t = Math.max(...nodes.filter(n => n.cy === rowC[i]).map(n => n.y1)), b = Math.min(...nodes.filter(n => n.cy === rowC[i + 1]).map(n => n.y0));
      if (b > t) { ysSet.add((t + b) / 2); gutY.push((t + b) / 2); }
    }
    addMids(xsSet); addMids(ysSet);
    const xs = [...xsSet].sort((a, b) => a - b).map(v => Math.round(v * 2) / 2);
    const ys = [...ysSet].sort((a, b) => a - b).map(v => Math.round(v * 2) / 2);
    const X = xs.length, Y = ys.length;
    const inside = (x, y, skip) => obst.some(o => !skip.has(o.n) && x > o.x0 && x < o.x1 && y > o.y0 && y < o.y1);
    const segUse = new Map();     // "i,j,h|v" → [edgeIdx...]
    const ptUse = new Map();      // "i,j" → {h, v}
    const xi = v => xs.indexOf(Math.round(v * 2) / 2), yi = v => ys.indexOf(Math.round(v * 2) / 2);
    const portUse = new Map();    // "node:side" → Set of 'in' / 'out'
    const portCost = (id, side, role) => { const u = portUse.get(`${id}:${side}`); return u && [...u].some(r => r !== role) ? 70 : 0; };

    edges.forEach((e, ei) => {
      const a = model.nById[e.from], b = model.nById[e.to];
      if (model.route === 'straight' || e.straight || a === b) { e.pts = straightPts(a, b); return; }
      const pa = ports(a), pb = ports(b);
      const dx = b.cx - a.cx, dy = b.py - a.py;
      const pref = (n, s, sx, sy) => {       // side preference: facing sides are cheapest
        const [nx, ny] = NORM[s];
        const dot = nx * Math.sign(sx) + ny * Math.sign(sy);
        let c = dot > 0 ? 0 : dot === 0 ? 40 : 110;
        if (n.shape === 'tile' && s === 'B' && n.lines.length + n.subLines.length > 2) c += 20;
        return c;
      };
      const sSides = e.fromSide ? [e.fromSide] : ['T', 'B', 'L', 'R'];
      const tSides = e.toSide ? [e.toSide] : ['T', 'B', 'L', 'R'];
      const skip = new Set();
      const starts = [], goals = new Map();
      for (const s of sSides) {
        const [px, py] = pa[s], sx = px + NORM[s][0] * STUB, sy = py + NORM[s][1] * STUB;
        const i = xi(sx), j = yi(sy);
        if (i < 0 || j < 0 || inside(sx, sy, skip)) continue;
        starts.push({ i, j, dir: dirOf(NORM[s]), cost: pref(a, s, dx, dy) + portCost(a.id, s, 'out'), side: s, port: [px, py] });
      }
      for (const s of tSides) {
        const [px, py] = pb[s], sx = px + NORM[s][0] * STUB, sy = py + NORM[s][1] * STUB;
        const i = xi(sx), j = yi(sy);
        if (i < 0 || j < 0 || inside(sx, sy, skip)) continue;
        goals.set(i * Y + j, { side: s, port: [px, py], inDir: dirOf([-NORM[s][0], -NORM[s][1]]), cost: pref(b, s, -dx, -dy) + portCost(b.id, s, 'in') });
      }
      const path = starts.length && goals.size ? astar(starts, goals) : null;
      if (!path) { e.pts = elbowPts(a, b); return; }
      const pts = [path.start.port, ...path.cells.map(([i, j]) => [xs[i], ys[j]]), path.goal.port];
      e.pts = simplify(pts);
      e.fromPort = path.start.side; e.toPort = path.goal.side;
      const mark = (id, side, role) => { const k = `${id}:${side}`; if (!portUse.has(k)) portUse.set(k, new Set()); portUse.get(k).add(role); };
      mark(a.id, e.fromPort, e.start ? 'both' : 'out'); mark(b.id, e.toPort, e.end && !e.start ? 'in' : 'both');
      // record usage for later edges
      for (let k = 0; k + 1 < path.cells.length; k++) {
        const [i1, j1] = path.cells[k], [i2, j2] = path.cells[k + 1];
        const h = j1 === j2, key = h ? `${Math.min(i1, i2)},${j1},h` : `${i1},${Math.min(j1, j2)},v`;
        if (!segUse.has(key)) segUse.set(key, []);
        segUse.get(key).push(ei);
        for (const [pi, pj] of [[i1, j1], [i2, j2]]) {
          const pk = `${pi},${pj}`, u = ptUse.get(pk) || { h: 0, v: 0 };
          u[h ? 'h' : 'v']++; ptUse.set(pk, u);
        }
      }

      function astar(starts, goals) {
        const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
        const BEND = 26, OVERLAP = 60, CROSS = 18, GUTTER_BONUS = 0.85;
        const gx = new Set(gutX.map(xi)), gy = new Set(gutY.map(yi));
        const best = new Map(), prev = new Map(), heap = [];
        const hFn = (i, j) => { let m = Infinity; for (const k of goals.keys()) { const gi = Math.floor(k / Y), gj = k % Y; m = Math.min(m, Math.abs(xs[i] - xs[gi]) + Math.abs(ys[j] - ys[gj])); } return m; };
        const push = (c, st) => { heap.push([c, st]); let q = heap.length - 1; while (q > 0) { const p = (q - 1) >> 1; if (heap[p][0] <= heap[q][0]) break; [heap[p], heap[q]] = [heap[q], heap[p]]; q = p; } };
        const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let q = 0; for (;;) { const l = q * 2 + 1, r = l + 1; let m = q; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === q) break; [heap[m], heap[q]] = [heap[q], heap[m]]; q = m; } } return top; };
        for (const s of starts) {
          const st = (s.i * Y + s.j) * 4 + s.dir;
          if (!best.has(st) || best.get(st) > s.cost) { best.set(st, s.cost); prev.set(st, { start: s }); push(s.cost + hFn(s.i, s.j), st); }
        }
        let done = null, doneCost = Infinity;
        let guard = 0;
        while (heap.length && guard++ < 400000) {
          const [f, st] = pop();
          const g = best.get(st);
          if (f - hFn(Math.floor(st / 4 / Y), Math.floor(st / 4) % Y) > g + 1e-6) continue;
          if (f >= doneCost) break;
          const cell = Math.floor(st / 4), dir = st % 4, i = Math.floor(cell / Y), j = cell % Y;
          const goal = goals.get(cell);
          if (goal) {
            const c = g + goal.cost + (dir === goal.inDir ? 0 : BEND);
            if (c < doneCost) { doneCost = c; done = { st, goal }; }
          }
          DIRS.forEach(([di, dj], nd) => {
            if ((nd ^ 1) === dir) return;                 // no U-turns
            const ni = i + di, nj = j + dj;
            if (ni < 0 || nj < 0 || ni >= X || nj >= Y) return;
            const mx = (xs[i] + xs[ni]) / 2, my = (ys[j] + ys[nj]) / 2;
            if (inside(mx, my, skip) || inside(xs[ni], ys[nj], skip)) return;
            const h = dj === 0;
            let c = Math.abs(xs[ni] - xs[i]) + Math.abs(ys[nj] - ys[j]);
            if ((h && gy.has(j)) || (!h && gx.has(i))) c *= GUTTER_BONUS;
            if (inSoft(mx, my)) c += h ? 400 : 45;      // under a group title: fine to dip under, never to run along
            if (nd !== dir) c += BEND;
            const key = h ? `${Math.min(i, ni)},${j},h` : `${i},${Math.min(j, nj)},v`;
            const used = segUse.get(key);
            if (used && used.some(o => !sharesEnd(edges[o], e))) c += OVERLAP;
            const pu = ptUse.get(`${ni},${nj}`);
            if (pu && (h ? pu.v : pu.h)) c += CROSS;
            const nst = (ni * Y + nj) * 4 + nd, ng = g + c;
            if (!best.has(nst) || best.get(nst) > ng) { best.set(nst, ng); prev.set(nst, { st }); push(ng + hFn(ni, nj), nst); }
          });
        }
        if (!done) return null;
        const cells = [];
        let st = done.st, start = null;
        for (;;) {
          const cell = Math.floor(st / 4);
          cells.push([Math.floor(cell / Y), cell % Y]);
          const p = prev.get(st);
          if (p.start) { start = p.start; break; }
          st = p.st;
        }
        cells.reverse();
        return { cells, start, goal: done.goal };
      }
    });
  }
  const dirOf = ([x, y]) => (x === 1 ? 0 : x === -1 ? 1 : y === 1 ? 2 : 3);
  const sharesEnd = (p, q) => (p.from === q.from && !p.start && !q.start) || (p.to === q.to && !p.end === !q.end);
  function simplify(pts) {
    const out = [pts[0]];
    for (let k = 1; k < pts.length; k++) {
      const p = pts[k], q = out[out.length - 1];
      if (Math.abs(p[0] - q[0]) < 0.01 && Math.abs(p[1] - q[1]) < 0.01) continue;
      if (out.length >= 2) {
        const r = out[out.length - 2];
        if ((Math.abs(r[0] - q[0]) < 0.01 && Math.abs(q[0] - p[0]) < 0.01) || (Math.abs(r[1] - q[1]) < 0.01 && Math.abs(q[1] - p[1]) < 0.01)) { out[out.length - 1] = p; continue; }
      }
      out.push(p);
    }
    return out;
  }
  function clipTo(n, x, y) {             // point on n's outline towards (x,y)
    const dx = x - n.cx, dy = y - n.py;
    if (!dx && !dy) return [n.cx, n.py];
    if (n.shape === 'circle') { const d = Math.hypot(dx, dy); return [n.cx + dx / d * n.r, n.py + dy / d * n.r]; }
    const hw = n.shape === 'tile' ? TILE / 2 : n.bw / 2, hh = n.shape === 'tile' ? TILE / 2 : n.bh / 2;
    const s = Math.min(hw / Math.abs(dx || 1e-9), hh / Math.abs(dy || 1e-9));
    return [n.cx + dx * s, n.py + dy * s];
  }
  function straightPts(a, b) { return [clipTo(a, b.cx, b.py), clipTo(b, a.cx, a.py)]; }
  function elbowPts(a, b) {
    const pa = ports(a), pb = ports(b);
    if (Math.abs(b.cx - a.cx) < 1) return b.py > a.py ? [pa.B, pb.T] : [pa.T, pb.B];
    if (Math.abs(b.py - a.py) < 1) return b.cx > a.cx ? [pa.R, pb.L] : [pa.L, pb.R];
    const s = b.py > a.py ? pa.B : pa.T, t = b.cx > a.cx ? pb.L : pb.R;
    return [s, [s[0], t[1]], t];
  }

  /* ------------------------------------------------------------ drawing -- */
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const f1 = v => Math.round(v * 10) / 10;

  function glyphSvg(icons, glyph, x, y, size, fill) {
    const g = icons && icons[glyph];
    if (!g) return `<rect x="${f1(x + size * .2)}" y="${f1(y + size * .2)}" width="${f1(size * .6)}" height="${f1(size * .6)}" rx="4" fill="none" stroke="${fill || '#fff'}" stroke-width="2"/>`;
    // a transformed <g>, not a nested <svg>: page CSS such as `svg { width: 18px }`
    // would otherwise resize every glyph
    const w = g.w || 24, h = g.h || 24, k = size / Math.max(w, h);
    const body = fill ? g.b.replace(/currentColor/g, fill) : g.b;
    return `<g transform="translate(${f1(x + (size - w * k) / 2)} ${f1(y + (size - h * k) / 2)}) scale(${+k.toFixed(4)})">${body}</g>`;
  }

  function roundedPath(pts, r) {
    if (pts.length < 3) return `M${pts.map(p => `${f1(p[0])} ${f1(p[1])}`).join(' L')}`;
    let d = `M${f1(pts[0][0])} ${f1(pts[0][1])}`;
    for (let k = 1; k < pts.length - 1; k++) {
      const [px, py] = pts[k - 1], [cx, cy] = pts[k], [nx, ny] = pts[k + 1];
      const l1 = Math.hypot(cx - px, cy - py), l2 = Math.hypot(nx - cx, ny - cy);
      const rr = Math.min(r, l1 / 2, l2 / 2);
      const ax = cx - (cx - px) / (l1 || 1) * rr, ay = cy - (cy - py) / (l1 || 1) * rr;
      const bx = cx + (nx - cx) / (l2 || 1) * rr, by = cy + (ny - cy) / (l2 || 1) * rr;
      d += ` L${f1(ax)} ${f1(ay)} Q${f1(cx)} ${f1(cy)} ${f1(bx)} ${f1(by)}`;
    }
    const last = pts[pts.length - 1];
    return d + ` L${f1(last[0])} ${f1(last[1])}`;
  }

  function hexA(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`;
  }

  function render(src, opts = {}) {
    const dark = !!opts.dark, icons = opts.icons || {}, P = opts.idPrefix || ('ad' + Math.random().toString(36).slice(2, 8));
    const model = parse(src);
    layout(model);
    routeAll(model);
    const col = name => COLORS[name][dark ? 1 : 0];
    const edgeC = 'var(--ad-edge)';
    const parts = [], defs = [], labels = [], titles = [];
    const usedGrad = new Set();
    const grad = cat => {
      const id = `${P}-g-${cat}`;
      if (!usedGrad.has(cat)) {
        usedGrad.add(cat);
        defs.push(`<linearGradient id="${id}" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="${CAT[cat][1]}"/><stop offset="1" stop-color="${CAT[cat][0]}"/></linearGradient>`);
      }
      return `url(#${id})`;
    };

    // bounds
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    const grow = (a, b, c, d) => { x0 = Math.min(x0, a); y0 = Math.min(y0, b); x1 = Math.max(x1, c); y1 = Math.max(y1, d); };
    model.nodes.forEach(n => grow(n.x0, n.y0, n.x1, n.y1));
    model.groups.forEach(g => grow(g.x0, g.y0, g.x1, g.y1));
    model.edges.forEach(e => e.pts.forEach(([x, y]) => grow(x, y, x, y)));

    // groups, outermost first so inner panels paint on top
    const depth = g => (g.parent ? 1 + depth(model.gById[g.parent]) : 0);
    const chain = g => (g.parent ? [...chain(model.gById[g.parent]), g] : [g]);   // root → g, for layered tints
    model.groups.slice().sort((a, b) => depth(a) - depth(b)).forEach(g => {
      const c = col(g.color), d = depth(g);
      const dashed = g.style ? g.style === 'dashed' : d === 0;
      parts.push(`<g class="ad-group">`
        + `<rect x="${f1(g.x0)}" y="${f1(g.y0)}" width="${f1(g.x1 - g.x0)}" height="${f1(g.y1 - g.y0)}" rx="10" fill="${hexA(c, dark ? .09 : .055)}" stroke="${hexA(c, dark ? .75 : .65)}" stroke-width="1.4"${dashed ? ' stroke-dasharray="6 4"' : ''}/>`);
      parts.push('</g>');
      // the title tab is drawn after the edges, opaque, so a line that has
      // to enter the panel under it tucks behind the tab instead of through the text
      let t = `<g class="ad-gtitle"><rect x="${f1(g.x0 + 1)}" y="${f1(g.y0 + 1)}" width="${f1(g.hw - 2)}" height="23" rx="6" fill="var(--ad-bg)"/>`
        + chain(g).map(a => `<rect x="${f1(g.x0 + 1)}" y="${f1(g.y0 + 1)}" width="${f1(g.hw - 2)}" height="23" rx="6" fill="${hexA(col(a.color), dark ? .09 : .055)}"/>`).join('');
      let tx = g.x0 + 12;
      if (g.icon) {
        const ic = resolveIcon(g.icon);
        if (ic.logo) t += glyphSvg(icons, ic.glyph, g.x0, g.y0, 24);
        else t += `<rect x="${f1(g.x0)}" y="${f1(g.y0)}" width="24" height="24" rx="4" fill="${c}"/>` + glyphSvg(icons, ic.glyph, g.x0 + 4, g.y0 + 4, 16, '#fff');
        tx = g.x0 + 32;
      }
      titles.push(t + `<text x="${f1(tx)}" y="${f1(g.y0 + 16.5)}" class="ad-gl" fill="${c}">${esc(g.label)}</text></g>`);
    });

    // edges under nodes
    const markers = new Set();
    const marker = (color, thick) => {
      const id = `${P}-m-${markers.size}`;
      for (const m of markers) if (m.color === color && m.thick === thick) return m.id;
      markers.add({ id, color, thick });
      const s = thick ? 1.2 : 1;
      defs.push(`<marker id="${id}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="${f1(7 * s)}" markerHeight="${f1(7 * s)}" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="${color}"/></marker>`);
      return id;
    };
    model.edges.forEach(e => {
      const c = e.color ? col(e.color) : edgeC;
      const mk = marker(e.color ? c : 'var(--ad-edge)', e.thick);
      const w = e.thick ? 2.6 : 1.6;
      const d = model.route === 'straight' || e.straight ? `M${e.pts.map(p => `${f1(p[0])} ${f1(p[1])}`).join(' L')}` : roundedPath(e.pts, 7);
      parts.push(`<path d="${d}" fill="none" stroke="${c}" stroke-width="${w}"${e.dashed ? ' stroke-dasharray="5 4"' : ''} stroke-linejoin="round"`
        + `${e.end ? ` marker-end="url(#${mk})"` : ''}${e.start ? ` marker-start="url(#${mk})"` : ''}/>`);
      if (e.label) labels.push(e);
    });

    parts.push(...titles);

    // nodes
    model.nodes.forEach(n => {
      const c = col(n.color);
      const txt = (lines, subLines, cx, top, anchor = 'middle') => {
        let s = '', y = top;
        lines.forEach(l => { y += LH; s += `<text x="${f1(cx)}" y="${f1(y - 4.5)}" class="ad-nl" text-anchor="${anchor}">${esc(l)}</text>`; });
        subLines.forEach(l => { y += SLH; s += `<text x="${f1(cx)}" y="${f1(y - 3.5)}" class="ad-ns" text-anchor="${anchor}">${esc(l)}</text>`; });
        return s;
      };
      let s = `<g class="ad-node" data-id="${esc(n.id)}">`;
      if (n.shape === 'tile') {
        const ix = n.cx - TILE / 2, iy = n.py - TILE / 2;
        if (n.icon.logo && /^logos:aws-/.test(n.icon.glyph)) s += glyphSvg(icons, n.icon.glyph, ix, iy, TILE);
        else if (n.icon.logo) s += `<rect x="${f1(ix)}" y="${f1(iy)}" width="${TILE}" height="${TILE}" rx="9" fill="#ffffff" stroke="var(--ad-border)"/>` + glyphSvg(icons, n.icon.glyph, ix + 8, iy + 8, TILE - 16);
        else {
          const cat = n.icon.cat;
          s += `<rect x="${f1(ix)}" y="${f1(iy)}" width="${TILE}" height="${TILE}" rx="9" fill="${grad(cat)}"/>` + glyphSvg(icons, n.icon.glyph, ix + 10, iy + 10, TILE - 20, '#fff');
        }
        s += txt(n.lines, n.subLines, n.cx, n.py + TILE / 2 + 4);
      } else if (n.shape === 'circle') {
        s += `<circle cx="${f1(n.cx)}" cy="${f1(n.cy)}" r="${f1(n.r)}" fill="${hexA(c, dark ? .2 : .12)}" stroke="${c}" stroke-width="1.6"/>`;
        s += txt(n.lines, [], n.cx, n.cy - n.lines.length * LH / 2 + 1);
        if (n.subLines.length) s += txt([], n.subLines, n.cx, n.cy + n.r + 1);
      } else if (n.shape === 'text') {
        s += txt(n.lines, n.subLines, n.cx, n.y0 + 3).replace(/class="ad-nl"/g, 'class="ad-nt"');
      } else {
        const x = n.x0, y = n.y0, w = n.bw, h = n.bh;
        const fill = n.shape === 'card' ? 'var(--ad-card)' : hexA(c, dark ? .16 : .09);
        const stroke = n.shape === 'card' ? 'var(--ad-border)' : hexA(c, dark ? .85 : .7);
        if (n.shape === 'diamond') {
          s += `<path d="M${f1(n.cx)} ${f1(y)} L${f1(x + w)} ${f1(n.cy)} L${f1(n.cx)} ${f1(y + h)} L${f1(x)} ${f1(n.cy)} Z" fill="${fill}" stroke="${stroke}" stroke-width="1.5" stroke-linejoin="round"/>`;
        } else if (n.shape === 'cyl') {
          const ry = 7;
          s += `<path d="M${f1(x)} ${f1(y + ry)} A${f1(w / 2)} ${ry} 0 0 1 ${f1(x + w)} ${f1(y + ry)} V${f1(y + h - ry)} A${f1(w / 2)} ${ry} 0 0 1 ${f1(x)} ${f1(y + h - ry)} Z" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>`
            + `<path d="M${f1(x)} ${f1(y + ry)} A${f1(w / 2)} ${ry} 0 0 0 ${f1(x + w)} ${f1(y + ry)}" fill="none" stroke="${stroke}" stroke-width="1.5"/>`;
        } else {
          const rx = n.shape === 'pill' ? h / 2 : 9;
          s += `<rect x="${f1(x)}" y="${f1(y)}" width="${f1(w)}" height="${f1(h)}" rx="${f1(rx)}" fill="${fill}" stroke="${stroke}" stroke-width="1.4"/>`;
          if (n.shape === 'card') s += `<rect x="${f1(x)}" y="${f1(y + 8)}" width="3" height="${f1(h - 16)}" rx="1.5" fill="${c}"/>`;
        }
        const th = n.lines.length * LH + n.subLines.length * SLH;
        const top = n.cy - th / 2 + (n.shape === 'cyl' ? 5 : 0);
        if (n.shape === 'card' && n.icon) {
          const ix = x + 12, iy = n.cy - 14;
          if (n.icon.logo) s += glyphSvg(icons, n.icon.glyph, ix, iy, 28);
          else s += `<rect x="${f1(ix)}" y="${f1(iy)}" width="28" height="28" rx="6" fill="${grad(n.icon.cat)}"/>` + glyphSvg(icons, n.icon.glyph, ix + 5, iy + 5, 18, '#fff');
          s += txt(n.lines, n.subLines, x + 48, top, 'start');
        } else {
          s += txt(n.lines, n.subLines, n.cx, top);
        }
      }
      parts.push(s + '</g>');
    });

    // edge labels last so they sit over lines
    const boxes = model.nodes.flatMap(nodeRects).map(r => r.slice(1));
    const placed = [];
    labels.forEach(e => {
      const lines = wrap(e.label, 11.5, 150);
      const w = Math.max(...lines.map(l => textW(l, 11.5))) + 10, h = lines.length * 14 + 4;
      const segs = [];
      for (let k = 0; k + 1 < e.pts.length; k++) {
        const [ax, ay] = e.pts[k], [bx, by] = e.pts[k + 1];
        segs.push({ len: Math.hypot(bx - ax, by - ay), mx: (ax + bx) / 2, my: (ay + by) / 2 });
      }
      segs.sort((p, q) => q.len - p.len);
      const others = [];
      model.edges.forEach(o => { if (o !== e) for (let k = 0; k + 1 < o.pts.length; k++) others.push([o.pts[k], o.pts[k + 1]]); });
      const hitsLine = (cx, cy) => others.some(([p, q]) => segHitsBox(p, q, [cx - w / 2 - 2, cy - h / 2 - 2, cx + w / 2 + 2, cy + h / 2 + 2]));
      const hit = (cx, cy, strict) => [...boxes, ...placed].some(([a, b, c2, d]) => cx + w / 2 > a && cx - w / 2 < c2 && cy + h / 2 > b && cy - h / 2 < d) || (strict && hitsLine(cx, cy));
      let spot = null;
      for (const strict of [true, false]) for (const sg of segs) {
        if (spot) break;
        for (const t of [0, -0.25, 0.25, -0.38, 0.38]) {
          const k = e.pts.findIndex((p, i) => i + 1 < e.pts.length && Math.abs((p[0] + e.pts[i + 1][0]) / 2 - sg.mx) < .01 && Math.abs((p[1] + e.pts[i + 1][1]) / 2 - sg.my) < .01);
          const [ax, ay] = e.pts[k], [bx, by] = e.pts[k + 1];
          const cx = sg.mx + (bx - ax) * t, cy = sg.my + (by - ay) * t;
          if (sg.len < w + 16 && t) continue;
          if (!hit(cx, cy, strict)) { spot = [cx, cy]; break; }
        }
      }
      if (!spot) spot = [segs[0].mx, segs[0].my];
      placed.push([spot[0] - w / 2, spot[1] - h / 2, spot[0] + w / 2, spot[1] + h / 2]);
      grow(spot[0] - w / 2, spot[1] - h / 2, spot[0] + w / 2, spot[1] + h / 2);
      let s = `<g class="ad-elabel"><rect x="${f1(spot[0] - w / 2)}" y="${f1(spot[1] - h / 2)}" width="${f1(w)}" height="${f1(h)}" rx="4" fill="var(--ad-bg)" fill-opacity=".94"/>`;
      lines.forEach((l, i) => { s += `<text x="${f1(spot[0])}" y="${f1(spot[1] - h / 2 + 13 + i * 14)}" class="ad-el" text-anchor="middle">${esc(l)}</text>`; });
      parts.push(s + '</g>');
    });

    const vx = x0 - MARGIN, vy = y0 - MARGIN, vw = x1 - x0 + MARGIN * 2, vh = y1 - y0 + MARGIN * 2;
    const style = `<style>
.${P}{--ad-text:var(--text,${dark ? '#e9edf5' : '#0f141c'});--ad-dim:var(--text-dim,${dark ? '#9ba6b9' : '#4c5566'});--ad-edge:var(--text-faint,${dark ? '#7a8497' : '#6b7486'});--ad-bg:var(--surface,${dark ? '#11151d' : '#ffffff'});--ad-card:var(--surface-2,${dark ? '#171c26' : '#f6f8fb'});--ad-border:var(--border-strong,${dark ? '#36415a' : '#c3ccda'})}
.${P}{fill:#000;stroke:none;stroke-width:1;stroke-linecap:butt;stroke-linejoin:miter;overflow:visible}
.${P} text{font-family:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',sans-serif}
.${P} .ad-nl{font-size:${FONT}px;font-weight:500;fill:var(--ad-text)}
.${P} .ad-nt{font-size:${FONT}px;font-weight:400;font-style:italic;fill:var(--ad-dim)}
.${P} .ad-ns{font-size:${SUB}px;fill:var(--ad-dim)}
.${P} .ad-gl{font-size:12.5px;font-weight:700;letter-spacing:.02em}
.${P} .ad-el{font-size:11.5px;fill:var(--ad-dim)}
</style>`;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" class="archd ${P}" viewBox="${f1(vx)} ${f1(vy)} ${f1(vw)} ${f1(vh)}" width="${f1(vw)}" height="${f1(vh)}" role="img"${model.caption ? ` aria-label="${esc(model.caption)}"` : ''}>${style}<defs>${defs.join('')}</defs>${parts.join('')}</svg>`;
    return { svg, width: vw, height: vh, caption: model.caption, model };
  }

  /* ------------------------------------------------------ quality report -- */
  // Used by the repo validator: counts what makes a diagram read as a
  // spider web, so a conversion can be checked without eyeballing it.
  function lint(src) {
    const { model } = render(src, { idPrefix: 'lint' });
    const segs = [];
    model.edges.forEach((e, ei) => { for (let k = 0; k + 1 < e.pts.length; k++) segs.push({ ei, a: e.pts[k], b: e.pts[k + 1] }); });
    let crossings = 0;
    for (let i = 0; i < segs.length; i++) for (let j = i + 1; j < segs.length; j++) {
      const s = segs[i], t = segs[j];
      if (s.ei === t.ei) continue;
      const e1 = model.edges[s.ei], e2 = model.edges[t.ei];
      if (e1.from === e2.from || e1.to === e2.to || e1.from === e2.to || e1.to === e2.from) continue;
      if (segCross(s.a, s.b, t.a, t.b)) crossings++;
    }
    const bends = model.edges.reduce((s, e) => s + Math.max(0, e.pts.length - 2), 0);
    const through = [];
    model.edges.forEach(e => {
      const hitIds = new Set();
      for (let k = 0; k + 1 < e.pts.length; k++) for (const [n, a, b, c, d] of model.nodes.flatMap(nodeRects)) {
        if (n.id === e.from || n.id === e.to || hitIds.has(n.id)) continue;
        if (segHitsBox(e.pts[k], e.pts[k + 1], [a + 2, b + 2, c - 2, d - 2])) { hitIds.add(n.id); through.push(`${e.from}->${e.to} passes through ${n.id}`); }
      }
    });
    let titleHits = 0;
    model.edges.forEach(e => {
      for (const g of model.groups) for (let k = 0; k + 1 < e.pts.length; k++) {
        if (segHitsBox(e.pts[k], e.pts[k + 1], [g.x0 + 2, g.y0 + 2, g.x0 + g.hw - 2, g.y0 + 22])) { titleHits++; break; }
      }
    });
    const R = model.nodes.flatMap(nodeRects);
    for (let i = 0; i < R.length; i++) for (let j = i + 1; j < R.length; j++) {
      const [n1, a1, b1, c1, d1] = R[i], [n2, a2, b2, c2, d2] = R[j];
      if (n1 === n2) continue;
      if (a1 < c2 - 1 && a2 < c1 - 1 && b1 < d2 - 1 && b2 < d1 - 1) through.push(`${n1.id} overlaps ${n2.id}: widen the grid (grid WxH), move one, or shorten a label`);
    }
    for (const g of model.groups) for (const n of model.nodes) {
      let inG = false;
      for (let p = n.parent && model.gById[n.parent]; p; p = p.parent ? model.gById[p.parent] : null) if (p === g) inG = true;
      if (!inG && n.x0 < g.x1 && n.x1 > g.x0 && n.y0 < g.y1 && n.y1 > g.y0) through.push(`${n.id} sits inside group ${g.id} but is not a member: add "in ${g.id}" or move it`);
    }
    const G = model.groups;
    for (let i = 0; i < G.length; i++) for (let j = i + 1; j < G.length; j++) {
      const g = G[i], h = G[j];
      const anc = (x, y) => { for (let p = x.parent && model.gById[x.parent]; p; p = p.parent ? model.gById[p.parent] : null) if (p === y) return true; return false; };
      if (anc(g, h) || anc(h, g)) continue;
      if (g.x0 < h.x1 && g.x1 > h.x0 && g.y0 < h.y1 && g.y1 > h.y0) through.push(`groups ${g.id} and ${h.id} overlap: their cells interleave`);
    }
    const { width, height } = render(src, { idPrefix: 'lint2' });
    return { nodes: model.nodes.length, edges: model.edges.length, crossings, bends, titleHits, through, width: Math.round(width), height: Math.round(height) };
  }
  function segCross(p1, p2, p3, p4) {
    const d = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
    const d1 = d(p3, p4, p1), d2 = d(p3, p4, p2), d3 = d(p1, p2, p3), d4 = d(p1, p2, p4);
    return ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0));
  }
  function segHitsBox(a, b, [x0, y0, x1, y1]) {
    for (let t = 0; t <= 1; t += 0.05) {
      const x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t;
      if (x > x0 && x < x1 && y > y0 && y < y1) return true;
    }
    return false;
  }

  const api = { parse, render, lint, ICONS, LOGOS, COLORS, CAT, resolveIcon };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.ArchDiagram = api;
})(typeof window !== 'undefined' ? window : globalThis);
