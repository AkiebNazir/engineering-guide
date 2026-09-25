import os
import subprocess

test_file = "temp.md"

content = """
```arch
%% caption: The catalog write path never depends on search — the outbox is what makes a crash-after-commit safe to replay.
node admin "Admin" at 0,0
node catalog "Catalog API" at 1,0
node relay "Outbox / CDC" at 2,0
node stream "Stream" at 3,0
node indexer "Indexer" at 4,0
node search "Search cluster" at 4,1

admin -> catalog : "edit product"
catalog -> relay : "outbox row"
relay -> stream : "publish"
stream -> indexer : "consume"
indexer -> search : "write"

node user "User" at 0,2
node cdn "CDN" at 2,2

user -> cdn : "request"
cdn -> user : "cached response"
cdn -> search : "miss: query"
search -> user : "results"
```

```arch
%% caption: The snapshot watermark closes the gap where a product changes while the bulk read is still running.
node job "Reindex job" at 0,1
node catalog "Catalog" at 1,0
node v42 "index_v42 (new)" at 2,0
node alias "Read alias" at 1,2
node v41 "index_v41 (old)" at 2,2

job -> catalog : "read / replay"
catalog -> v42 : "write / apply"
job -> v42 : "create / validate"
job -> alias : "move alias"
alias -> v42 : "points to"
alias -> v41 : "used to point to"
```
"""

with open(test_file, "w") as f:
    f.write(content)

result = subprocess.run(["node", "webapp/arch_tool.mjs", "check", test_file], capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
