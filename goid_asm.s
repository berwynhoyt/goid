// Get runtime goroutine struct g for all architectures supported by Go

// Most architectures reserve a g register, which assembly can access directly.
// On 386 and amd64, g is loaded from thread-local storage instead.
// ABI0 code on amd64 cannot rely on R14 holding g, so TLS is used there too.

// Future gc architectures fail noisily at compile time (error will be: unrecognized instruction "STORE_G").
// Compilers other than gc without a Go assembler (e.g. gccgo) use the slow fallback in goid_other.go.
// So does the purego build tag, which by convention disables assembly (TinyGo sets it automatically).
// The user can test whether fallback is selected with UsingFallback().
// Keep these build tags identical to goid_asm.go and the inverse of goid_other.go.
//go:build gc && !purego

// Note: nothing prevents this from working in go versions back as far as 1.5. I don't know about anything earlier than that.
// However, goid.go would have to stop using newer language syntax: like for range() and unsafe.Add()

#include "go_asm.h"
#include "textflag.h"

#ifdef GOARCH_386
#define STORE_G(dst) MOVL (TLS), AX; MOVL AX, dst
#endif

#ifdef GOARCH_amd64
#define STORE_G(dst) MOVQ (TLS), AX; MOVQ AX, dst
#endif

#ifdef GOARCH_arm
#define STORE_G(dst) MOVW g, dst
#endif

#ifdef GOARCH_mips
#define STORE_G(dst) MOVW g, dst
#endif

#ifdef GOARCH_mipsle
#define STORE_G(dst) MOVW g, dst
#endif

#ifdef GOARCH_arm64
#define STORE_G(dst) MOVD g, dst
#endif

#ifdef GOARCH_ppc64
#define STORE_G(dst) MOVD g, dst
#endif

#ifdef GOARCH_ppc64le
#define STORE_G(dst) MOVD g, dst
#endif

#ifdef GOARCH_s390x
#define STORE_G(dst) MOVD g, dst
#endif

#ifdef GOARCH_wasm
#define STORE_G(dst) MOVD g, dst
#endif

#ifdef GOARCH_loong64
#define STORE_G(dst) MOVV g, dst
#endif

#ifdef GOARCH_mips64
#define STORE_G(dst) MOVV g, dst
#endif

#ifdef GOARCH_mips64le
#define STORE_G(dst) MOVV g, dst
#endif

#ifdef GOARCH_riscv64
#define STORE_G(dst) MOV g, dst
#endif

TEXT ·getg(SB), NOSPLIT, $0-const_ptrSize
	// Pass destination to STORE_G as this prevents a go vet false positive error.
	// Note: If STORE_G is unrecognized (an error), add a new STORE_G definition above for this GOARCH.
	STORE_G(ret+0(FP))
	RET
