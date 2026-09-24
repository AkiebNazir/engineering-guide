import asyncio

async def consume_market_data(ticker: str):
    print(f"Subscribing to market data for {ticker}...")
    # async with grpc.aio.insecure_channel('localhost:50051') as channel:
    #     stub = api_pb2_grpc.MicroserviceSystemStub(channel)
    #     request = api_pb2.MarketRequest(ticker_symbol=ticker)
    #     async for update in stub.WatchMarketData(request):
    
    # Mocking the async generator
    for i in range(5):
        print(f"[Timestamp] {ticker} - ${150.0 + i:.2f}")
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(consume_market_data("AAPL"))
