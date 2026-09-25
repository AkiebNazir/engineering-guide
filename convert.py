import sys

def replace_file():
    filepath = 'CICD/06-Continuous-Delivery-and-Deployment/06-Continuous-Delivery-and-Deployment.md'
    with open(filepath, 'r') as f:
        content = f.read()
        
    diagram1_mermaid = """```mermaid
flowchart LR
    Dev["Developer Commit"] --> CI["CI Pipeline\\n(Build & Test)"]
    CI --> Staging["Deploy to Staging"]
    Staging --> Gate{"Approval Gate"}
    Gate -- Manual Approval --> Prod["Deploy to Production"]
```"""
    diagram1_arch = """```arch
node Dev "Developer Commit" at 0,0
node CI "CI Pipeline\\n(Build & Test)" at 0,2
node Staging "Deploy to Staging" at 0,4
node Gate "Approval Gate" at 0,6
node Prod "Deploy to Production" at 0,8

Dev -> CI
CI -> Staging
Staging -> Gate
Gate -> Prod : "Manual Approval"
```"""
    
    diagram2_mermaid = """```mermaid
flowchart LR
    Dev["Developer Commit"] --> CI["CI Pipeline\\n(Build & Test)"]
    CI --> Staging["Deploy to Staging & Run E2E"]
    Staging --> Prod["Auto-Deploy to Production"]
```"""
    diagram2_arch = """```arch
node Dev "Developer Commit" at 0,0
node CI "CI Pipeline\\n(Build & Test)" at 0,2
node Staging "Deploy to Staging\\n& Run E2E" at 0,4
node Prod "Auto-Deploy to\\nProduction" at 0,6

Dev -> CI
CI -> Staging
Staging -> Prod
```"""

    diagram3_mermaid = """```mermaid
sequenceDiagram
    participant Pipeline
    participant AppServer
    participant Database

    Pipeline->>Database: Run Migration Scripts (V1 -> V2)
    Pipeline->>AppServer: Deploy New Code (V2)
    AppServer->>Database: Queries using V2 schema
```"""
    diagram3_arch = """```arch
node Pipeline "Pipeline" at 0,0
node AppServer "App Server" at 0,3
node Database "Database" at 0,6

Pipeline -> Database : "1. Run Migration\\nScripts (V1 -> V2)"
Pipeline -> AppServer : "2. Deploy New\\nCode (V2)"
AppServer -> Database : "3. Queries using\\nV2 schema"
```"""

    content = content.replace(diagram1_mermaid, diagram1_arch)
    content = content.replace(diagram2_mermaid, diagram2_arch)
    content = content.replace(diagram3_mermaid, diagram3_arch)

    with open(filepath, 'w') as f:
        f.write(content)

replace_file()
