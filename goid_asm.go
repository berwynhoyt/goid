// Declares getg() for goid_asm.s. Keep these build tags identical to goid_asm.s.
//go:build gc && !purego
// +build gc,!purego

package goid

import "unsafe"

// getg returns the address of the current goroutine's runtime g struct.
// The g struct is never freed by the runtime, so the pointer remains valid.
func getg() unsafe.Pointer
