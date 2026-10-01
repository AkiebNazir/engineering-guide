# BASIC EXAMPLE: Python Inbuilt xmlrpc.server
# Demonstrates the standard library precursor to gRPC (XML-RPC).
from xmlrpc.server import SimpleXMLRPCServer

def get_user(id_str):
    if id_str == "1":
        return {"id": "1", "name": "Alice"}
    return {}

if __name__ == "__main__":
    server = SimpleXMLRPCServer(("localhost", 8000))
    print("XML-RPC Listening on port 8000...")
    server.register_function(get_user, "get_user")
    server.serve_forever()

    # To test as a client:
    # import xmlrpc.client
    # proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")
    # print(proxy.get_user("1"))
