# goid

This package implements direct instant access to the goroutine ID (goid) for all versions of Go (including future), and all architectures that the Go compiler/assembler supports. The package is written by Berwyn Hoyt for YottaDB, copyright 2006, and released under an [MIT license](LICENSE).

Many packages attempt to provide a fast goid (e.g. by [Peter Mattis](https://github.com/petermattis/goid) or [OutrigDev](https://github.com/outrigdev/goid)), but invariably depend on specific versions of Go, and only work with certain architectures. This package has neither limitation.

Go designers discourage production-code access to the goid because they want to prevent goroutine-local storage that can lead to writing fragile, implicit code. However, there are valid and sometimes important reasons to need the goid. Many of these (e.g. debug visibility and profiling) do not require speed. But a few use-cases do require both speed and production access. For example, the Go wrapper for YottaDB needs to use the goroutine ID as a safety check (specifically, incorrect use of multiple database connections within a single goroutine, causing deadlocks). Such use of the goid is deemed acceptable, and even desirable, to prevent unintentional programmer errors. Use it with care.

Since fast access to the goid requires assembler code, the package still provides a slow fallback for whether the developer is using an alternative Go compiler without an assember (e.g. gccgo or gollvm).

## Features

* **Fast:** instant assembler access to the goid
* **All versions of Go** (including future versions).
* **All architectures** that the standard Go assembler supports.

## Quick start

```go
go get github.com/berwynhoyt/goid
```

## Example

```go
package main

import (
	"fmt"
	"github.com/berwynhoyt/goid"
)

func ExampleGet() {
	fmt.Println("Current goroutine ID:", goid.Get())
	fmt.Println("Should match GetSlow() ID:", goid.GetSlow())
	fmt.Println("UsingFallback():", goid.UsingFallback())
}
```

## Implementation

* The assembly code provides a one-line assembly instruction for each supported Go architecture to return the goroutine struct. This struct is used by all versions of Go, but the offset of goid within it varies between Go versions.
* The init() function finds this offset by scanning the struct until it finds the goid that matches the more standard GetSlow(), and which also agrees with the location found in several concurrent goroutines.

## Benchmarks

```sh
$ go test --bench .
goos: linux
goarch: amd64
cpu: AMD Ryzen 9 8945H w/ Radeon 780M Graphics
BenchmarkGet-16                	 571182526	        2.102  ns/op
BenchmarkGetSlow-16            	    724078	        1658   ns/op
BenchmarkGetParallel-16        	1000000000	        0.2032 ns/op
BenchmarkGetSlowParallel-16    	    637208	        1826   ns/op
```

