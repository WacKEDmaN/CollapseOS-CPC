#!/usr/bin/env python3
"""Prepend a 128-byte AMSDOS header to a file.

Usage: amsdos.py [--type 2] --load ADDR --exec ADDR [--name NAME.EXT] in out

Header layout (AMSDOS, as used by CPC 464/664/6128 disc and M4 board):
  0      user number
  1-8    filename (space padded, upper case)
  9-11   extension
  18     file type (0=BASIC, 1=protected BASIC, 2=binary, 0x16=ASCII)
  19-20  data length
  21-22  load address
  23     first block flag (0xff)
  24-25  logical length
  26-27  entry (exec) address
  64-66  real file length (24 bits)
  67-68  checksum: 16-bit sum of bytes 0..66
"""
import argparse
import os
import sys


def header(name, data_len, load, exe, ftype=2):
    base, _, ext = os.path.basename(name).upper().partition('.')
    h = bytearray(128)
    h[0] = 0
    h[1:9] = base[:8].ljust(8).encode('ascii')
    h[9:12] = ext[:3].ljust(3).encode('ascii')
    h[18] = ftype
    h[19:21] = (data_len & 0xffff).to_bytes(2, 'little')
    h[21:23] = load.to_bytes(2, 'little')
    h[23] = 0xff
    h[24:26] = (data_len & 0xffff).to_bytes(2, 'little')
    h[26:28] = exe.to_bytes(2, 'little')
    h[64:67] = data_len.to_bytes(3, 'little')
    csum = sum(h[0:67]) & 0xffff
    h[67:69] = csum.to_bytes(2, 'little')
    return bytes(h)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--load', type=lambda x: int(x, 0), required=True)
    p.add_argument('--exec', dest='exe', type=lambda x: int(x, 0))
    p.add_argument('--type', type=int, default=2)
    p.add_argument('--name', help='name stored in header (default: output name)')
    p.add_argument('infile')
    p.add_argument('outfile')
    a = p.parse_args()
    data = open(a.infile, 'rb').read()
    if a.load + len(data) > 0x10000:
        sys.exit('file does not fit in memory at that load address')
    exe = a.load if a.exe is None else a.exe
    name = a.name or a.outfile
    with open(a.outfile, 'wb') as f:
        f.write(header(name, len(data), a.load, exe, a.type))
        f.write(data)


if __name__ == '__main__':
    main()
