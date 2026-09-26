import os
import shutil

base = "/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Secret_Management"
examples_py_dir = os.path.join(base, "examples")
examples_go_dir = os.path.join(base, "examples_go")

if os.path.exists(examples_py_dir):
    shutil.rmtree(examples_py_dir)
if os.path.exists(examples_go_dir):
    shutil.rmtree(examples_go_dir)

files = {}

# Python
files["examples/01_kv_read_write/README.md"] = "# KV V2 Secret Read/Write (Python)"
files["examples/01_kv_read_write/main.py"] = "import hvac\nprint('KV Python')"
files["examples/02_approle_auth/README.md"] = "# AppRole Authentication (Python)"
files["examples/02_approle_auth/main.py"] = "import hvac\nprint('AppRole Python')"
files["examples/03_dynamic_db_secrets/README.md"] = "# Dynamic Database Secrets (Python)"
files["examples/03_dynamic_db_secrets/main.py"] = "import hvac\nprint('Dynamic DB Python')"
files["examples/04_transit_encryption/README.md"] = "# Transit Encryption (Python)"
files["examples/04_transit_encryption/main.py"] = "import hvac\nprint('Transit Python')"
files["examples/05_aws_dynamic_secrets/README.md"] = "# AWS Dynamic Secrets (Python)"
files["examples/05_aws_dynamic_secrets/main.py"] = "import hvac\nprint('AWS Python')"

# Go
files["examples_go/01_kv_read_write/README.md"] = "# KV V2 Secret Read/Write (Golang)"
files["examples_go/01_kv_read_write/main.go"] = "package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"KV Go\") }"
files["examples_go/02_approle_auth/README.md"] = "# AppRole Authentication (Golang)"
files["examples_go/02_approle_auth/main.go"] = "package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"AppRole Go\") }"
files["examples_go/03_dynamic_db_secrets/README.md"] = "# Dynamic Database Secrets (Golang)"
files["examples_go/03_dynamic_db_secrets/main.go"] = "package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"Dynamic DB Go\") }"
files["examples_go/04_transit_encryption/README.md"] = "# Transit Encryption (Golang)"
files["examples_go/04_transit_encryption/main.go"] = "package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"Transit Go\") }"
files["examples_go/05_aws_dynamic_secrets/README.md"] = "# AWS Dynamic Secrets (Golang)"
files["examples_go/05_aws_dynamic_secrets/main.go"] = "package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"AWS Go\") }"

for filepath, content in files.items():
    full_path = os.path.join(base, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content.strip() + "\\n")
