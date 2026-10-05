import asyncio
from typing import AsyncGenerator
import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Query:
    @strawberry.field
    def dummy(self) -> str:
        return "ok"

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 5) -> AsyncGenerator[int, None]:
        print(f"Client subscribed to count up to {target}")
        for i in range(1, target + 1):
            yield i
            await asyncio.sleep(1)

schema = strawberry.Schema(query=Query, subscription=Subscription)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    print("Run using: uvicorn usecase5_subscriptions:app --reload")
    # You can connect to ws://localhost:8000/graphql to test subscriptions
