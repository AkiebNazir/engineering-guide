# Architecture diagrams: the `arch` block

Every box-and-arrow diagram in this repo is an ` ```arch ` fenced block. The reader
(`webapp/static/arch-diagram.js`) draws it in the AWS reference-diagram style:
coloured icon tiles, tinted region/VPC-style panels, and right-angle connectors that
run through the gutters between cells instead of across each other.

Why not mermaid `flowchart`: dagre/ELK choose the positions, and on real system
diagrams that produces crossing lines and nodes flung to the edges. Here **you** place
every node on a grid cell. The router only draws the lines, so the same source always
gives the same picture.

Mermaid still owns what it is good at: `sequenceDiagram` (request timelines),
`mindmap`, `xychart-beta`. Box-and-arrow `flowchart` / `graph` / `stateDiagram`
blocks are `arch`.

On pages that also have a live, animated lab (System Design `sd-flow-*`, CS
Fundamentals labs), the static `arch` diagram comes **first**, near the top of the
section, and the live lab follows it at the end of that section.

## Syntax

```
%% caption: One sentence shown under the figure (optional, keep it).
grid 160x120                                   optional: cell pitch in px (these are the defaults)
route straight                                 optional: straight lines instead of right angles (trees, graphs)

group <id> "Label" [in <parentGroup>] [color=<c>] [icon=<i>] [style=dashed|solid]
node  <id> "Label" at <col>,<row> [in <group>] [icon=<i>] [shape=<s>] [sub="small second line"] [color=<c>] [w=<px>]

a -> b                      arrow
a <-> b                     both ends
a -- b                      plain line
a ..> b                     dashed arrow (async, replication, eventual)
a <..> b   a .. b           dashed both / plain
a ==> b                     thick arrow (the hot path)
a -> b -> c                 chain
a -> b : "label"            edge label (keep it to 1-4 words)
a:R -> b:L                  force the ports: T B L R
a -> b dashed color=red     flags: dashed thick straight, color=<c>
```

* `at col,row`: zero-based. Columns go left to right, rows top to bottom. Half steps
  (`at 1.5,2`) centre a node between two columns. Two nodes may not share a cell.
* Spacing adapts: a gap grows to fit a big node, and each group edge between two
  cells adds padding. You never need to leave empty cells for a group border.
* A label may contain `\n` for a forced line break.
* `%%` lines are comments; `%% caption:` is the figure caption.

### Shapes: pick by what the node *is*

| shape | looks like | use for |
|---|---|---|
| `tile` (default when `icon=` is set) | 48px coloured icon square, label underneath | **system components**: services, DBs, caches, queues, clients, LBs, CDNs |
| `card` | rounded card, small icon badge, title + `sub` text | a component or step that needs a sentence of explanation |
| `box` (default with no icon) | tinted rounded rectangle | process steps, plain concepts |
| `pill` | capsule | start/end, an interface/boundary, a label in a pipeline |
| `diamond` | decision | yes/no branching. Keep the text to a short question |
| `circle` | round node, text inside | data-structure nodes: tree/heap/graph/trie vertices, states |
| `cyl` | cylinder | a store, when you want the classic DB silhouette without an icon |
| `text` | italic text, no border | an annotation next to something |

### Colours

`blue purple green orange red pink teal slate amber indigo cyan`. Tiles pick their
colour from the icon's category (compute orange, network purple, storage green,
database blue, security red, messaging pink, AI teal, observability pink, client
slate), which gives the AWS look for free. Use `color=` on groups, boxes, circles and
decisions to group meaning: e.g. green = success path, red = failure, amber =
decision.

### Icons

Generic (drawn white on the category-coloured tile):

* **people/clients**: user users admin client browser mobile desktop cli developer
* **network/edge**: internet dns cdn lb gateway api network firewall proxy mesh region cloud wifi link connection edge
* **compute**: server service app worker process function container k8s cpu memory scheduler cron thread code package rocket git plugin
* **data**: db sql nosql replica index table cache kv search storage blob disk file doc folder archive layers vector graph tree matrix grid counter sort filter sigma
* **messaging**: queue stream topic event webhook email notify message chat sync workflow sitemap forum
* **security**: auth lock key secrets identity shield alert
* **observability**: metrics dashboard logs monitor gauge trace timer speed eye time
* **AI**: llm model agent bot tool prompt embed idea
* **misc**: payment cart store delivery map video image music news feed tag id decision check error warn question start stop edit delete flag learn group text number

Brand logos (full colour; `logos:` prefix optional): `aws-*` (api-gateway, aurora,
cloudfront, cloudwatch, cognito, dynamodb, ec2, ecs, eks, elasticache, elb,
eventbridge, fargate, glacier, iam, kinesis, kms, lambda, msk, open-search, rds,
redshift, route53, s3, secrets-manager, sns, sqs, step-functions, vpc, waf, athena,
glue, neptune, timestream), kafka-icon, redis, postgresql, mongodb-icon, cassandra,
elasticsearch, rabbitmq-icon, nginx, docker-icon, kubernetes, grpc, graphql,
openai-icon, anthropic-icon, prometheus, grafana, python, go, react, cloudflare-icon,
google-cloud, google-gemini-icon, mysql-icon, sqlite, etcd, consul, vault-icon,
terraform-icon, github-icon, git-icon, jenkins, nodejs-icon, java, rust, linux-tux,
apache-spark, apache-flink-icon, hadoop, memcached, datadog-icon, stripe, slack-icon,
twilio-icon, envoy, meta-icon, mistral-ai-icon, pinecone-icon, swagger,
postman-icon, websocket, json, html-5, chrome, android-icon, apple, fastapi-icon,
flask, django-icon.

Use a brand logo only when the text names that product ("Kafka", "Redis",
"DynamoDB"). A generic "message queue" gets `icon=queue`, not a Kafka logo.

## Layout rules: what makes it read like the reference

1. **Flow in one direction.** Requests go top → bottom (or left → right). Put clients
   on row 0, the edge/LB next, services in the middle, data stores at the bottom.
2. **Groups are boundaries that mean something**: region, VPC, cluster, trust
   boundary, "write path", "control plane", "kernel space". Nest at most two deep.
   Put everything that is inside the boundary in the group (`in <id>`); the linter
   fails a node that sits inside a panel without being a member.
3. **Align.** Things at the same tier share a row; a chain shares a column. Straight
   lines beat bent ones. Mirror symmetric things (two regions, primary/replica).
4. **Keep it narrow.** The reader column is ~640px and a diagram is never shown below
   720px (wider ones scroll sideways). Aim for **≤ 760px natural width** (about 4
   tile columns, or 3 card columns), and treat 900px as the hard ceiling. Go taller
   before you go wider.
5. **Few crossings.** Place nodes so edges don't have to cross. `check` reports
   crossings; 0–2 is the target.
6. **Labels are short.** Node label: 1–4 words; detail goes in `sub=`. Edge label:
   1–4 words. The caption and prose carry the explanation.
7. **Don't lose information.** A converted diagram keeps every node, every edge,
   every label and the caption of the original. Restyle it; don't cut it.

## Checking your work

```
node webapp/arch_tool.mjs check path/to/file.md      # syntax, overlaps, lines through boxes, crossings, size
node webapp/arch_tool.mjs shot  path/to/file.md 3    # PNG of block 3 (add --dark, --out DIR)
```

`check` must report no `FAIL`. Look at the `shot` PNG of every diagram you write:
the linter can't tell you that the layout is ugly.

## Examples

A cloud architecture:

```arch
%% caption: Two regions serve traffic independently; the data layer replicates between them.
node dns "Route 53" at 1.5,0 icon=aws-route53
group r1 "Region A" icon=region color=blue
node lb1 "Load balancer" at 0,1 in r1 icon=lb
node app1 "App servers" at 0,2 in r1 icon=server sub="autoscaled"
node db1 "Primary DB" at 0,3 in r1 icon=db
group r2 "Region B" icon=region color=blue
node lb2 "Load balancer" at 3,1 in r2 icon=lb
node app2 "App servers" at 3,2 in r2 icon=server sub="autoscaled"
node db2 "Replica DB" at 3,3 in r2 icon=replica
dns -> lb1
dns -> lb2
lb1 -> app1 -> db1
lb2 -> app2 -> db2
db1 ..> db2 : "async replication"
```

A decision flow:

```arch
%% caption: Pick the range structure from what the operations need.
node q "What does the problem ask?" at 1,0 shape=pill
node d1 "Range updates or min/max?" at 1,1 shape=diamond color=amber
node seg "Segment tree" at 0,2 shape=card icon=tree sub="O(log n) query + update"
node fw "Fenwick tree" at 2,2 shape=card icon=counter sub="invertible op, point updates"
q -> d1
d1 -> seg : "yes"
d1 -> fw : "no"
```

A data structure (straight edges, circles, a tight grid: data-structure pictures want
`grid 70x80` to `grid 110x100`, not the component-sized default):

```arch
%% caption: A min-heap: every parent is no larger than its children.
route straight
grid 80x90
node a "1" at 1.5,0 shape=circle color=blue
node b "3" at 0.5,1 shape=circle color=blue
node c "2" at 2.5,1 shape=circle color=blue
node d "7" at 0,2 shape=circle color=blue
node e "4" at 1,2 shape=circle color=blue
a -- b
a -- c
b -- d
b -- e
```
