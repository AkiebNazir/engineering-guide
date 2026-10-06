import httpx
import asyncio

async def fetch_feed():
    async with httpx.AsyncClient() as client:
        params = {"_limit": 10, "_start": 0}
        
        response = await client.get("https://jsonplaceholder.typicode.com/posts", params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Fetched {len(data)} paginated posts.")

if __name__ == "__main__":
    asyncio.run(fetch_feed())
