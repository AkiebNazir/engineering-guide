import grpc
from concurrent import futures
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())
grpc_server_instrumentor = GrpcInstrumentorServer()
grpc_server_instrumentor.instrument()

class GreeterServicer:
    def SayHello(self, request, context):
        return {"message": f"Hello, {request.name}!"}

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
