```arch
node Pipeline "Pipeline" at 0,0
node AppServer "App Server" at 0,3
node Database "Database" at 0,6

Pipeline -> Database : "1. Run Migration\nScripts (V1 -> V2)"
Pipeline -> AppServer : "2. Deploy New\nCode (V2)"
AppServer -> Database : "3. Queries using\nV2 schema"
```
