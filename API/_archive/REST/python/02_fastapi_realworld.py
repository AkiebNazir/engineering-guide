# REAL-WORLD EXAMPLE: FastAPI (External 1)
# Demonstrates: Dependency Injection, Pydantic Validation, Bearer Auth, HTTP Exceptions
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import List, Dict

app = FastAPI(title="E-Commerce API", version="1.0.0")

# Mock Database
users_db: Dict[str, dict] = {}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr

def get_current_user(token: str = Depends(oauth2_scheme)):
    if token != "supersecrettoken":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user_id": "admin"}

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    if any(u["email"] == user.email for u in users_db.values()):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(len(users_db) + 1)
    # Never store raw passwords in production! (Use Passlib/Bcrypt)
    user_dict = {"id": user_id, "name": user.name, "email": user.email, "hashed_password": user.password + "_hash"}
    users_db[user_id] = user_dict
    
    return user_dict

@app.get("/users/me", response_model=Dict[str, str])
def read_users_me(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['user_id']}, you have access!"}

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
