from fastapi import FastAPI, Body
import uvicorn

app = FastAPI()

@app.patch("/users/{user_id}")
async def update_user(user_id: str, payload: dict = Body(...)):
    # payload will only contain fields the client explicitly sent
    print(f"Applying updates to {user_id}: {payload}")
    return {"status": "updated", "data": payload}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
