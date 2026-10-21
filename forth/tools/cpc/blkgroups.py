#!/usr/bin/env python3
"""Split a Collapse OS blkfs into AMSDOS files of 8 blocks (8K) each.

Usage: blkgroups.py [--no-header] blkfs outdir

File Bnnn.BLK holds blocks nnn..nnn+7 (nnn = first block, decimal).
Groups that are entirely empty (all zero) are skipped: the CPC driver
treats a missing file as 8 empty blocks.
By default each file gets an AMSDOS binary header (load 0x7b00).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amsdos import header

GROUP = 8 * 1024


def main():
    args = sys.argv[1:]
    hdr = True
    if args and args[0] == '--no-header':
        hdr = False
        args = args[1:]
    blkfs, outdir = args
    data = open(blkfs, 'rb').read()
    for off in range(0, len(data), GROUP):
        chunk = data[off:off + GROUP].ljust(GROUP, b'\0')
        if not any(chunk):
            continue
        name = 'B%03d.BLK' % (off // 1024)
        with open(os.path.join(outdir, name), 'wb') as f:
            if hdr:
                f.write(header(name, GROUP, 0x7b00, 0))
            f.write(chunk)


if __name__ == '__main__':
    main()
