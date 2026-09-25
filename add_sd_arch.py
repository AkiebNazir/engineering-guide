import re

inserts = [
    (
        "SoftwareDesign/06_error_handling_and_failure_design.md",
        "Everything else should let the error propagate.",
        '''```arch\n%% caption: Error Handling Architecture Boundaries\ngroup bnd "4. Boundary Layer (HTTP/Job)" color=blue style=dashed\nnode ctrl "HTTP Controller\\n(returns 500 / logs)" at 1,0 in bnd icon=api\n\ngroup domain "3. Domain / Use Case Layer" color=green style=dashed\nnode usecase "User Onboarding\\n(adds context)" at 1,1 in domain icon=process\n\ngroup adapt "2. Adapter Layer" color=amber style=dashed\nnode repo "SQL Repository\\n(translates error)" at 1,2 in adapt icon=database\n\nnode db "Database\\n(throws IntegrityError)" at 1,3 icon=db color=slate\n\ndb -> repo : "throw"\nrepo -> usecase : "throw\\nDuplicateEmail"\nusecase -> ctrl : "throw\\n(with note)"\nctrl -> ctrl : "log\\n& stop"\n```\n\nEverything else should let the error propagate.'''
    ),
    (
        "SoftwareDesign/06_error_handling_and_failure_design.md",
        "### Order the steps",
        '''```arch\n%% caption: Partial Failure Compensation Flow (Saga Pattern)\nnode client "Client" at 0,1 icon=client\nnode s1 "Step 1\\n(Reserve Inventory)" at 1,0 icon=box color=blue\nnode s2 "Step 2\\n(Charge Card)" at 2,1 icon=payment color=amber\nnode comp "Compensate\\n(Release Inventory)" at 1,2 icon=undo color=red\n\nclient -> s1 : "1. do()"\nclient -> s2 : "2. do() [fails]"\ns2 -> comp : "3. error triggers undo()"\n```\n\n### Order the steps'''
    ),
    (
        "SoftwareDesign/07_designing_concurrent_code.md",
        "The smallest version: one thread owns a plain list, everyone else sends it messages",
        '''```arch\n%% caption: Actor Model Pattern (Single Writer)\nnode t1 "Thread A" at 0,0 icon=process color=blue\nnode t2 "Thread B" at 1,0 icon=process color=blue\nnode t3 "Thread C" at 2,0 icon=process color=blue\n\nnode q "Message Queue\\n(Inbox)" at 1,1 shape=card icon=queue color=amber\nnode actor "Actor Thread\\n(State Owner)" at 1,2 icon=process color=green\nnode state "Mutable State" at 1,3 shape=circle icon=database color=red\n\nt1 -> q : "push"\nt2 -> q : "push"\nt3 -> q : "push"\nq -> actor : "pop (sequential)"\nactor -> state : "mutate\\n(no locks!)"\n```\n\nThe smallest version: one thread owns a plain list, everyone else sends it messages'''
    ),
    (
        "SoftwareDesign/07_designing_concurrent_code.md",
        "Single-flight makes concurrent callers",
        '''```arch\n%% caption: Single-flight Cache Pattern\nnode c1 "Client 1" at 0,0 icon=client color=blue\nnode c2 "Client 2" at 1,0 icon=client color=blue\nnode c3 "Client 3" at 2,0 icon=client color=blue\n\nnode cache "Single-Flight\\nCache" at 1,1 shape=card icon=cache color=green\nnode db "Database" at 1,2 shape=cyl icon=db color=slate\n\nc1 -> cache : "1. miss (leader)"\nc2 -> cache : "2. miss (wait)"\nc3 -> cache : "3. miss (wait)"\ncache ==> db : "4. single fetch"\ndb ==> cache : "5. result"\ncache -> c1 : "6. return"\ncache -> c2 : "6. return"\ncache -> c3 : "6. return"\n```\n\nSingle-flight makes concurrent callers'''
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

