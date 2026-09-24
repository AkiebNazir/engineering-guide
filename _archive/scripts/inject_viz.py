import os
from pathlib import Path

API_DIR = Path('/Users/njasm/Njasm/AI/DSA-Practice/API')

injections = {
    "REST/REST_API_Guide.md": """
## Architectural Diagram & Visualization

<div data-viz="api-rest"></div>

```mermaid
sequenceDiagram
    participant Client
    participant LoadBalancer
    participant APIGateway
    participant RESTService
    participant Database

    Client->>LoadBalancer: GET /api/v1/users
    LoadBalancer->>APIGateway: Route Request
    APIGateway->>RESTService: Validate & Forward
    RESTService->>Database: SELECT * FROM users
    Database-->>RESTService: Rows Data
    RESTService-->>APIGateway: JSON Response
    APIGateway-->>LoadBalancer: 200 OK
    LoadBalancer-->>Client: 200 OK (JSON Data)
```
""",
    "GraphQL/GraphQL_Guide.md": """
## Architectural Diagram & Visualization

<div data-viz="api-graphql"></div>

```mermaid
sequenceDiagram
    participant Client
    participant GraphQLServer
    participant UserDB
    participant PostDB

    Client->>GraphQLServer: POST { user { name, posts { title } } }
    GraphQLServer->>UserDB: Resolve User
    UserDB-->>GraphQLServer: User Data
    GraphQLServer->>PostDB: Resolve User's Posts
    PostDB-->>GraphQLServer: Posts Data
    GraphQLServer-->>Client: JSON { data: { user: ... } }
```
""",
    "WebSockets/WebSockets_Guide.md": """
## Architectural Diagram & Visualization

<div data-viz="api-ws"></div>

```mermaid
sequenceDiagram
    participant Client
    participant WebSocketServer
    participant RedisPubSub

    Client->>WebSocketServer: HTTP GET /ws (Upgrade: websocket)
    WebSocketServer-->>Client: 101 Switching Protocols
    note over Client,WebSocketServer: Persistent TCP Connection Established
    Client->>WebSocketServer: {"action": "join_room", "room": "chat1"}
    WebSocketServer->>RedisPubSub: SUBSCRIBE chat1
    RedisPubSub-->>WebSocketServer: Subscribed
    WebSocketServer->>Client: {"msg": "Joined room"}
```
""",
    "gRPC/gRPC_Guide.md": """
## Architectural Diagram & Visualization

<div data-viz="api-grpc"></div>

```mermaid
sequenceDiagram
    participant Client (Go)
    participant gRPC Server (Python)
    
    Client->>Client (Go): Generate Stub
    Client->>gRPC Server (Python): HTTP/2 POST /MyService/ProcessData (Binary)
    note over Client (Go),gRPC Server (Python): Multiplexed over single TCP connection
    gRPC Server (Python)->>gRPC Server (Python): Decode Protobuf
    gRPC Server (Python)-->>Client (Go): HTTP/2 200 OK + Protobuf Payload
    Client->>Client (Go): Parse Response
```
""",
    "Protobuf/Protobuf_Guide.md": """
## Architectural Diagram & Visualization

<div data-viz="api-protobuf"></div>

```mermaid
flowchart LR
    A[user.proto Schema] -->|protoc| B(user.pb.go)
    A -->|protoc| C(user_pb2.py)
    B -->|Serialize| D[(Binary 0x08 0x01)]
    D -->|Network| E[(Binary 0x08 0x01)]
    E -->|Deserialize| C
```
"""
}

for rel_path, content in injections.items():
    p = API_DIR / rel_path
    if p.exists():
        original = p.read_text()
        if '<div data-viz=' not in original:
            # Inject right after the first heading
            lines = original.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('# '):
                    lines.insert(i + 1, content)
                    break
            else:
                lines.insert(0, content)
            p.write_text('\n'.join(lines))
            print(f"Injected into {rel_path}")

