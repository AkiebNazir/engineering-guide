import asyncio
from typing import List
import strawberry
from strawberry.dataloader import DataLoader

# Simulated batch database query
async def load_posts_for_users(keys: List[str]) -> List[List[str]]:
    print(f"Executing Batch DB Query for keys: {keys}")
    # SELECT * FROM posts WHERE user_id IN keys
    mock_db = {
        "user1": ["Post A", "Post B"],
        "user2": ["Post C"]
    }
    return [mock_db.get(key, []) for key in keys]

post_loader = DataLoader(load_fn=load_posts_for_users)

@strawberry.type
class User:
    id: str
    
    @strawberry.field
    async def posts(self) -> List[str]:
        # Enqueues the request. Loader waits a tick, batches keys, and executes load_posts_for_users
        return await post_loader.load(self.id)

@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> List[User]:
        return [User(id="user1"), User(id="user2")]

schema = strawberry.Schema(query=Query)

async def run_query():
    query = """
        query {
            users {
                id
                posts
            }
        }
    """
    result = await schema.execute(query)
    print("Query Result:", result.data)

if __name__ == "__main__":
    asyncio.run(run_query())
