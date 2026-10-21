# Collapse OS for the Amstrad CPC

Ports of [Collapse OS](http://collapseos.org) to the Amstrad CPC 464 (with
DDI-1 disc interface), 664 and 6128. They run from floppy (AMSDOS) or from an
M4 board's SD card.

There are two ports, one for each era of Collapse OS:

| | Forth (`forth/`) | Assembly (`asm/`) |
|---|---|---|
| Collapse OS version | release 2021-04-21 (the "complete" Forth system) | March 2020 assembly kernel |
| What you get | Forth system: interpreter, block editor, Visual Editor, Z80 assembler, cross-compiler | BASIC shell |
| Screen | mode 2, 80x25 | mode 1, 40x25 |
| Storage | blocks in AMSDOS files, read and write | none |
| Port code | `forth/arch/z80/cpc/`, blocks 370-377 in `forth/blk.fs` | `asm/recipes/cpc/`, `asm/kernel/cpc/` |

## Quick start (prebuilt files in `release/`)

### Forth version

Floppy: write `release/forth/COLLAPS.DSK` to a disc (or use it in a Gotek,
HxC or emulator), then type

    RUN"COLLAPS

M4 board: unzip `release/forth/COLLAPS.ZIP` into a folder on the SD card with
a name of 8 characters or less (e.g. `COLLAPS`), then

    |CD,"COLLAPS"
    RUN"COLLAPS

Don't `RUN"COLLAPS.BIN"` directly: running a binary from BASIC resets the
firmware and disconnects the disc/M4 ROM, so blocks would not load.

First steps (Forth words take their arguments first):

    0 LIST          list block 0, the master index
    2 3 + .         prints 5
    110 LOAD        load the Visual Editor (takes about a minute)
    VE              start it, q quits
    5 LOAD          load the Z80 assembler

`LIST` on its own answers "stack underflow": it needs a block number.

### Assembly version

Floppy: `release/asm/collapse.dsk`, then `RUN"COLLAPSE`. M4: copy
`release/asm/COLLAPSE.BIN` to the SD card, then `RUN"COLLAPSE.BIN`. At the `>`
prompt type BASIC, e.g. `print 6*7`, `10 print 1234`, `list`, `run`.

## Building

Both builds need `python3`, `make`, a C compiler and, for the assembly
version, `xxd` and `git`.

Forth version:

    make -C forth/cvm clean          # removes stale objects from upstream
    make -C forth/arch/z80/cpc       # os.bin, COLLAPS.BIN/.BAS/.DSK/.ZIP

Assembly version:

    asm/emul/get-libz80.sh           # fetches libz80 at the pinned commit
    make -C asm/emul zasm/zasm
    make -C asm/recipes/cpc          # os.bin, COLLAPSE.BIN, collapse.dsk

Both builds are reproducible: they produce the files in `release/` byte for
byte (the zip only differs in timestamps).

Without `xxd`, `asm/emul/bin2c.sh` writes empty bootstrap images and zasm
"hangs" on every recipe.

## Porting notes

The design is described in `forth/arch/z80/cpc/README.md` and
`asm/recipes/cpc/README.md`. `docs/NOTES.md` has the working notes: firmware
facts verified in the ROM and the emulator, and the traps found along the way.

The most important one: **the CPC firmware's interrupt handler owns the
shadow registers AF' and BC'.** Any `EXX` or `EX AF,AF'` with interrupts
enabled crashes the machine at the next interrupt.
- The Forth port redefines the assembler words `EXX,` and `EXAFAF',` (block
  370) so the unchanged upstream Z80 kernel uses RAM slots instead.
- The assembly port rewrites the four library routines that used them, with
  identical behaviour. The upstream unit and shell tests still pass.

Other things worth knowing:
- All file and folder names the CPC sees must be 8.3 or shorter (AMSDOS, M4).
- The firmware is kept resident: console through TXT/KM, storage through the
  AMSDOS CAS calls, which the M4 board patches. The same code therefore works
  on floppy and SD.
- Forth blocks are stored 8 per AMSDOS file (`B208.BLK` = blocks 208-215),
  with a two-file cache. `.BAK` files that AMSDOS leaves on save are erased.

## Testing

`test/` holds the MAME harness used to test both ports. It boots a CPC,
types into it, takes screenshots and turns them into text. See
`test/README.md`.

Tested in MAME 0.264 on an emulated CPC 6128, and on a 464 + DDI-1:
- boot
- the interpreters
- block reads and writes (Forth)
- the Visual Editor (Forth)
- the Z80 assembler (Forth)

Not yet tested on real hardware. The M4 board can't be emulated: the Forth
version reached the prompt on a real M4, but block writes on M4 are untested.

## Repository layout

    forth/     Collapse OS 2021-04-21 + CPC port (arch/z80/cpc, blocks 370-377,
               tools/cpc)
    asm/       Collapse OS March 2020 (assembly) + CPC port (recipes/cpc,
               kernel/cpc, tools/cpc, 4 library routines, emul.c include fix)
    release/   prebuilt disc images, binaries and the M4 zip
    test/      MAME test harness and screen OCR
    docs/      porting notes

## Credits and license

Collapse OS is by Virgil Dupras and contributors, licensed under the GNU GPL
version 3 (see `LICENSE`, and `forth/COPYING`, `asm/COPYING`). The CPC ports
are released under the same license.

Upstream sources used (collapseos.org is the official home; these are
snapshots of it):
- Forth: tag v1.0.0 of https://github.com/kizitoomoit/CollapseOS, the
  unmodified 2021-04-21 release
- Assembly: https://github.com/tcheredeev/collapseos (March 2020, 792 commits)
- libz80: https://github.com/ggambetta/libz80 at 8a1f935
