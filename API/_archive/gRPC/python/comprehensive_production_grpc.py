import asyncio
import grpc

# Conceptually assuming pb2 and pb2_grpc are generated

class MyServiceServicer:
    # 1. Unary RPC
    async def ProcessData(self, request, context: grpc.aio.ServicerContext):
        # Validation
        if not request.field:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("field is required")
            return None
            
        try:
            # Simulate work respecting client deadlines
            await asyncio.wait_for(asyncio.sleep(2), timeout=context.time_remaining())
            return None # Return Response object
        except asyncio.TimeoutError:
            context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, "Time expired")

    # 2. Bidirectional Streaming RPC
    async def RealtimeChat(self, request_iterator, context: grpc.aio.ServicerContext):
        async for request in request_iterator:
            yield None # Yield Response objects

# --- Middleware (Interceptor) ---
class AuthInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)
        
        token = metadata.get("authorization")
        if token != "Bearer secret-jwt":
            return grpc.rpc_method_handlers.unary_unary(
                lambda r, c: c.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid token")
            )
            
        # Continue to actual handler
        return await continuation(handler_call_details)

async def serve():
    server = grpc.aio.server(interceptors=(AuthInterceptor(),))
    # pb2_grpc.add_MyServiceServicer_to_server(MyServiceServicer(), server)
    
    server.add_insecure_port('[::]:50051')
    print("gRPC Production Server starting on port 50051")
    
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    # asyncio.run(serve())
    pass
