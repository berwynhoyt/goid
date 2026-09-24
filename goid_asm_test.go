// Keep these build tags identical to goid_asm.go.
//go:build gc && !purego
// +build gc,!purego

package goid

import "testing"

// TestNotFallback checks that the gc toolchain uses the fast assembly path.
func TestNotFallback(t *testing.T) {
	if UsingFallback() {
		t.Fatal("UsingFallback() = true, want false under gc without purego")
	}
	if getg() == nil {
		t.Fatal("getg() returned nil")
	}
}
