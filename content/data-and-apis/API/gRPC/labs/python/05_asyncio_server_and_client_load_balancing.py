"""
LAB 05 (advanced) - grpc.aio concurrency and client-side load balancing
=======================================================================
You will learn
  * SYNC server: one THREAD per in-flight call. 4 workers + 20 slow calls = they queue up.
    ASYNC server (grpc.aio): one asyncio task per call, thousands of slow I/O-bound calls on one thread.
    Measured below.
  * WHY load balancing is special in gRPC:
        an L4 load balancer balances CONNECTIONS. gRPC keeps ONE long-lived HTTP/2 connection and
        multiplexes every call over it, so all traffic lands on ONE backend.
    Solutions:  (1) client-side balancing (this lab)  (2) an L7 / gRPC-aware proxy (Envoy, Linkerd)
  * client-side balancing with a service config:  pick_first (default)  vs  round_robin
  * what happens when a backend dies: the channel notices and re-spreads traffic

Needs   pip install grpcio grpcio-tools protobuf   (stubs: shop_pb2*.py made by ../generate.sh)
Run it  python 05_asyncio_server_and_client_load_balancing.py
"""
import asyncio
import collections
import json
import time
from concurrent import futures

import grpc
import grpc.aio

import shop_pb2 as pb
import shop_pb2_grpc as rpc


# ---------------------------------------------------- async server: I/O bound --
class AsyncCatalog(rpc.CatalogServicer):
    async def GetProduct(self, request, context):
        await asyncio.sleep(0.2)                       # pretend: a database / HTTP call (yields the event loop)
        return pb.Product(id=request.id, name="async")


class SyncCatalog(rpc.CatalogServicer):
    def GetProduct(self, request, context):
        time.sleep(0.2)                                   # the same "database call", but it BLOCKS a thread
        return pb.Product(id=request.id, name="sync")


# ------------------------------------------ labelled backends for load balancing --
class NamedBackend(rpc.CatalogServicer):
    def __init__(self, name: str):
        self.name = name

    def GetProduct(self, request, context):
        return pb.Product(id=request.id, name=self.name)


async def start_aio(servicer) -> tuple[grpc.aio.Server, int]:
    server = grpc.aio.server()
    rpc.add_CatalogServicer_to_server(servicer, server)
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()
    return server, port


async def main():
    print("== 1. sync (4 threads) vs asyncio, 20 concurrent slow calls of 0.2s each ==")
    sync_server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_CatalogServicer_to_server(SyncCatalog(), sync_server)
    sync_port = sync_server.add_insecure_port("127.0.0.1:0")
    sync_server.start()
    aio_server, aio_port = await start_aio(AsyncCatalog())

    async def burst(port: int) -> float:
        async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as ch:
            stub = rpc.CatalogStub(ch)
            start = time.perf_counter()
            await asyncio.gather(*[stub.GetProduct(pb.GetProductRequest(id=i), timeout=10) for i in range(20)])
            return time.perf_counter() - start

    t_sync, t_aio = await burst(sync_port), await burst(aio_port)
    print(f"  sync  server, 4 workers : {t_sync:.2f}s   (20 calls / 4 threads x 0.2s = 5 rounds)")
    print(f"  aio   server, 1 thread  : {t_aio:.2f}s   (all 20 waiting concurrently)")
    assert t_sync > 0.9 and t_aio < 0.6
    sync_server.stop(0)

    print("\n== 2. three backends, called through ONE channel ==")
    backends = []
    for name in ("A", "B", "C"):
        server, port = await start_aio(NamedBackend(name))
        backends.append((name, server, port))
    target = "ipv4:" + ",".join(f"127.0.0.1:{p}" for _, _, p in backends)

    async def distribution(service_config: dict | None, calls: int = 30, channel=None) -> collections.Counter:
        options = [("grpc.service_config", json.dumps(service_config))] if service_config else []
        async with grpc.aio.insecure_channel(target, options=options) as ch:
            stub = rpc.CatalogStub(ch)
            seen = collections.Counter()
            for i in range(calls):
                seen[(await stub.GetProduct(pb.GetProductRequest(id=i), timeout=2, wait_for_ready=True)).name] += 1
            return seen

    pick_first = await distribution(None)
    print("  default (pick_first)   :", dict(pick_first), " <- ALL calls stuck to one backend")
    assert len(pick_first) == 1

    round_robin = await distribution({"loadBalancingConfig": [{"round_robin": {}}]})
    print("  round_robin            :", dict(sorted(round_robin.items())), " <- spread across ALL three (about 10 each)")
    assert set(round_robin) == {"A", "B", "C"} and all(6 <= v <= 14 for v in round_robin.values())   # ~10 each; exact split depends on connect timing

    print("\n== 3. a backend dies mid-flight ==")
    async with grpc.aio.insecure_channel(target, options=[
            ("grpc.service_config", json.dumps({"loadBalancingConfig": [{"round_robin": {}}]}))]) as ch:
        stub = rpc.CatalogStub(ch)
        for i in range(6):                                              # warm all three subchannels
            await stub.GetProduct(pb.GetProductRequest(id=i), timeout=2, wait_for_ready=True)
        await backends[1][1].stop(0)                                    # kill B
        await asyncio.sleep(0.3)                                        # let the channel notice
        after = collections.Counter()
        for i in range(20):
            try:
                after[(await stub.GetProduct(pb.GetProductRequest(id=i), timeout=2)).name] += 1
            except grpc.aio.AioRpcError as e:
                after[e.code().name] += 1
        print("  after B died:", dict(sorted(after.items())))
        assert "B" not in after and after["A"] + after["C"] >= 18

    for name, server, _ in backends:
        await server.stop(0)
    await aio_server.stop(0)
    await asyncio.sleep(0.3)          # let grpc's background threads finish before the event loop closes
    print("\nOK")


if __name__ == "__main__":
    asyncio.run(main())
