#!/usr/bin/env python3
"""Turn a MAME CPC snapshot (768x272 PNG) into text by matching each 8x8
character cell against the CPC ROM font (lower ROM, offset 0x3800).

Usage: cpcocr.py snapshot.png [cols] [rom]
  rom: CPC system ROM holding the font (default: roms/cpc6128/cpc6128.rom
       next to this script, or $CPC_ROMS/cpc6128/cpc6128.rom)
  cols: 40 (mode 1) or 80 (mode 2), or 20 (mode 0). Default: 40.

The 640x200 active area sits at x=64, y=37 in MAME's 768x272 snapshot of a
cpc6128/cpc464. Any pixel whose colour differs from the paper colour (taken
from the top-left of the active area's background) is "ink". Inverse cells
(e.g. a cursor) match the inverted glyph and are shown as-is.
"""
import os
import sys
from PIL import Image

X0, Y0, W, H = 64, 37, 640, 200


def load_font(rom):
    data = open(rom, 'rb').read()
    return [data[0x3800 + 8 * c:0x3800 + 8 * c + 8] for c in range(256)]


def main():
    png = sys.argv[1]
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    roms = os.environ.get('CPC_ROMS', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'roms'))
    rom = sys.argv[3] if len(sys.argv) > 3 else os.path.join(roms, 'cpc6128', 'cpc6128.rom')
    font = load_font(rom)
    im = Image.open(png).convert('RGB')
    px = im.load()
    # paper = most common colour in the active area
    hist = {}
    for y in range(Y0, Y0 + H, 4):
        for x in range(X0, X0 + W, 4):
            c = px[x, y]
            hist[c] = hist.get(c, 0) + 1
    paper = max(hist, key=hist.get)
    cw = W // cols
    lines = []
    for row in range(25):
        s = ''
        for col in range(cols):
            bits = []
            for yy in range(8):
                b = 0
                for xx in range(8):
                    x = X0 + col * cw + int((xx + 0.5) * cw / 8)
                    y = Y0 + row * 8 + yy
                    b = (b << 1) | (px[x, y] != paper)
                bits.append(b)
            if not any(bits):
                s += ' '
                continue
            best, bestd = '?', 99
            for c in range(32, 127):
                g = font[c]
                d = sum(bin(g[i] ^ bits[i]).count('1') for i in range(8))
                di = sum(bin((g[i] ^ 0xff) ^ bits[i]).count('1') for i in range(8))
                if d < bestd:
                    best, bestd = chr(c), d
                if di < bestd:
                    best, bestd = chr(c), di
            s += best if bestd <= 6 else '?'
        lines.append(s.rstrip())
    while lines and not lines[-1]:
        lines.pop()
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
