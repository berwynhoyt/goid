// Fallback for compilers other than gc, which lack a Go assembler, or when the purego build tag is set.
// Keep these build tags the inverse of goid_asm.s.
//go:build !gc || purego

package goid

import "unsafe"

// getg returns nil to make Get() use the slow getSlow() fallback.
func getg() unsafe.Pointer {
	return nil
}
