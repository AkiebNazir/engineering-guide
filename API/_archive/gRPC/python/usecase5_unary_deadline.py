import asyncio
import grpc

async def dispatch_task(task_id: str):
    print(f"Dispatching task {task_id} with a 2.0s strict deadline...")
    try:
        # async with grpc.aio.insecure_channel('localhost:50051') as channel:
        #     stub = api_pb2_grpc.MicroserviceSystemStub(channel)
        #     response = await stub.ProcessTask(
        #         api_pb2.Task(task_id=task_id, payload="image_bytes"),
        #         timeout=2.0 
        #     )
        
        # Simulate deadline exceeded behavior
        await asyncio.sleep(2.0)
        raise Exception("grpc.StatusCode.DEADLINE_EXCEEDED")
    except Exception as e:
        print(f"Task {task_id} failed: Deadline Exceeded. Server took too long. ({e})")

if __name__ == '__main__':
    asyncio.run(dispatch_task("tsk_99"))
