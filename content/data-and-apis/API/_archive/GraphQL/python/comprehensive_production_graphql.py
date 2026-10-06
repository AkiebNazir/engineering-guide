import strawberry
from fastapi import FastAPI, Depends, HTTPException, Request
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional

# --- Mock Database ---
users_db = {
    "u1": {"id": "u1", "name": "Alice", "email": "alice@example.com"},
    "u2": {"id": "u2", "name": "Bob", "email": "bob@example.com"},
}

posts_db = {
    "p1": {"id": "p1", "title": "GraphQL with Strawberry", "author_id": "u1"},
    "p2": {"id": "p2", "title": "FastAPI integration", "author_id": "u2"},
}

# --- Context & Authentication Dependency ---
def get_current_user(request: Request):
    """
    FastAPI dependency to extract the token from headers.
    This injects the user context into Strawberry GraphQL resolvers.
    """
    token = request.headers.get("Authorization")
    if token == "Bearer admin-token":
        return "u1"
    return None

async def get_context(current_user: Optional[str] = Depends(get_current_user)):
    return {"user_id": current_user}

# --- GraphQL Types ---
@strawberry.type
class User:
    id: str
    name: str
    email: str

@strawberry.type
class Post:
    id: str
    title: str
    author_id: strawberry.Private[str] # Private field, not exposed in API

    # Nested Resolver: Resolves the author relationship dynamically
    @strawberry.field
    def author(self) -> User:
        user_data = users_db.get(self.author_id)
        if not user_data:
            raise Exception("Author not found")
        return User(**user_data)

# --- Queries (Reads) ---
@strawberry.type
class Query:
    
    # Simple query returning a list
    @strawberry.field
    def all_posts(self) -> List[Post]:
        return [Post(**data) for data in posts_db.values()]

    # Query with arguments
    @strawberry.field
    def post_by_id(self, id: str) -> Optional[Post]:
        data = posts_db.get(id)
        if data:
            return Post(**data)
        return None

# --- Mutations (Writes) ---
@strawberry.type
class Mutation:
    
    @strawberry.mutation
    def create_post(self, info: strawberry.Info, title: str) -> Post:
        # Access the context (Injected by FastAPI dependencies)
        user_id = info.context.get("user_id")
        
        if not user_id:
            raise Exception("Unauthorized: Missing or invalid token")
            
        new_id = f"p{len(posts_db) + 1}"
        new_post_data = {"id": new_id, "title": title, "author_id": user_id}
        posts_db[new_id] = new_post_data
        
        return Post(**new_post_data)

# --- Schema & FastAPI Integration ---
schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context # Binds FastAPI auth to Strawberry context
)

app = FastAPI(title="Production GraphQL API")
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    import uvicorn
    print("Run with: uvicorn comprehensive_production_graphql:app --reload")
    # uvicorn.run(app, host="0.0.0.0", port=8000)
