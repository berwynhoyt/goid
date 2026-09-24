// Keep these build tags identical to goid_other.go.
//go:build !gc || purego

package goid

import "testing"

// TestFallback checks that the slow path is selected without an assembler.
func TestFallback(t *testing.T) {
	if !UsingFallback() {
		t.Fatal("UsingFallback() = false, want true under purego or non-gc compiler")
	}
}
