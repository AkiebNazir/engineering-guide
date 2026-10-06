import strawberry
import httpx
import asyncio

@strawberry.type
class User:
    id: int
    name: str

@strawberry.type
class Query:
    @strawberry.field
    async def legacy_user(self, id: str) -> User:
        # GraphQL acting as an API Gateway to a REST endpoint
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://jsonplaceholder.typicode.com/users/{id}")
            data = resp.json()
            return User(id=data["id"], name=data["name"])

schema = strawberry.Schema(query=Query)

async def fetch_gateway():
    query = """
        query {
            legacyUser(id: "1") {
                id
                name
            }
        }
    """
    result = await schema.execute(query)
    print("Gateway Result fetching from REST:", result.data)

if __name__ == "__main__":
    asyncio.run(fetch_gateway())
