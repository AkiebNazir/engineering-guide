package main

import (
	"context"
	"log"
	"time"
)

type MarketRequest struct { TickerSymbol string }
type MarketData struct { Symbol string; Price float64; Timestamp int64 }

type pbWatchMarketDataServer interface {
	Send(*MarketData) error
	Context() context.Context
}

type server struct{}

func (s *server) WatchMarketData(req *MarketRequest, stream pbWatchMarketDataServer) error {
	ticker := req.TickerSymbol
	log.Printf("Client subscribed to %s", ticker)
	
	for i := 0; i < 10; i++ {
		if stream.Context().Err() != nil {
			return stream.Context().Err()
		}
		
		priceUpdate := &MarketData{
			Symbol: ticker,
			Price:  150.00 + float64(i),
			Timestamp: time.Now().Unix(),
		}
		
		if err := stream.Send(priceUpdate); err != nil {
			return err
		}
		time.Sleep(1 * time.Second)
	}
	return nil
}

func main() {}
