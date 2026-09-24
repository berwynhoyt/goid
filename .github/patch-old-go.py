#!/usr/bin/env python3
"""Patch an old Go toolchain so its foreign-architecture binaries run under qemu-user.

Usage: patch-old-go.py <GOROOT> <go minor version>
Prints "rebuild" if the compiler and assembler must then be rebuilt with "go install -a cmd/asm cmd/compile".

Neither patch changes the goroutine struct that goid inspects.
Each only swaps behavior qemu cannot emulate for the equivalent that newer Go uses.
"""

import os
import re
import sys

goroot, minor = sys.argv[1], int(sys.argv[2])


def patch(rel, old, new):
    """Replace exactly one occurrence of regex old with new in GOROOT/rel."""
    path = os.path.join(goroot, rel)
    with open(path) as f:
        text = f.read()
    text, count = re.subn(old, new, text)
    if count != 1:
        sys.exit("patch-old-go: expected 1 match in %s, found %d" % (rel, count))
    with open(path, "w") as f:
        f.write(text)
    print("patch-old-go: patched " + rel, file=sys.stderr)


# Before Go 1.9, the runtime creates threads without CLONE_SYSVSEM, and qemu rejects that.
# arm, arm64 and s390x then die with errno 22. ppc64 and mips64 misread the error and hang.
# Go 1.9 added the flag for exactly this reason (Go issue #20763).
if minor < 9:
    rel = "src/runtime/os_linux.go" if minor >= 7 else "src/runtime/os1_linux.go"
    patch(rel, r"_CLONE_THREAD /\* revisit - okay for now \*/",
          "_CLONE_SYSVSEM | _CLONE_THREAD /* revisit - okay for now */")

# Before Go 1.10, MOVW between mips64 registers assembles to OR or ADDU with $zero.
# The ISA leaves their upper 32 bits undefined, and qemu does not sign-extend them.
# Signed 32-bit compares then fail, crashing the runtime at startup.
# Go 1.10 and later still use ADDU but pass the tests, so they are left alone.
# Newer Go uses SLL, which the ISA defines to sign-extend, so do the same here.
if 6 <= minor < 10:
    rel = "src/cmd/internal/obj/mips/asm0.go"
    oprrr = "c.oprrr(" if minor >= 9 else "oprrr(ctxt, "
    sll = ("a := AOR\n\t\tif p.As == AMOVW {\n\t\t\ta = ASLL\n\t\t}\n"
           "\t\to1 = OP_RRR(" + oprrr + "a), uint32(p.From.Reg), uint32(REGZERO), uint32(p.To.Reg))")
    # The whole body of "case 1" (register move) is replaced, since its wording varies by version.
    # Only mips64 reaches this with MOVW; mips32 MOVW needs no extension, and SLL by zero is a move.
    patch(rel, r"(case 1: /\* mov r1,r2 ==> OR r1,r0,r2 \*/\n\t\t)(?:.|\n)*?(\n\n\tcase 2:)",
          lambda m: m.group(1) + sll + m.group(2))
    print("rebuild")
