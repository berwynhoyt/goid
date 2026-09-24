// Get goroutine ID fast for every architecture supported by Go

package goid

import (
	"bytes"
	"runtime"
	"strconv"
	"unsafe"
)

// ptrSize is exported to goid_asm.s via go_asm.h as const_ptrSize.
const ptrSize = unsafe.Sizeof(uintptr(0))

// GetSlow returns the current goroutine's ID by parsing runtime.Stack() output.
// The first line of the trace looks like "goroutine 123 [running]:".
// It is slow but uses only public APIs, though the trace format is not formally specified.
// Tests use this to check that the fast version has identified the right offset within g for the fast id lookup by Get().
func GetSlow() uint64 {
	var buf [64]byte
	s := buf[:runtime.Stack(buf[:], false)]
	s = bytes.TrimPrefix(s, []byte("goroutine "))
	if i := bytes.IndexByte(s, ' '); i >= 0 {
		s = s[:i]
	}
	id, err := strconv.ParseUint(string(s), 10, 64)
	if err != nil {
		panic("goid: cannot parse goroutine ID from runtime.Stack(): " + err.Error())
	}
	return id
}

// readGoid returns the uint64 at g+offset.
func readGoid(g unsafe.Pointer, offset uintptr) uint64 {
	return *(*uint64)(unsafe.Add(g, offset))
}

// goidOffset stores the offset of g.goid, calculated by init()
var goidOffset uintptr

// init scans the goroutine struct to locate the offset of goid
func init() {
	if UsingFallback() {
		return
	}

	type data struct {
		g  unsafe.Pointer
		id uint64
	}

	// Run several goroutines to check that our location works in all of them.
	const num_goroutines = 5
	var datas [num_goroutines]data
	ch := make(chan data)
	done := make(chan struct{})
	defer close(done)

	// Fetch g and GetSlow() from each of our goroutines
	for range len(datas) {
		go func() {
			ch <- data{getg(), GetSlow()}
			// Keep alive until the scan is done so g struct is not released.
			<-done
		}()
	}
	for i := range datas {
		datas[i] = <-ch
	}

	// Find offset within struct that matches for every goroutine.
	// Increment offset by minimum alignment size for uint64 on this architecture.
findOffset:
	for goidOffset = 0; ; goidOffset += ptrSize {
		// Should be impossible to get to this, so if we do, report it because it signals a design fault
		if goidOffset >= 2048 { // e.g. Go 1.27 goroutine struct is ~500 bytes, so this is plenty
			panic("goid: could not find g.goid offset: report package design fault error to the developer")
		}
		for _, d := range datas {
			if readGoid(d.g, goidOffset) != d.id {
				continue findOffset
			}
		}
		break
	}
	// goidOffset now equals the offset of goid within g
}

// UsingFallback returns whether calls to Get() will be slow because this alternative toolchain has no Go assembler
// (or the purego build tag is set). Only the standard Go compiler has an assembler, not gccgo, gollvm, TinyGo, etc.
func UsingFallback() bool {
	return getg() == nil
}

// Get returns the current goroutine ID instantly.
// This uses assembly code to access the goroutine struct for performance 1000x faster than GetSlow().
// It relies on init() which computes the goidOffset to match this version of Go.
func Get() uint64 {
	g := getg()
	if g == nil {
		return GetSlow()
	}
	return readGoid(g, goidOffset)
}
