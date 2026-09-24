# REAL-WORLD EXAMPLE: grpcio (External 1)
# Demonstrates: Interceptors (Middleware for Auth/Logging), Error Handling, ThreadPools
import grpc
from concurrent import futures
import time

# Mock generated code imports (Assume python -m grpc_tools.protoc was run)
# import user_pb2
# import user_pb2_grpc

class MockUser:
    def __init__(self, name):
        self.name = name

class MockResponse:
    def __init__(self, user):
        self.user = user

class MockContext:
    def abort(self, code, details):
        raise Exception(f"gRPC Abort {code}: {details}")

# 1. Interceptor (Middleware)
class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        print(f"[{time.time()}] Calling: {handler_call_details.method}")
        # Could also check handler_call_details.invocation_metadata for Auth tokens here
        return continuation(handler_call_details)

# 2. Servicer Implementation
class UserService: # would inherit from user_pb2_grpc.UserServiceServicer
    def GetUser(self, request, context):
        if request.id == "1":
            return MockResponse(user=MockUser(name="Alice"))
        
        # Proper gRPC Error Handling
        context.abort(grpc.StatusCode.NOT_FOUND, "User not found in database")

def serve():
    # 3. Server Initialization with ThreadPool and Interceptors
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=(LoggingInterceptor(),)
    )
    # user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port("[::]:50051")
    print("gRPC Server running on :50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
