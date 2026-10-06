"""
LAB 02 (basic) - FastAPI: validation, status codes and free OpenAPI docs
=========================================================================
You will learn
  * declaring the contract once (Pydantic models) and getting validation + docs for free
  * 422 automatic validation errors vs your own 404/409 business errors
  * response_model: what the client sees is NOT what is stored (never leak password_hash)
  * the machine-readable OpenAPI document served at /openapi.json (and Swagger UI at /docs)

Needs         pip install fastapi httpx uvicorn
Run it        python 02_fastapi_validation_openapi.py
Keep serving  python 02_fastapi_validation_openapi.py --serve   (open http://localhost:8000/docs)
"""
import sys

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI(title="Users API", version="1.0.0")


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)
    age: int | None = Field(default=None, ge=0, le=150)


class UserOut(BaseModel):                 # what we RETURN: no password
    id: int
    name: str
    email: str
    age: int | None = None


DB: dict[int, dict] = {}


@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(user: UserCreate, response: Response):
    if any(u["email"] == user.email for u in DB.values()):
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")   # business rule
    uid = len(DB) + 1
    DB[uid] = {"id": uid, **user.model_dump(), "password_hash": f"hash({user.password})"}
    response.headers["Location"] = f"/users/{uid}"
    return DB[uid]                        # response_model filters password_hash out


@app.get("/users/{user_id}", response_model=UserOut, tags=["users"])
def get_user(user_id: int):               # a non-integer id gives 422 automatically
    if user_id not in DB:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return DB[user_id]


@app.get("/users", response_model=list[UserOut], tags=["users"])
def list_users(min_age: int | None = None, limit: int = Query(20, le=100)):
    rows = [u for u in DB.values() if min_age is None or (u["age"] or 0) >= min_age]
    return rows[:limit]


def demo():
    c = TestClient(app)
    good = {"name": "Ana", "email": "ana@x.io", "password": "s3cretpass", "age": 30}

    r = c.post("/users", json=good)
    print("create           ->", r.status_code, r.headers["location"], r.json())
    assert r.status_code == 201 and "password" not in r.json() and "password_hash" not in r.json()

    r = c.post("/users", json=good)
    print("duplicate email  ->", r.status_code, r.json())
    assert r.status_code == 409

    r = c.post("/users", json={"name": "A", "email": "nope", "password": "123"})
    print("bad payload      ->", r.status_code)
    for err in r.json()["detail"]:
        print("     ", err["loc"], "-", err["msg"])
    assert r.status_code == 422 and len(r.json()["detail"]) == 3

    assert c.get("/users/1").status_code == 200
    assert c.get("/users/99").status_code == 404
    assert c.get("/users/abc").status_code == 422          # path param is typed

    spec = c.get("/openapi.json").json()
    print("OpenAPI paths    ->", sorted(spec["paths"]))
    print("UserCreate schema->", spec["components"]["schemas"]["UserCreate"]["required"])
    assert "/users/{user_id}" in spec["paths"]
    print("OK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000)
    else:
        demo()
