# Amstrad CPC

Collapse OS (release 2021-04-21, Forth) on the Amstrad CPC 464 (with DDI-1),
664 and 6128. It boots from floppy (AMSDOS) or from an M4 board's SD card,
and keeps its blocks in ordinary AMSDOS files, so the same code works on both.

## Files

All names the CPC sees are 8.3 or shorter (AMSDOS and the M4 board only
handle 8.3 names, folders included). The program is called `COLLAPS`.

`make` produces:

- `os.bin`: the raw kernel, built to run at 0x0400.
- `COLLAPS.BIN`: the same with an AMSDOS header.
- `COLLAPS.BAS`: BASIC loader (ASCII). It POKEs a 41-byte boot stub
  (`boot.fs`) at 0x9000 and CALLs it. The stub loads `COLLAPS.BIN` to
  0x0400 with CAS IN OPEN/DIRECT and jumps to it.
- `blkgroups/Bnnn.BLK`: the blkfs split into 8K AMSDOS files. `B208.BLK`
  holds blocks 208-215. Empty groups are not written.
- `COLLAPS.DSK`: 40-track AMSDOS DATA disc, Extended DSK container. Holds
  the loader, the kernel and the groups useful on a CPC: 0-23 (assemblers),
  96-119 (block editor, VE), 200-239 (xcomp, core), 280-303 (Z80 kernel
  source) and 368-375 (CPC drivers). About 35K is left free.
- `COLLAPS.ZIP`: everything for an M4 SD card, at the root of the zip:
  loader, kernel and all non-empty groups.

## Running

Floppy (or Gotek/HxC with `COLLAPS.DSK`):

    RUN"COLLAPS

M4: unzip `COLLAPS.ZIP` into a folder with a name of 8 characters or less
(e.g. `COLLAPS`) on the SD card, then

    |CD,"COLLAPS"
    RUN"COLLAPS

Do not use `RUN"COLLAPS.BIN"`: running a binary from BASIC resets the
firmware. The background ROMs (AMSDOS, M4) get disconnected and block I/O
falls back to cassette (verified: "Press PLAY then any key:"). The loader
uses LOAD-style calls that keep them alive.

The loader refuses to start if HIMEM is below &9FFF. That happens when
other ROMs reserved too much memory, which would overlap Collapse OS's stacks.

## First steps

Collapse OS words take their arguments from the stack, before the word:

    0 LIST          list block 0 (the master index)
    LIST            -> "stack underflow": LIST needs a block number
    100 LIST        block editor source
    110 LOAD  VE    load and start the Visual Editor (q quits)
    5 LOAD          load the Z80 assembler
    2 3 + .         prints 5

## Design: firmware stays resident

Like the TRS-80 recipe, this port uses the machine's own firmware for I/O.
It never touches the interrupt mode or vector.

- `(emit)` -> TXT OUTPUT (0xbb5a), screen mode 2 (80x25).
- `(key?)` -> KM READ CHAR (0xbb09). Characters >= 0x80 (cursor keys,
  COPY, ...) are ignored. ESC's break mechanism is disarmed.
- `AT-XY` -> TXT SET CURSOR (0xbb75). `COLS` `LINES` `CELL!` `XYMODE` make
  the Visual Editor work (`110 LOAD` then `VE`).
- `BYE` resets the machine.

Extra words:

- `FW ( af bc de hl addr -- af bc de hl )` calls any firmware routine. A
  is the MSB of `af`, carry is bit 0 of the returned `af`. Example: `0x0700
  0 0 0 0xbb5a FW 2DROP 2DROP` beeps.
- `FW0 ( addr -- )` calls a routine without arguments.
- `MODE ( n -- )` sets screen mode (COLS stays 80; VE wants mode 2).
- `CMOVE ( src dst u -- )` copies memory with LDIR.

### The shadow-register rule

The CPC firmware interrupt handler (`0x0038: jp 0xb941`) starts with
`di / ex af,af' / jr c,... / exx / ... out (c),c`. It keeps its re-entrancy
flag in AF' and the Gate Array port in BC'. Code that runs `EXX` or
`EX AF,AF'` while interrupts are enabled crashes the machine at the next
interrupt.

The Z80 kernel uses `EXX,` (FIND, `*`, `/MOD`, `[]=`, CRC16) and `EXAFAF',`
(CARRY? and `+` `-` `*`). Block 370, loaded between the assembler and
B280, redefines those two assembler words. `EXX,` swaps DE with a RAM slot,
and `EXAFAF',` swaps AF with a RAM slot. The kernel only ever uses EXX to
protect DE (IP) and EX AF,AF' to stash the carry, so the behaviour is
identical. The upstream blocks are unchanged.

If you assemble your own code on the CPC (`5 LOAD`), do not use `EXX,` or
`EXAFAF',` unless you first load the same redefinitions:
`0x9ba0 CONSTANT DRVMEM 370 LOAD`.

### Blocks: AMSDOS group files

AMSDOS has no random access, so blocks are grouped by 8 into 8K files,
read and written whole with CAS IN/OUT DIRECT. Two groups are cached in RAM
with LRU, so nested `LOAD`s that jump between a parent block and its
children don't re-read the disc. Writing a block rewrites its group file
(write-through). AMSDOS then renames the old file to `.BAK`, so the driver
erases that `.BAK` with `|ERA` right away (KL FIND COMMAND + KL FAR PCHL).
Otherwise every edited group would leave 9K behind and the disc would fill
up.

A block in a group with no file reads as empty. AMSDOS prints
`Bnnn.BLK not found` when that happens: it always prints this message, with
no flag to disable it (checked in the AMSDOS ROM: `CEC4 jp nc,D50C ->
ld a,6 -> print`). The first write creates the file.

Group files carry an AMSDOS header. Headerless files can't be read with
CAS IN DIRECT (tested), so each 8K group takes 9K on disc.

## Memory map

    0x0000-0x03ff  firmware restarts, BASIC (unused once we run)
    0x0400         kernel (~7K), then BLK( buffer and the dictionary
    0x5300-0x5aff  CASBUF, AMSDOS 2K buffer
    0x5b00-0x9aff  GRPBUF, two 8K group slots
    0x9b00-0x9bff  SYSVARS, DRVMEM
    0x9c00         RS (grows up)
    0x9ffe         PS (grows down)
    0xa000-        firmware, AMSDOS, M4 workspace

The dictionary has about 12K: the Z80 assembler uses ~2.9K, the editors
~2.5K. Buffers passed to the firmware and the stacks must be inside
0x4000-0xbfff. While the firmware runs (its interrupts included), it pages
ROM over the rest.

## Speed

Loading source is CPU bound: Collapse OS looks up every word with a linear
dictionary search. On a CPC a block takes 1-2 seconds, so `110 LOAD` (VE)
takes about 70 seconds and `5 LOAD` (assembler) about a minute (measured in
MAME). Reading or writing a group takes a few seconds on a floppy. While
AMSDOS transfers sectors, interrupts are off and the firmware doesn't scan
the keyboard, so keys pressed during disc activity can be missed.

## Verified in MAME 0.264 (cpc6128 and cpc464 + DDI-1)

- Boot from the DSK with `RUN"COLLAPS`, banner, interpreter.
- `LIST` from group files, a missing group reads as empty.
- `COPY` writes blocks: new group files are created, existing ones
  rewritten. Reading back after cache eviction is correct, and no `.BAK`
  is left behind (checked with CAT).
- `110 LOAD` + `VE`: Visual Editor draws and edits, `q` exits.
- `5 LOAD`, `LIVETGT`, a CODE word assembled and run on the CPC
  (`3 X7 .` -> 10), and `FW` calling TXT OUTPUT.
- VE edit cycle: type into an empty block, `q`, `FLUSH`, evict the cache,
  `LIST` shows the text read back from disc.
- On the 464 + DDI-1: boot, `LIST`, `COPY`.

The M4 board can't be emulated here. It patches the same AMSDOS/CAS
vectors this port uses, but that part has not been tested on M4 hardware.
