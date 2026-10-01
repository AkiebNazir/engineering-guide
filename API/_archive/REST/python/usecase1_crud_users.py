from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class User(BaseModel):
    id: str
    name: str

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    return User(id=user_id, name="Alice")

@app.post("/users", status_code=201)
async def create_user(user: User):
    return {"status": "created", "user": user}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
