with open("webapp/server.py", "r") as f:
    code = f.read()

bad_str = """                items.append({
                    "id": path.name,
                    "num": num,
                    "kind": "level",
                    "group": group_name,
                    **doc_meta(md_file, f"Theory: {topic_name}")
                })
            
            return items"""

good_str = """                items.append({
                    "id": path.name,
                    "num": num,
                    "kind": "level",
                    "group": group_name,
                    **doc_meta(md_file, f"Theory: {topic_name}")
                })
    return items"""

if bad_str in code:
    code = code.replace(bad_str, good_str)
    with open("webapp/server.py", "w") as f:
        f.write(code)
    print("Fixed!")
else:
    print("Not found.")
