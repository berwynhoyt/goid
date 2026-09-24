package goid

import (
	"runtime"
	"sync"
	"testing"
)

// TestGetMatchesSlow checks Get() against the slow parser on the test goroutine.
func TestGetMatchesSlow(t *testing.T) {
	if got, want := Get(), GetSlow(); got != want {
		t.Fatalf("Get() = %d, want %d", got, want)
	}
}

// TestGetStable checks that repeated calls in one goroutine return the same ID.
func TestGetStable(t *testing.T) {
	id := Get()
	for i := range 1000 {
		if i%100 == 0 {
			runtime.Gosched() // Encourage migration to another OS thread.
		}
		if got := Get(); got != id {
			t.Fatalf("call %d: Get() = %d, want %d", i, got, id)
		}
	}
}

// TestGetConcurrent checks many simultaneous goroutines each get their own correct ID.
// Several rounds are run so that exited g structs get reused by the runtime.
func TestGetConcurrent(t *testing.T) {
	const rounds = 5
	const perRound = 200
	for round := range rounds {
		ids := make([]uint64, perRound)
		errs := make(chan string, perRound)
		var wg sync.WaitGroup
		for i := range perRound {
			wg.Add(1)
			go func() {
				defer wg.Done()
				id := Get()
				runtime.Gosched()
				if slow := GetSlow(); id != slow {
					errs <- "Get() does not match GetSlow()"
				}
				if again := Get(); id != again {
					errs <- "Get() changed within one goroutine"
				}
				ids[i] = id
			}()
		}
		wg.Wait()
		close(errs)
		for e := range errs {
			t.Fatalf("round %d: %s", round, e)
		}

		// Live goroutines must all have distinct IDs.
		seen := make(map[uint64]bool, perRound)
		for _, id := range ids {
			if seen[id] {
				t.Fatalf("round %d: duplicate goroutine ID %d", round, id)
			}
			seen[id] = true
		}
	}
}

// TestGetLockedThread checks Get() on a goroutine locked to its OS thread.
func TestGetLockedThread(t *testing.T) {
	ch := make(chan [2]uint64)
	go func() {
		runtime.LockOSThread()
		defer runtime.UnlockOSThread()
		ch <- [2]uint64{Get(), GetSlow()}
	}()
	if r := <-ch; r[0] != r[1] {
		t.Fatalf("Get() = %d, want %d", r[0], r[1])
	}
}

func BenchmarkGet(b *testing.B) {
	var sink uint64
	for range b.N {
		sink += Get()
	}
	_ = sink
}

func BenchmarkGetSlow(b *testing.B) {
	var sink uint64
	for range b.N {
		sink += GetSlow()
	}
	_ = sink
}

func BenchmarkGetParallel(b *testing.B) {
	b.RunParallel(func(pb *testing.PB) {
		var sink uint64
		for pb.Next() {
			sink += Get()
		}
		_ = sink
	})
}

func BenchmarkGetSlowParallel(b *testing.B) {
	b.RunParallel(func(pb *testing.PB) {
		var sink uint64
		for pb.Next() {
			sink += GetSlow()
		}
		_ = sink
	})
}
