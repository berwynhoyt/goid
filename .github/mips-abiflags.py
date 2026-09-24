#!/usr/bin/env python3
"""go test -exec wrapper: add a .MIPS.abiflags header to a Go mips binary, allowing qemu to run it.

Usage: go test -exec .github/mips-abiflags.py ...
Go only emits this header from 1.17. Without it, qemu cannot tell which FPU mode the binary needs.
It then picks 64-bit FPU registers (FR=1), but Go expects paired 32-bit ones (FR=0).
Float compares then fail, so the runtime aborts at startup with "fatal error: float64nan".
Real kernels read the same header, so this only declares what the code already assumes.

The header is added by retyping Go's PT_PAX_FLAGS program header, which Linux ignores.
It points at 24 bytes of flags appended to the file, which is where qemu reads them from.
The flags match those Go 1.17+ emits: MIPS32 rev 1, 32-bit registers, hard-float double.
"""

import os
import struct
import sys

PT_PAX_FLAGS = 0x65041580
PT_MIPS_ABIFLAGS = 0x70000003

path = sys.argv[1]
with open(path, "rb") as f:
    elf = bytearray(f.read())
if elf[:4] != b"\x7fELF" or elf[4] != 1:
    sys.exit("mips-abiflags: %s is not a 32-bit ELF file" % path)
end = "<" if elf[5] == 1 else ">"
phoff, = struct.unpack_from(end + "I", elf, 28)
phentsize, phnum = struct.unpack_from(end + "HH", elf, 42)
for i in range(phnum):
    ph = phoff + i * phentsize
    if struct.unpack_from(end + "I", elf, ph)[0] == PT_PAX_FLAGS:
        break
else:
    sys.exit("mips-abiflags: %s has no PT_PAX_FLAGS header to reuse" % path)

while len(elf) % 8:
    elf.append(0)
flags_off = len(elf)
# Fields: version, isa_level, isa_rev, gpr_size, cpr1_size, cpr2_size, fp_abi, isa_ext, ases, flags1, flags2.
# Size code 1 means 32 bits, and fp_abi 1 means hard float with double precision.
elf += struct.pack(end + "HBBBBBBIIII", 0, 32, 1, 1, 1, 0, 1, 0, 0, 0, 0)
# Fields: type, offset, vaddr, paddr, filesz, memsz, flags, align.
struct.pack_into(end + "8I", elf, ph, PT_MIPS_ABIFLAGS, flags_off, 0, 0, 24, 24, 4, 8)
with open(path, "wb") as f:
    f.write(elf)

# binfmt_misc hands the binary to qemu, just as go test would have done without -exec.
os.execv(path, sys.argv[1:])
