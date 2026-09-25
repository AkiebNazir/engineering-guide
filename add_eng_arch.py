import re

inserts = [
    (
        "PyEngineering/01_rest_api_service/01_rest_api_service_explanation.py",
        "A small but production-shaped",
        '''```arch\n%% caption: REST API Service Architecture\nnode req "Client Request" at 0,1 icon=client color=blue\nnode api "FastAPI Router\\n(HTTP endpoints)" at 1,1 icon=api color=green\nnode valid "Pydantic\\n(Validation)" at 2,1 icon=check color=amber\nnode domain "Domain Logic\\n(CRUD ops)" at 3,1 icon=process color=slate\nnode db "In-Memory Store\\n(with asyncio.Lock)" at 4,1 icon=memory color=red\n\nreq -> api\napi -> valid : "parses JSON"\nvalid -> domain : "valid payload"\ndomain -> db : "safe mutation"\n```\n\nA small but production-shaped'''
    ),
    (
        "GoEngineering/01_rest_api_service/explanation/01_rest_api_service_explanation.go",
        "A small but production-shaped",
        '''```arch\n%% caption: REST API Service Architecture\nnode req "Client Request" at 0,1 icon=client color=blue\nnode api "ServeMux Router\\n(HTTP endpoints)" at 1,1 icon=api color=green\nnode valid "JSON Decode\\n(& Validation)" at 2,1 icon=check color=amber\nnode domain "Domain Logic\\n(CRUD ops)" at 3,1 icon=process color=slate\nnode db "In-Memory Store\\n(with sync.RWMutex)" at 4,1 icon=memory color=red\n\nreq -> api\napi -> valid : "parses JSON"\nvalid -> domain : "valid payload"\ndomain -> db : "safe mutation"\n```\n\nA small but production-shaped'''
    ),
    (
        "PyEngineering/02_middleware_chain/02_middleware_chain_explanation.py",
        "A small stack of composable **pure-ASGI middleware**",
        '''```arch\n%% caption: Middleware Onion Architecture\ngroup m "Middleware Chain (Outbound & Inbound)" color=slate style=dashed\nnode m1 "Exception\\nHandling" at 1,0 in m icon=shield color=red\nnode m2 "Request\\nID" at 2,0 in m icon=tag color=blue\nnode m3 "Access\\nLog" at 3,0 in m icon=file color=amber\nnode m4 "Timeout" at 4,0 in m icon=cron color=purple\nnode m5 "Auth" at 5,0 in m icon=lock color=green\n\nnode client "Client" at 0,0 icon=client color=blue\nnode app "FastAPI App\\n(Business Logic)" at 6,0 icon=process color=slate\n\nclient -> m1\nm1 -> m2\nm2 -> m3\nm3 -> m4\nm4 -> m5\nm5 -> app\n```\n\nA small stack of composable **pure-ASGI middleware**'''
    ),
    (
        "GoEngineering/02_middleware_chain/explanation/02_middleware_chain_explanation.go",
        "A composable HTTP middleware stack",
        '''```arch\n%% caption: Middleware Onion Architecture\ngroup m "Middleware Chain (Outbound & Inbound)" color=slate style=dashed\nnode m1 "Panic\\nRecovery" at 1,0 in m icon=shield color=red\nnode m2 "Request\\nID" at 2,0 in m icon=tag color=blue\nnode m3 "Access\\nLog" at 3,0 in m icon=file color=amber\nnode m4 "Timeout" at 4,0 in m icon=cron color=purple\nnode m5 "Auth" at 5,0 in m icon=lock color=green\n\nnode client "Client" at 0,0 icon=client color=blue\nnode app "http.Handler\\n(Business Logic)" at 6,0 icon=process color=slate\n\nclient -> m1\nm1 -> m2\nm2 -> m3\nm3 -> m4\nm4 -> m5\nm5 -> app\n```\n\nA composable HTTP middleware stack'''
    )
]

for file_path, search_str, replace_str in inserts:
    try:
        with open(file_path, "r") as f:
            content = f.read()
        if "```arch" not in content:
            content = content.replace(search_str, replace_str)
            with open(file_path, "w") as f:
                f.write(content)
            print(f"Added arch to {file_path}")
        else:
            print(f"Skipped {file_path}")
    except Exception as e:
        print(f"Failed {file_path}: {e}")

