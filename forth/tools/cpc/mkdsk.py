#!/usr/bin/env python3
"""Build an Amstrad CPC "DATA format" disc image (.dsk, standard MV - CPCEMU
format) containing the given files.

Usage: mkdsk.py [--standard] out.dsk FILE [FILE...]
       mkdsk.py --list in.dsk          (list directory, for checking)

The image is written in the Extended DSK container ("EXTENDED CPC DSK
File") by default, or the original "MV - CPCEMU" one with --standard.
Both hold the same 40-track AMSDOS DATA-format disc.

Each FILE is stored under its own basename (upper-cased, 8.3). Files are
written as-is: add an AMSDOS header beforehand (amsdos.py) for binaries.

DATA format: 40 tracks, 1 side, 9 sectors/track of 512 bytes, sector IDs
0xC1-0xC9, no reserved tracks, 1K allocation blocks, 2 directory blocks
(64 entries), 178K usable. Sectors are laid out on each track with the
interleave AMSDOS's own FORMAT uses (C1 C6 C2 C7 C3 C8 C4 C9 C5).
"""
import os
import sys

TRACKS = 40
SECTORS = 9
SECSIZE = 512
FIRST_ID = 0xC1
BLOCK = 1024
DIR_BLOCKS = 2
DIR_ENTRIES = 64
TOTAL_BLOCKS = TRACKS * SECTORS * SECSIZE // BLOCK  # 180
INTERLEAVE = [0, 5, 1, 6, 2, 7, 3, 8, 4]


def cpm_name(path):
    base, _, ext = os.path.basename(path).upper().partition('.')
    if not base or len(base) > 8 or len(ext) > 3:
        sys.exit(f'{path}: name must be 8.3')
    return base.ljust(8).encode('ascii'), ext.ljust(3).encode('ascii')


def build(files):
    # linear image of all sectors, logical sector n = track n//9, sector n%9
    img = bytearray([0xE5]) * (TRACKS * SECTORS * SECSIZE)
    direntries = []
    nextblk = DIR_BLOCKS
    for path in files:
        data = open(path, 'rb').read()
        name, ext = cpm_name(path)
        nblocks = (len(data) + BLOCK - 1) // BLOCK
        if nextblk + nblocks > TOTAL_BLOCKS:
            sys.exit(f'disc full while adding {path}')
        blocks = list(range(nextblk, nextblk + nblocks))
        nextblk += nblocks
        for i, b in enumerate(blocks):
            chunk = data[i * BLOCK:(i + 1) * BLOCK]
            img[b * BLOCK:b * BLOCK + len(chunk)] = chunk
        records = (len(data) + 127) // 128
        # one directory entry ("extent") per 16K
        ext_no = 0
        while True:
            eblocks = blocks[ext_no * 16:(ext_no + 1) * 16]
            erecs = min(128, records - ext_no * 128)
            e = bytearray(32)
            e[0] = 0  # user 0
            e[1:9] = name
            e[9:12] = ext
            e[12] = ext_no
            e[15] = erecs
            for i, b in enumerate(eblocks):
                e[16 + i] = b
            direntries.append(bytes(e))
            ext_no += 1
            if ext_no * 128 >= records:
                break
    if len(direntries) > DIR_ENTRIES:
        sys.exit('too many directory entries')
    d = b''.join(direntries)
    img[0:len(d)] = d
    return img


def to_dsk(img, extended=True):
    out = bytearray(256)
    if extended:
        hdr = b'EXTENDED CPC DSK File\r\nDisk-Info\r\n'
    else:
        hdr = b'MV - CPCEMU Disk-File\r\nDisk-Info\r\n'
    out[0:len(hdr)] = hdr
    out[0x22:0x22 + 14] = b'collapseos-cpc'
    out[0x30] = TRACKS
    out[0x31] = 1
    tsize = 0x100 + SECTORS * SECSIZE
    if extended:
        # per-track size table, in units of 256 bytes
        for t in range(TRACKS):
            out[0x34 + t] = tsize // 256
    else:
        out[0x32:0x34] = tsize.to_bytes(2, 'little')
    for t in range(TRACKS):
        ti = bytearray(256)
        ti[0:12] = b'Track-Info\r\n'
        ti[0x10] = t
        ti[0x11] = 0
        ti[0x14] = 2  # 512 bytes
        ti[0x15] = SECTORS
        ti[0x16] = 0x4E  # GAP#3
        ti[0x17] = 0xE5  # filler
        data = bytearray()
        for i, s in enumerate(INTERLEAVE):
            si = 0x18 + i * 8
            ti[si] = t
            ti[si + 1] = 0
            ti[si + 2] = FIRST_ID + s
            ti[si + 3] = 2
            if extended:  # actual data length
                ti[si + 6:si + 8] = SECSIZE.to_bytes(2, 'little')
            off = (t * SECTORS + s) * SECSIZE
            data += img[off:off + SECSIZE]
        out += ti + data
    return bytes(out)


def list_dsk(path):
    raw = open(path, 'rb').read()
    tracks = raw[0x30]
    if raw[:8] == b'EXTENDED':
        sizes = [raw[0x34 + t] * 256 for t in range(tracks)]
    else:
        assert raw[:8] == b'MV - CPC', 'not a DSK'
        sizes = [int.from_bytes(raw[0x32:0x34], 'little')] * tracks
    img = bytearray(tracks * SECTORS * SECSIZE)
    pos = 256
    for t in range(tracks):
        tb = raw[pos:pos + sizes[t]]
        pos += sizes[t]
        for i in range(SECTORS):
            sid = tb[0x18 + i * 8 + 2]
            s = sid - FIRST_ID
            off = (t * SECTORS + s) * SECSIZE
            img[off:off + SECSIZE] = tb[256 + i * SECSIZE:256 + (i + 1) * SECSIZE]
    for n in range(DIR_ENTRIES):
        e = img[n * 32:(n + 1) * 32]
        if e[0] == 0xE5:
            continue
        name = e[1:9].decode('ascii', 'replace') + '.' + e[9:12].decode('ascii', 'replace')
        blocks = [b for b in e[16:32] if b]
        print(f'{name} ext={e[12]} records={e[15]} blocks={blocks}')
    return img


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == '--list':
        list_dsk(sys.argv[2])
        return
    args = sys.argv[1:]
    extended = True
    if args and args[0] == '--standard':
        extended = False
        args = args[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    img = build(args[1:])
    open(args[0], 'wb').write(to_dsk(img, extended))


if __name__ == '__main__':
    main()
