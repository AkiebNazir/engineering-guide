import asyncio
import websockets
import json

async def auth_via_first_frame():
    uri = "ws://localhost:8080/ws"
    
    try:
        async with websockets.connect(uri) as ws:
            auth_payload = json.dumps({
                "type": "authenticate",
                "token": "valid-jwt-token"
            })
            
            await ws.send(auth_payload)
            response = await ws.recv()
            print(f"Server response: {response}")
            
    except Exception as e:
        print(f"Auth or Connection Failed: {e}")

if __name__ == "__main__":
    print("Run `go run usecase5_auth_ws.go` in another terminal first.")
    # asyncio.run(auth_via_first_frame())
