'use strict';

if (typeof defineLab !== 'undefined') {

  const addVizStyles = () => {
    if (document.getElementById('viz-api-styles')) return;
    const style = document.createElement('style');
    style.id = 'viz-api-styles';
    style.innerHTML = `
      .api-viz-container {
        position: relative;
        width: 100%;
        height: 200px;
        background: var(--surface-2, #171c26);
        border: 1px solid var(--border, #242c3a);
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-family: var(--sans, sans-serif);
        color: var(--text, #d0d4dc);
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.2);
        margin: 20px 0;
      }
      .api-node {
        width: 90px;
        height: 70px;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 13px;
        z-index: 10;
        position: absolute;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
      }
      .api-node span { font-size: 10px; font-weight: normal; opacity: 0.7; margin-top: 4px; }
      .api-node-client { background: linear-gradient(135deg, rgba(52, 152, 219, 0.9), rgba(41, 128, 185, 1)); left: 30px; }
      .api-node-server { background: linear-gradient(135deg, rgba(46, 204, 113, 0.9), rgba(39, 174, 96, 1)); right: 30px; }
      .api-node-stripe { background: linear-gradient(135deg, rgba(103, 114, 229, 0.9), rgba(84, 105, 212, 1)); left: 30px; }
      
      .api-packet {
        position: absolute;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: var(--mono, monospace);
        font-size: 11px;
        color: #fff;
        padding: 6px 12px;
        transition: left 0.8s cubic-bezier(0.4, 0, 0.2, 1), background 0.3s, opacity 0.2s;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        white-space: nowrap;
        z-index: 5;
        top: 85px;
      }
      .api-label { font-family: var(--mono, monospace); font-size: 12px; color: var(--text-dim, #848c9a); position: absolute; bottom: 15px; }
      
      .gql-beam { position: absolute; height: 4px; background: #e10098; box-shadow: 0 0 10px #e10098; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); left: 120px; top: 98px; border-radius: 2px; z-index: 4; }
      
      .grpc-stream-container { position: absolute; left: 130px; right: 130px; top: 70px; height: 60px; display: flex; flex-direction: column; justify-content: space-around; }
      .grpc-stream { width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; position: relative; overflow: hidden; }
      .grpc-chunk { position: absolute; height: 100%; border-radius: 3px; transition: left 1s linear; }
      
      .ws-line { position: absolute; top: 98px; left: 120px; right: 120px; height: 2px; background: rgba(255,255,255,0.2); z-index: 4; }
      .ws-particle { position: absolute; width: 12px; height: 12px; border-radius: 50%; top: -5px; transition: left 0.8s linear, right 0.8s linear; box-shadow: 0 0 12px currentColor; }
      
      .soap-env { border: 2px solid #f39c12; background: rgba(243, 156, 18, 0.15); color: #f39c12; font-weight: bold; }
    `;
    document.head.appendChild(style);
  };
  addVizStyles();

  // 1. REST API
  defineLab('api-rest', (host) => {
    host.innerHTML = `
      <div class="api-viz-container">
        <div class="api-node api-node-client">Client<span>Mobile App</span></div>
        <div id="rest-packet" class="api-packet" style="background:#e74c3c; left:120px; opacity:0;">GET /users</div>
        <div class="api-node api-node-server">Server<span>REST API</span></div>
        <div class="api-label" id="rest-log">Idle</div>
      </div>
    `;
    const pkt = host.querySelector('#rest-packet');
    const log = host.querySelector('#rest-log');
    let state = 0;
    
    setInterval(() => {
      if (state === 0) {
        pkt.style.opacity = '1';
        pkt.style.left = '130px';
        pkt.style.background = '#e74c3c';
        pkt.innerText = "GET /users/1";
        log.innerText = "Client initiates stateless HTTP Request";
        state = 1;
      } else if (state === 1) {
        pkt.style.left = 'calc(100% - 210px)'; // Move to server
        state = 2;
      } else if (state === 2) {
        pkt.style.background = '#2ecc71';
        pkt.innerText = '200 OK {"name":"Alice"}';
        log.innerText = "Server processes and returns JSON Resource";
        state = 3;
      } else if (state === 3) {
        pkt.style.left = '130px'; // Move to client
        state = 4;
      } else {
        pkt.style.opacity = '0';
        log.innerText = "Connection closed (Stateless)";
        state = 0;
      }
    }, 1000);
  });

  // 2. GraphQL
  defineLab('api-graphql', (host) => {
    host.innerHTML = `
      <div class="api-viz-container">
        <div class="api-node api-node-client" style="background: linear-gradient(135deg, #e10098, #9b59b6);">Client<span>React</span></div>
        <div class="gql-beam" id="gql-beam"></div>
        <div id="gql-packet" class="api-packet" style="background:#e10098; left:130px; opacity:0; top:60px;">{ user { name } }</div>
        <div class="api-node api-node-server">Server<span>/graphql</span></div>
        <div class="api-label" id="gql-log">Idle</div>
      </div>
    `;
    const pkt = host.querySelector('#gql-packet');
    const beam = host.querySelector('#gql-beam');
    const log = host.querySelector('#gql-log');
    let state = 0;
    
    setInterval(() => {
      if (state === 0) {
        pkt.style.opacity = '1';
        pkt.style.left = '130px';
        pkt.style.background = '#e10098';
        pkt.innerText = "query { user { name, posts { title } } }";
        beam.style.width = '0px';
        log.innerText = "Client asks for EXACTLY what it needs";
        state = 1;
      } else if (state === 1) {
        pkt.style.left = 'calc(100% - 400px)';
        beam.style.width = 'calc(100% - 240px)';
        state = 2;
      } else if (state === 2) {
        pkt.style.background = '#2ecc71';
        pkt.innerText = '{ "data": { "user": { "name": "Alice", "posts": [...] } } }';
        log.innerText = "Server returns only requested fields (No Over-fetching)";
        state = 3;
      } else if (state === 3) {
        pkt.style.left = '130px';
        state = 4;
      } else {
        pkt.style.opacity = '0';
        beam.style.width = '0px';
        state = 0;
      }
    }, 1200);
  });

  // 3. gRPC
  defineLab('api-grpc', (host) => {
    host.innerHTML = `
      <div class="api-viz-container">
        <div class="api-node api-node-client" style="background: linear-gradient(135deg, #2c3e50, #34495e);">Gateway<span>Client</span></div>
        <div class="grpc-stream-container">
            <div class="grpc-stream"><div id="grpc-s1" class="grpc-chunk" style="background:#e74c3c; width:40px; left:0;"></div></div>
            <div class="grpc-stream"><div id="grpc-s2" class="grpc-chunk" style="background:#3498db; width:60px; left:20%;"></div></div>
            <div class="grpc-stream"><div id="grpc-s3" class="grpc-chunk" style="background:#2ecc71; width:30px; left:80%;"></div></div>
        </div>
        <div class="api-node api-node-server" style="background: linear-gradient(135deg, #2c3e50, #34495e);">Service<span>Server</span></div>
        <div class="api-label">HTTP/2 Multiplexed Binary Streaming (Protobuf)</div>
      </div>
    `;
    const s1 = host.querySelector('#grpc-s1');
    const s2 = host.querySelector('#grpc-s2');
    const s3 = host.querySelector('#grpc-s3');
    setInterval(() => { s1.style.left = s1.style.left === '100%' ? '-40px' : '100%'; }, 900);
    setInterval(() => { s2.style.left = s2.style.left === '100%' ? '-60px' : '100%'; }, 1200);
    setInterval(() => { s3.style.left = s3.style.left === '-30px' ? '100%' : '-30px'; }, 700); // Server stream
  });

  // 4. WebSockets
  defineLab('api-ws', (host) => {
    host.innerHTML = `
      <div class="api-viz-container">
        <div class="api-node api-node-client" style="background: linear-gradient(135deg, #f39c12, #d35400);">Client<span>Browser</span></div>
        <div class="ws-line">
            <div id="ws-p1" class="ws-particle" style="color:#3498db; left:0;"></div>
            <div id="ws-p2" class="ws-particle" style="color:#e74c3c; right:0;"></div>
        </div>
        <div class="api-node api-node-server" style="background: linear-gradient(135deg, #8e44ad, #9b59b6);">Server<span>WS Hub</span></div>
        <div class="api-label">Persistent Full-Duplex Bi-Directional Connection</div>
      </div>
    `;
    const p1 = host.querySelector('#ws-p1');
    const p2 = host.querySelector('#ws-p2');
    setInterval(() => {
      p1.style.left = p1.style.left === '100%' ? '0' : '100%';
      // P2 moves slightly out of sync to show true duplex
      setTimeout(() => { p2.style.right = p2.style.right === '100%' ? '0' : '100%'; }, 300);
    }, 1000);
  });

  // 5. Webhooks
  defineLab('api-webhooks', (host) => {
    host.innerHTML = `
      <div class="api-viz-container">
        <div class="api-node api-node-stripe">Stripe<span>Sender</span></div>
        <div id="wh-packet" class="api-packet" style="background:#e74c3c; left:120px; opacity:0;">Event</div>
        <div class="api-node api-node-server" style="background: linear-gradient(135deg, #34495e, #2c3e50);">Your App<span>Receiver</span></div>
        <div class="api-label" id="wh-log">Idle (No Polling!)</div>
      </div>
    `;
    const pkt = host.querySelector('#wh-packet');
    const log = host.querySelector('#wh-log');
    let state = 0;
    
    setInterval(() => {
      if (state === 0) {
        log.innerText = "Waiting for an event... (Efficient, no polling)";
        pkt.style.opacity = '0';
        pkt.style.left = '130px';
        state = 1;
      } else if (state === 1) {
        pkt.style.opacity = '1';
        pkt.style.background = '#6772e5'; // Stripe color
        pkt.innerText = "POST /webhook { payment: success }";
        log.innerText = "Event Occurs! Sender pushes data to Receiver";
        setTimeout(() => { pkt.style.left = 'calc(100% - 310px)'; }, 100);
        state = 2;
      } else if (state === 2) {
        pkt.style.background = '#2ecc71';
        pkt.innerText = "200 OK (Acknowledged)";
        log.innerText = "Receiver instantly acknowledges receipt";
        pkt.style.left = '130px';
        state = 3;
      } else {
        pkt.style.opacity = '0';
        state = 0;
      }
    }, 1500);
  });

  // 6. SOAP
  defineLab('api-soap', (host) => {
    host.innerHTML = `
      <div class="api-viz-container">
        <div class="api-node api-node-client" style="background: linear-gradient(135deg, #7f8c8d, #95a5a6);">System A<span>Legacy</span></div>
        <div id="soap-packet" class="api-packet soap-env" style="left:120px; opacity:0;">&lt;soap:Envelope&gt;...&lt;/soap:Envelope&gt;</div>
        <div class="api-node api-node-server" style="background: linear-gradient(135deg, #7f8c8d, #95a5a6);">System B<span>Enterprise</span></div>
        <div class="api-label" id="soap-log">Strict XML WSDL Contracts & WS-Security</div>
      </div>
    `;
    const pkt = host.querySelector('#soap-packet');
    const log = host.querySelector('#soap-log');
    let state = 0;
    
    setInterval(() => {
      if (state === 0) {
        pkt.style.opacity = '1';
        pkt.style.left = '130px';
        log.innerText = "Validating strict XML against WSDL...";
        state = 1;
      } else if (state === 1) {
        pkt.style.left = 'calc(100% - 290px)';
        state = 2;
      } else if (state === 2) {
        log.innerText = "Executing ACID Transaction...";
        pkt.style.left = '130px';
        state = 3;
      } else {
        pkt.style.opacity = '0';
        state = 0;
      }
    }, 1200);
  });
  
  // 7. Protobuf (Data format visualization)
  defineLab('api-protobuf', (host) => {
    host.innerHTML = `
      <div class="api-viz-container" style="flex-direction:row; justify-content:space-evenly;">
        <div style="text-align:center;">
          <div style="font-family:var(--mono); font-size:12px; background:var(--surface); padding:10px; border:1px solid var(--border); border-radius:8px;">
            {<br/>&nbsp;&nbsp;"id": 1,<br/>&nbsp;&nbsp;"name": "Alice"<br/>}
          </div>
          <div style="margin-top:10px; font-size:11px; color:var(--text-dim);">JSON (Text) ~ 30 bytes</div>
        </div>
        
        <div id="pb-arrow" style="font-size:24px; transition: transform 0.5s;">➡️</div>
        
        <div style="text-align:center;">
          <div style="font-family:var(--mono); font-size:12px; background:rgba(46, 204, 113, 0.1); color:#2ecc71; padding:10px; border:1px solid #2ecc71; border-radius:8px;">
            08 01 12 05 41 6c 69 63 65
          </div>
          <div style="margin-top:10px; font-size:11px; color:var(--text-dim);">Protobuf (Binary) ~ 9 bytes</div>
        </div>
      </div>
    `;
    const arrow = host.querySelector('#pb-arrow');
    setInterval(() => {
      arrow.style.transform = arrow.style.transform === 'scale(1.3)' ? 'scale(1)' : 'scale(1.3)';
    }, 600);
  });

}
