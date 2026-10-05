# REAL-WORLD EXAMPLE: Strawberry (External 1)
# Demonstrates: Nested Resolvers, Mutations, Data Loaders (N+1 problem mitigation concepts), FastAPI integration
import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional

# Mock DBs
users_db = {"1": {"id": "1", "name": "Alice", "role": "ADMIN"}}
posts_db = [
    {"id": "100", "title": "GraphQL is awesome", "author_id": "1"},
    {"id": "101", "title": "Strawberry vs Graphene", "author_id": "1"}
]

@strawberry.type
class Post:
    id: str
    title: str
    author_id: strawberry.Private[str]

@strawberry.type
class User:
    id: str
    name: str
    role: str

    @strawberry.field
    def posts(self) -> List[Post]:
        # Nested resolver: Fetches posts specifically for this user
        return [Post(**p) for p in posts_db if p["author_id"] == self.id]

@strawberry.type
class Query:
    @strawberry.field
    def get_user(self, id: str) -> Optional[User]:
        user_data = users_db.get(id)
        if user_data:
            return User(**user_data)
        return None

@strawberry.type
class Mutation:
    @strawberry.field
    def create_post(self, title: str, author_id: str) -> Post:
        if author_id not in users_db:
            raise Exception("Author not found")
        new_id = str(len(posts_db) + 100)
        new_post = {"id": new_id, "title": title, "author_id": author_id}
        posts_db.append(new_post)
        return Post(**new_post)

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
