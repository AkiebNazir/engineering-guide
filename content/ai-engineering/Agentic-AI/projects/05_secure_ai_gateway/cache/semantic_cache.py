"""
Python gRPC Server for Semantic Caching.
Requires: pip install grpcio grpcio-tools chromadb sentence-transformers
To generate proto: python -m grpc_tools.protoc -I../proto --python_out=. --grpc_python_out=. ../proto/cache.proto
"""
import time
import uuid
import grpc
from concurrent import futures
import chromadb
from sentence_transformers import SentenceTransformer

# Note: In a real environment, you generate cache_pb2 and cache_pb2_grpc from the proto file.
# We are mocking the imports here for structural demonstration.
try:
    import cache_pb2
    import cache_pb2_grpc
    HAS_PROTO = True
except ImportError:
    HAS_PROTO = False
    print("Warning: Proto files not compiled. Run protoc.")

class SemanticCacheServicer:
    def __init__(self, threshold=0.15):
        self.threshold = threshold
        print("Loading Embedding Model...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        print("Initializing ChromaDB...")
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(name="semantic_cache")

    def CheckCache(self, request, context):
        if not HAS_PROTO: return None
        
        prompt = request.prompt
        query_embedding = self.encoder.encode(prompt).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=1
        )
        
        if results['distances'] and len(results['distances'][0]) > 0:
            distance = results['distances'][0][0]
            if distance < self.threshold:
                return cache_pb2.CacheResponse(
                    hit=True,
                    cached_response=results['metadatas'][0][0]['response'],
                    similarity_score=1.0 - distance
                )
                
        return cache_pb2.CacheResponse(hit=False, cached_response="", similarity_score=0.0)

    def SetCache(self, request, context):
        if not HAS_PROTO: return None
        
        prompt = request.prompt
        response = request.response
        embedding = self.encoder.encode(prompt).tolist()
        doc_id = str(uuid.uuid4())
        
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[prompt],
            metadatas=[{"response": response}]
        )
        return cache_pb2.SetCacheResponse(success=True)

def serve():
    if not HAS_PROTO:
        print("Skipping server start. Compile protos first.")
        return
        
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cache_pb2_grpc.add_SemanticCacheServiceServicer_to_server(SemanticCacheServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Semantic Cache gRPC Server running on port 50051...")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
