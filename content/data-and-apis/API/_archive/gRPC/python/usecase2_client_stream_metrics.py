import asyncio
import random

class MockMetric:
    def __init__(self, service_id, cpu_usage, mem_usage):
        self.service_id = service_id
        self.cpu_usage = cpu_usage
        self.mem_usage = mem_usage

async def generate_metrics(service_id: str):
    for _ in range(5):
        yield MockMetric(
            service_id=service_id, 
            cpu_usage=random.uniform(10.0, 90.0), 
            mem_usage=random.uniform(50.0, 512.0)
        )
        await asyncio.sleep(0.5)

async def stream_telemetry():
    print("Streaming metrics to gRPC server...")
    # async with grpc.aio.insecure_channel('localhost:50051') as channel:
    #     stub = api_pb2_grpc.MicroserviceSystemStub(channel)
    #     summary = await stub.StreamMetrics(generate_metrics("worker-python-1"))
    
    async for metric in generate_metrics("worker-python-1"):
        print(f"Sent: CPU={metric.cpu_usage:.1f}%")
        
if __name__ == '__main__':
    asyncio.run(stream_telemetry())
