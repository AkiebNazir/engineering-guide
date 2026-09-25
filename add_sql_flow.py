import re

js_file = "webapp/static/flows-osdb.js"
md_file = "SQL/09_transactions_and_isolation_levels.md"

with open(js_file, "r") as f:
    js_content = f.read()

sql_flow = """
/* ================================================= sql transaction (SQL/09) == */
const LosTx = lane([
  { label: 'TRANSACTION A', nodes: [
    { id: 't1_b', label: 'BEGIN', kind: 'client', icon: 'start', row: 0 },
    { id: 't1_w', label: 'UPDATE account', kind: 'client', icon: 'edit', row: 1 },
    { id: 't1_c', label: 'COMMIT', kind: 'client', icon: 'check', row: 4 }] },
  { label: 'DATABASE (Postgres)', nodes: [
    { id: 'db_row', label: 'Row Data', sub: 'balance=100', kind: 'db', icon: 'db', row: 2 },
    { id: 'db_lock', label: 'Row Lock', sub: 'exclusive', kind: 'cache', icon: 'lock', row: 1 }] },
  { label: 'TRANSACTION B', nodes: [
    { id: 't2_b', label: 'BEGIN', kind: 'client', icon: 'start', row: 0 },
    { id: 't2_r', label: 'SELECT balance', sub: 'Read Committed', kind: 'client', icon: 'search', row: 2 },
    { id: 't2_w', label: 'UPDATE account', sub: 'Blocked', kind: 'client', icon: 'edit', row: 3 }] }
]);

defineFlow('flow-sql-isolation', {
  title: 'Live flow: ACID Isolation Levels',
  hint: 'Watch how Transaction B is blocked from writing, but under Read Committed can still read the old value.',
  zones: LosTx.zones, h: LosTx.h, nodes: LosTx.nodes,
  edges: [
    ['t1_b', 't1_w'], ['t1_w', 'db_lock'], ['t1_w', 'db_row'],
    ['t2_b', 't2_r'], ['t2_r', 'db_row'], ['t2_r', 't2_w'], ['t2_w', 'db_lock'],
    ['db_lock', 't1_c', { dashed: true }]
  ],
  scenarios: [
    {
      id: 'rc', name: 'Read Committed (Postgres Default)',
      summary: 'Tx A updates the row (taking the exclusive lock). Tx B tries to read it: under Read Committed, it reads the <b>old</b> committed value (no lock needed). Tx B then tries to update it and <b>blocks</b> waiting for Tx A to commit.',
      steps: [
        { node: 't1_b', note: 'Tx A starts' },
        { node: 't1_w', edge: ['t1_b', 't1_w'] },
        { node: 'db_lock', edge: ['t1_w', 'db_lock'], note: 'Tx A acquires the exclusive row lock.' },
        { node: 'db_row', edge: ['t1_w', 'db_row'], note: 'Tx A writes the new value, but it is uncommitted.' },
        { node: 't2_b', note: 'Tx B starts' },
        { node: 't2_r', edge: ['t2_b', 't2_r'] },
        { node: 'db_row', edge: ['t2_r', 'db_row'], note: 'Tx B reads the old snapshot value (100).' },
        { node: 't2_w', edge: ['t2_r', 't2_w'] },
        { node: 'db_lock', edge: ['t2_w', 'db_lock'], error: true, note: 'Tx B tries to update and blocks!' },
        { node: 't1_c', edge: ['db_lock', 't1_c'], note: 'Tx A commits, releasing the lock. Tx B can now proceed.' }
      ]
    }
  ]
});
"""

if 'flow-sql-isolation' not in js_content:
    js_content = js_content.rstrip().rstrip('}') + sql_flow + "\n}\n"
    with open(js_file, "w") as f:
        f.write(js_content)
    print("Added flow to flows-osdb.js")

with open(md_file, "r") as f:
    md_content = f.read()

if 'data-viz="flow-sql-isolation"' not in md_content:
    # Insert after the Read Committed section
    insert_marker = "Postgres defaults to Read Committed."
    new_text = f"{insert_marker}\n\n<div class=\"lab\" data-viz=\"flow-sql-isolation\"></div>\n"
    md_content = md_content.replace(insert_marker, new_text)
    with open(md_file, "w") as f:
        f.write(md_content)
    print("Added div to SQL/09_transactions_and_isolation_levels.md")

