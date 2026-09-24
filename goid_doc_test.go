// UsingFallback() intentionally doesn't return false if purego is set, so skip this test
//go:build gc && !purego
// +build gc,!purego

package goid_test

import (
	"fmt"

	"github.com/berwynhoyt/goid"
)

// Test the README.md example
func ExampleGet() {
	fmt.Println("Current goroutine ID:", goid.Get())
	fmt.Println("Should match GetSlow() ID:", goid.GetSlow())
	fmt.Println("UsingFallback():", goid.UsingFallback())

	// Output:
	// Current goroutine ID: 1
	// Should match GetSlow() ID: 1
	// UsingFallback(): false
}
