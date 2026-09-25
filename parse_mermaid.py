import re

with open('SystemDesign/solutions/006_chat_solution.md', 'r') as f:
    content = f.read()

blocks = re.findall(r'```mermaid(.*?)```', content, re.DOTALL)
for i, b in enumerate(blocks):
    print(f"--- Block {i} ---")
    print(b)

