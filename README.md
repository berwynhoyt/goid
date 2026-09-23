# goid

This package implements direct instant access to the goroutine ID (goid) for all versions of Go (including future), and all architectures that the Go compiler/assembler supports. The package is released an [MIT license](LICENSE), and written by Berwyn Hoyt for YottaDB, copyright 2006.

Many packages attempt to provide a fast goid (e.g. by [Peter Mattis](https://github.com/petermattis/goid) or [OutrigDev](https://github.com/outrigdev/goid)). But they invariably depend on specific versions of Go, and only work with certain architectures. This package has neither limitation.

The goid is notoriously difficult to read directly and quickly. This is because the Go designers actively discourage production-code access to it because they want to prevent goroutine-local storage that can lead to writing fragile, implicit code. And nobody wants that.

However, there are valid and sometimes important reasons to need the goid. Many of these (debug visibility and profiling) do not requires speed. But a few use-cases do require both speed and production access. For example, the Go wrapper for YottaDB needs to use the goroutine ID as a safety check against unintentional programmer errors (incorrectly using multiple database connections and transactions with a single goroutine, causing deadlocks). Such use of the goid is deemed acceptable and even desirable. Use it with care.

Since fast access to the goid requires assembler code, the package still provides a slow fallback for whether the developer is using an alternative Go compiler without an assember (e.g. gccgo or gollvm).

## Features

* **Fast**
* **All versions of Go** (including future versions).
* **All architectures** that the standard Go assembler supports.

## Quick start

