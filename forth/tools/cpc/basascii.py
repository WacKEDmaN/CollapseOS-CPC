#!/usr/bin/env python3
"""Turn a plain-text BASIC listing into an AMSDOS ASCII BASIC file
(no header, CR LF line ends, terminated by 0x1A) that LOAD/RUN accept.

Usage: basascii.py in.bas OUT.BAS
"""
import sys

src = open(sys.argv[1]).read().splitlines()
out = b''.join(l.rstrip().encode('ascii') + b'\r\n' for l in src if l.strip())
open(sys.argv[2], 'wb').write(out + b'\x1a')
