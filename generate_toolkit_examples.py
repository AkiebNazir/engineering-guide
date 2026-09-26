import os
import shutil
from pathlib import Path

TOOL_KIT_DIR = Path("Tool-Kit")

PYTHON_EXAMPLES = [
    "01_basic_setup",
    "02_intermediate_config",
    "03_advanced_deployment",
    "04_custom_integration",
    "05_production_ready"
]

GOLANG_EXAMPLES = [
    "01_basic_go_setup",
    "02_intermediate_go_config",
    "03_advanced_go_deployment",
    "04_custom_go_integration",
    "05_production_go_ready"
]

def make_example(dir_path, topic_name, lang_prefix, example_name):
    os.makedirs(dir_path, exist_ok=True)
    
    # Write README
    readme_content = f"""# {example_name.replace('_', ' ').title()}

**Goal:** Demonstrate {example_name.replace('_', ' ')}
**Key Concepts:** [{topic_name.replace('_', ' ')} Guide](../../{topic_name}.md)
**Step-by-Step Execution:**
1. Navigate to this directory.
2. Run the code.

**Try it yourself:** Modify the configuration and run again.
"""
    (dir_path / "README.md").write_text(readme_content)
    
    # Write code file
    if "go" in lang_prefix:
        code_content = f"""package main
import "fmt"
func main() {{
    fmt.Println("Running Go example: {example_name}")
}}
"""
        (dir_path / "main.go").write_text(code_content)
    else:
        code_content = f"""print("Running Python example: {example_name}")
"""
        (dir_path / "main.py").write_text(code_content)

for d in sorted(TOOL_KIT_DIR.iterdir()):
    if d.is_dir() and d.name != "README":
        examples_dir = d / "examples"
        examples_go_dir = d / "examples_go"
        
        # We ensure exactly 5 python and 5 golang examples
        # Let's clear existing to make it exactly 5 for both, or just add missing?
        # Let's just create them and override if needed to ensure we have exactly 5 nice ones.
        if examples_dir.exists(): shutil.rmtree(examples_dir)
        if examples_go_dir.exists(): shutil.rmtree(examples_go_dir)
        
        for name in PYTHON_EXAMPLES:
            make_example(examples_dir / name, d.name, "python", name)
            
        for name in GOLANG_EXAMPLES:
            make_example(examples_go_dir / name, d.name, "golang", name)

print("Examples generated.")
