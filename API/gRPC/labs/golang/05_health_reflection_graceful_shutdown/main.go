/*
LAB 05 (advanced) - Operating a gRPC server: health checks, reflection, keepalive, graceful shutdown
=====================================================================================================
You will learn

  - the STANDARD health protocol (grpc.health.v1): load balancers and Kubernetes probes use it.
    Check  = one-shot status         Watch = a stream of status CHANGES
    per-service status: "" is the whole server, "shop.v1.Catalog" a single service

  - server REFLECTION: the server describes its own services, so tools like grpcurl work without
    the .proto file. You will write the client side: list services, then read the method list.

  - keepalive and idle connections: MaxConnectionIdle closes unused connections; the client
    channel goes IDLE and silently reconnects on the next call

  - GRACEFUL SHUTDOWN, the production recipe:

    1. health -> NOT_SERVING       load balancers stop routing NEW calls here
    2. GracefulStop()              refuse new calls, let in-flight calls FINISH
    3. timeout? -> Stop()          force-close whatever is still running (a stuck stream)

Try after the lab:  grpcurl -plaintext localhost:PORT list     (if you change the lab to -serve)

Run it   go run ./gRPC/labs/golang/05_health_reflection_graceful_shutdown
*/
package main

import (
	"context"
	"fmt"
	"io"
	"net"
	"sort"
	"sync"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/connectivity"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/health"
	healthpb "google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/reflection"
	reflectionpb "google.golang.org/grpc/reflection/grpc_reflection_v1"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/descriptorpb"

	"dsapractice/api/gRPC/labs/golang/shoppb"
)

type server struct {
	shoppb.UnimplementedCatalogServer
	started chan struct{}
}

func (s *server) GetProduct(ctx context.Context, r *shoppb.GetProductRequest) (*shoppb.Product, error) {
	return &shoppb.Product{Id: r.Id, Name: "Keyboard"}, nil
}

// A stream that takes `limit` x 100ms - used to have a call "in flight" during shutdown.
func (s *server) ListProducts(r *shoppb.ListProductsRequest, st shoppb.Catalog_ListProductsServer) error {
	select {
	case s.started <- struct{}{}:
	default:
	}
	for i := int64(1); i <= int64(r.Limit); i++ {
		time.Sleep(100 * time.Millisecond)
		if err := st.Send(&shoppb.Product{Id: i, Name: "item"}); err != nil {
			return err
		}
	}
	return nil
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func newServer() (*grpc.Server, *health.Server, *server, string) {
	lis, _ := net.Listen("tcp", "127.0.0.1:0")
	s := grpc.NewServer(
		grpc.KeepaliveParams(keepalive.ServerParameters{
			MaxConnectionIdle: 400 * time.Millisecond, // close connections that carry no calls (demo value!)
			Time:              30 * time.Second,       // ping an idle client every 30s to detect dead peers
			Timeout:           5 * time.Second,        // ... and give up if it does not answer in 5s
		}),
		grpc.KeepaliveEnforcementPolicy(keepalive.EnforcementPolicy{MinTime: 10 * time.Second}), // reject clients that ping too often
	)
	impl := &server{started: make(chan struct{}, 1)}
	shoppb.RegisterCatalogServer(s, impl)

	h := health.NewServer() // implements grpc.health.v1.Health
	healthpb.RegisterHealthServer(s, h)
	h.SetServingStatus("shop.v1.Catalog", healthpb.HealthCheckResponse_SERVING)

	reflection.Register(s) // registers reflection v1 and v1alpha
	go s.Serve(lis)
	return s, h, impl, lis.Addr().String()
}

func dial(addr string) *grpc.ClientConn {
	conn, err := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		panic(err)
	}
	return conn
}

func main() {
	s, hs, impl, addr := newServer()
	conn := dial(addr)
	defer conn.Close()
	ctx := context.Background()

	fmt.Println("== 1. health: Check and Watch ==")
	hc := healthpb.NewHealthClient(conn)
	r, _ := hc.Check(ctx, &healthpb.HealthCheckRequest{Service: "shop.v1.Catalog"})
	fmt.Println("  Check(shop.v1.Catalog) ->", r.Status)
	_, err := hc.Check(ctx, &healthpb.HealthCheckRequest{Service: "no.such.Service"})
	fmt.Println("  Check(unknown service) ->", status.Code(err), "(a probe treats this as failed)")
	must(status.Code(err) == codes.NotFound, "unknown service")

	wctx, cancelWatch := context.WithCancel(ctx)
	watch, _ := hc.Watch(wctx, &healthpb.HealthCheckRequest{Service: "shop.v1.Catalog"})
	var statuses []string
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		for {
			m, err := watch.Recv()
			if err != nil {
				return
			}
			statuses = append(statuses, m.Status.String())
		}
	}()
	time.Sleep(100 * time.Millisecond)
	hs.SetServingStatus("shop.v1.Catalog", healthpb.HealthCheckResponse_NOT_SERVING) // e.g. database lost
	time.Sleep(100 * time.Millisecond)
	hs.SetServingStatus("shop.v1.Catalog", healthpb.HealthCheckResponse_SERVING)
	time.Sleep(100 * time.Millisecond)
	cancelWatch()
	wg.Wait()
	fmt.Println("  Watch saw the transitions:", statuses)
	must(len(statuses) == 3 && statuses[1] == "NOT_SERVING", "watch stream")

	fmt.Println("\n== 2. reflection: a client that knows NOTHING about shop.proto ==")
	rc := reflectionpb.NewServerReflectionClient(conn)
	stream, _ := rc.ServerReflectionInfo(ctx)
	stream.Send(&reflectionpb.ServerReflectionRequest{MessageRequest: &reflectionpb.ServerReflectionRequest_ListServices{}})
	resp, _ := stream.Recv()
	var services []string
	for _, sv := range resp.GetListServicesResponse().GetService() {
		services = append(services, sv.Name)
	}
	sort.Strings(services)
	fmt.Println("  services:", services)
	must(len(services) >= 2, "list services")

	stream.Send(&reflectionpb.ServerReflectionRequest{MessageRequest: &reflectionpb.ServerReflectionRequest_FileContainingSymbol{FileContainingSymbol: "shop.v1.Catalog"}})
	resp, _ = stream.Recv()
	for _, raw := range resp.GetFileDescriptorResponse().GetFileDescriptorProto() {
		var fd descriptorpb.FileDescriptorProto
		proto.Unmarshal(raw, &fd)
		for _, svc := range fd.GetService() {
			if svc.GetName() != "Catalog" {
				continue
			}
			for _, m := range svc.GetMethod() {
				kind := "unary"
				switch {
				case m.GetClientStreaming() && m.GetServerStreaming():
					kind = "bidi stream"
				case m.GetServerStreaming():
					kind = "server stream"
				case m.GetClientStreaming():
					kind = "client stream"
				}
				fmt.Printf("  shop.v1.Catalog/%-14s %-14s %s -> %s\n", m.GetName(), kind, m.GetInputType(), m.GetOutputType())
			}
		}
	}
	stream.CloseSend()
	fmt.Println("  (this is exactly how `grpcurl -plaintext host:port describe shop.v1.Catalog` works)")

	fmt.Println("\n== 3. idle connections ==")
	client := shoppb.NewCatalogClient(conn)
	client.GetProduct(ctx, &shoppb.GetProductRequest{Id: 1})
	fmt.Println("  after a call          :", conn.GetState())
	time.Sleep(900 * time.Millisecond) // server's MaxConnectionIdle=400ms closes the connection
	conn.Connect()
	deadline := time.Now().Add(time.Second)
	for conn.GetState() != connectivity.Idle && time.Now().Before(deadline) {
		wctx, c := context.WithTimeout(ctx, 100*time.Millisecond)
		conn.WaitForStateChange(wctx, conn.GetState())
		c()
	}
	fmt.Println("  after 900ms of silence:", conn.GetState(), "(server closed the idle connection)")
	_, err = client.GetProduct(ctx, &shoppb.GetProductRequest{Id: 1}) // transparently reconnects
	fmt.Println("  next call after idle  :", status.Code(err), "(the channel reconnected by itself)")
	must(err == nil, "reconnect")

	fmt.Println("\n== 4. graceful shutdown with a call in flight ==")
	ls, _ := client.ListProducts(ctx, &shoppb.ListProductsRequest{Limit: 6}) // takes ~600ms
	<-impl.started
	go func() {
		time.Sleep(50 * time.Millisecond)
		hs.Shutdown() // step 1: mark every service NOT_SERVING so load balancers drain us
		fmt.Println("  [server] health -> NOT_SERVING, calling GracefulStop()")
		s.GracefulStop() // step 2: stop accepting new work, wait for existing calls
	}()
	got := 0
	for {
		if _, err := ls.Recv(); err != nil {
			fmt.Printf("  in-flight stream delivered %d/6 messages, ended with: %v\n", got, err == io.EOF)
			must(err == io.EOF && got == 6, "in-flight call completed despite shutdown")
			break
		}
		got++
	}
	time.Sleep(100 * time.Millisecond)
	_, err = client.GetProduct(ctx, &shoppb.GetProductRequest{Id: 1})
	fmt.Println("  NEW call after shutdown:", status.Code(err))
	must(status.Code(err) == codes.Unavailable, "new calls refused")

	fmt.Println("\n== 5. the timeout fallback: a stuck stream must not block shutdown forever ==")
	s2, _, impl2, addr2 := newServer()
	conn2 := dial(addr2)
	defer conn2.Close()
	stuck, _ := shoppb.NewCatalogClient(conn2).ListProducts(ctx, &shoppb.ListProductsRequest{Limit: 1000}) // ~100s
	<-impl2.started
	done := make(chan struct{})
	go func() { s2.GracefulStop(); close(done) }()
	select {
	case <-done:
		panic("FAILED: graceful stop should still be waiting for the stuck stream")
	case <-time.After(300 * time.Millisecond):
		fmt.Println("  GracefulStop still waiting after 300ms (the stream never ends) -> force Stop()")
		s2.Stop()
	}
	<-done
	for { // a few messages may already be buffered on the client; the error follows them
		if _, err = stuck.Recv(); err != nil {
			break
		}
	}
	fmt.Println("  the stuck client sees:", status.Code(err))
	must(err != nil, "stuck stream terminated")
	fmt.Println("\nOK")
}
