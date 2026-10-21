#!/usr/bin/env python3
"""Make the Collapse OS BASIC loader: an AMSDOS ASCII BASIC file that POKEs
the boot stub (boot.bin, assembled for ADDR) and CALLs it.

Usage: mkloader.py boot.bin ADDR MINHIMEM OUT.BAS
"""
import sys

stub = open(sys.argv[1], 'rb').read()
addr = int(sys.argv[2], 0)
minhimem = int(sys.argv[3], 0)
lines = [
    f'10 IF HIMEM<&{minhimem:X} THEN PRINT "Collapse OS needs HIMEM>=&{minhimem:X}":END',
    f'20 FOR i=0 TO {len(stub) - 1}:READ a:POKE &{addr:X}+i,a:NEXT',
    f'30 CALL &{addr:X}',
]
n = 100
for i in range(0, len(stub), 16):
    lines.append(f'{n} DATA ' + ','.join(str(b) for b in stub[i:i + 16]))
    n += 10
out = b''.join(l.encode('ascii') + b'\r\n' for l in lines) + b'\x1a'
open(sys.argv[4], 'wb').write(out)
