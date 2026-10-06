import asyncio
import grpc

class MockAuthResponse:
    def __init__(self, is_valid, user_id):
        self.is_valid = is_valid
        self.user_id = user_id

async def validate_user_token(token: str):
    print(f"Connecting to grpc server to validate {token}")
    # async with grpc.aio.insecure_channel('localhost:50051') as channel:
    #     stub = api_pb2_grpc.MicroserviceSystemStub(channel)
    #     response = await stub.ValidateToken(api_pb2.AuthRequest(token=token))
    
    # Mocking execution for snippet validity
    response = MockAuthResponse(True, "usr_123")
    print(f"Auth Result: Valid={response.is_valid}, UserID={response.user_id}")
    return response.is_valid

if __name__ == '__main__':
    asyncio.run(validate_user_token("secret-jwt"))
