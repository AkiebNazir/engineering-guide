import asyncio
from typing import AsyncGenerator
import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

# --- GraphQL Subscriptions ---

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def stock_price_updates(self, symbol: str) -> AsyncGenerator[float, None]:
        """
        A WebSocket subscription that streams live data back to the client.
        """
        print(f"Client subscribed to {symbol}")
        current_price = 150.0
        
        try:
            # Infinite loop streaming data
            while True:
                # In a real app, this waits for a Redis Pub/Sub message
                await asyncio.sleep(1)
                current_price += 0.5
                
                # Yield sends the data packet over the WebSocket
                yield current_price
        except asyncio.CancelledError:
            print(f"Client unsubscribed from {symbol}")


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello world!"

# --- FastAPI Integration ---

schema = strawberry.Schema(query=Query, subscription=Subscription)

# The GraphQLRouter automatically provisions a WebSocket endpoint for subscriptions
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    import uvicorn
    print("Run with: uvicorn subscriptions:app --reload")
    # uvicorn.run(app, host="0.0.0.0", port=8000)
