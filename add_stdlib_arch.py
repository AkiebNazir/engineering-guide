import re

inserts = [
    (
        "GoStdLib/03_io/GUIDE.md",
        "## When to reach for it vs alternatives already in this repo",
        '''```arch\n%% caption: Go io Interfaces Architecture\nnode r "io.Reader" at 0,1 shape=diamond icon=file color=blue\nnode w "io.Writer" at 2,1 shape=diamond icon=file color=amber\nnode rw "io.ReadWriter" at 1,0 shape=diamond icon=layers color=green\n\nnode f "os.File" at 0,2 shape=card icon=disk color=slate\nnode net "net.Conn" at 2,2 shape=card icon=network color=slate\nnode buf "bytes.Buffer" at 1,2 shape=card icon=memory color=slate\n\nr -> rw : "embeds"\nw -> rw : "embeds"\nf -> r : "implements"\nnet -> rw : "implements"\nbuf -> rw : "implements"\n```\n\n## When to reach for it vs alternatives already in this repo'''
    ),
    (
        "PyStdLib/01_os/GUIDE.md",
        "## When to reach for `os` vs alternatives already in this repo",
        '''```arch\n%% caption: Python os Module Architecture\nnode os "os module" at 1,1 shape=hexagon icon=process color=blue\nnode sys "POSIX / Win32 Syscalls" at 1,2 shape=card icon=server color=slate\nnode p "pathlib" at 0,0 shape=card icon=folder color=green\nnode sub "subprocess" at 2,0 shape=card icon=process color=amber\n\nos -> sys : "wraps"\np -> os : "uses (os.stat, os.scandir)"\nsub -> os : "uses (os.exec, os.pipe)"\n```\n\n## When to reach for `os` vs alternatives already in this repo'''
    )
]

for file_path, search_str, replace_str in inserts:
    with open(file_path, "r") as f:
        content = f.read()
    if replace_str not in content:
        content = content.replace(search_str, replace_str)
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Added arch to {file_path}")
    else:
        print(f"Skipped {file_path}")
