import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
import uvicorn

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        # Room -> Set of WebSockets
        self.rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, token: str):
        if token != "secret-jwt":
            await websocket.close(code=1008) # Policy Violation
            raise HTTPException(status_code=403, detail="Invalid Token")
        
        await websocket.accept()

    def disconnect(self, websocket: WebSocket):
        for room_name, clients in self.rooms.items():
            if websocket in clients:
                clients.remove(websocket)

    async def join_room(self, websocket: WebSocket, room: str):
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)
        await websocket.send_text(f"Joined room: {room}")

    async def broadcast_to_room(self, room: str, message: str, sender: WebSocket):
        if room in self.rooms:
            for client in self.rooms[room]:
                if client != sender:
                    await client.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    await manager.connect(websocket, token)
    
    try:
        while True:
            # receive_text automatically handles Ping/Pong under the hood in FastAPI
            data = await websocket.receive_text()
            
            try:
                payload = json.loads(data)
                action = payload.get("action")
                
                if action == "join_room":
                    await manager.join_room(websocket, payload.get("room"))
                elif action == "send_message":
                    await manager.broadcast_to_room(
                        payload.get("room"), 
                        payload.get("message"), 
                        websocket
                    )
            except json.JSONDecodeError:
                await websocket.send_text("Error: Invalid JSON payload")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")

if __name__ == "__main__":
    print("Run with: uvicorn comprehensive_production_ws:app --reload")
