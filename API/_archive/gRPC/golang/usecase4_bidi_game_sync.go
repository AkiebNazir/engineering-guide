package main

import (
	"io"
	"log"
)

type PlayerState struct { PlayerId string; X float32; Y float32 }
type GameState struct { ActivePlayers int32; GlobalEvent string }

type pbGameSyncServer interface {
	Recv() (*PlayerState, error)
	Send(*GameState) error
}

type server struct{}

func (s *server) GameSync(stream pbGameSyncServer) error {
	for {
		playerState, err := stream.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
		
		log.Printf("Player %s moved to X:%f Y:%f", playerState.PlayerId, playerState.X, playerState.Y)
		
		globalState := &GameState{
			ActivePlayers: 42,
			GlobalEvent:   "Weather: Rain",
		}
		
		if err := stream.Send(globalState); err != nil {
			return err
		}
	}
}

func main() {}
