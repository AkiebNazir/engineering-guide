# Exercise 4: Dynamic Feature Flag System in Go 🟡

## 🎯 Objective
Implement a feature flag system in Go that allows enabling/disabling a new feature at runtime without restarting the application.

## 📋 Prerequisites
- Go installed

## 📝 Instructions

1. Create `feature_flags.go`.
2. Use a `sync.RWMutex` to safely allow concurrent reads and updates to a map of feature flags.
3. Simulate an application loop checking the flag.

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type FeatureFlagManager struct {
	mu    sync.RWMutex
	flags map[string]bool
}

func NewManager() *FeatureFlagManager {
	return &FeatureFlagManager{
		flags: make(map[string]bool),
	}
}

func (m *FeatureFlagManager) Set(feature string, enabled bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.flags[feature] = enabled
	fmt.Printf("[SYSTEM] Feature '%s' set to %v\n", feature, enabled)
}

func (m *FeatureFlagManager) IsEnabled(feature string) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.flags[feature]
}

func main() {
	ff := NewManager()
	
	// Initial state
	ff.Set("NewPaymentGateway", false)

	// Simulate user requests in a goroutine
	go func() {
		for i := 1; i <= 5; i++ {
			if ff.IsEnabled("NewPaymentGateway") {
				fmt.Printf("User %d: Processed via NEW Stripe Gateway\n", i)
			} else {
				fmt.Printf("User %d: Processed via LEGACY Gateway\n", i)
			}
			time.Sleep(1 * time.Second)
		}
	}()

	// Simulate a developer turning on the feature remotely
	time.Sleep(2 * time.Second)
	ff.Set("NewPaymentGateway", true)

	time.Sleep(4 * time.Second)
}
```

## ✅ Expected Output
```
[SYSTEM] Feature 'NewPaymentGateway' set to false
User 1: Processed via LEGACY Gateway
User 2: Processed via LEGACY Gateway
[SYSTEM] Feature 'NewPaymentGateway' set to true
User 3: Processed via NEW Stripe Gateway
User 4: Processed via NEW Stripe Gateway
User 5: Processed via NEW Stripe Gateway
```

## 🧠 Key Takeaway
Feature flags decouple deployment from release. The code for the new gateway was already deployed and running, but the *release* happened when the flag was flipped to true.
