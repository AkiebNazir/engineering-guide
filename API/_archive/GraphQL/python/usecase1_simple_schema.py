import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import uvicorn

@strawberry.type
class User:
    id: str
    name: str

@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: str) -> User:
        return User(id=id, name="Alice")

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    print("Run using: uvicorn usecase1_simple_schema:app --reload")
    # uvicorn.run(app, host="0.0.0.0", port=8000)
