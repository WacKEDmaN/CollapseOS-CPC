# Amstrad CPC

Collapse OS (assembly era, BASIC shell) on the Amstrad CPC 464/664/6128.
Loads from floppy (AMSDOS) or from an M4 board's SD card like any other
CPC binary.

## Design: firmware stays resident

This port does not take over the machine from reset. The CPC firmware ROM
stays resident and enabled the whole time, following the pattern of the
trs80 recipe. The program is a flat binary loaded into free RAM and run
from BASIC. It never writes to address 0, never patches the RST 0x38
interrupt vector, and never changes IM or the interrupt-enable state: the
firmware's own interrupt-driven keyboard scan depends on all of that.

Console output goes through the firmware Text VDU (`kernel/cpc/vdp.asm`,
implementing the `grid.asm` contract), keyboard input through the Key
Manager (`kernel/cpc/kbd.asm`).

### The shadow-register rule

The CPC firmware interrupt handler (`0x0038: jp 0xb941` on a 6128) starts
with `di / ex af,af' / jr c,... / exx / ... out (c),c`: it keeps its
re-entrancy flag in the carry of AF' and the Gate Array port and ROM
state in BC'. Code that runs `exx` or `ex af,af'` with interrupts
enabled corrupts those registers. The next interrupt then pages the wrong
ROM in, and the machine crashes (verified with a MAME trace).

Four shared library routines used the shadow registers. They were rewritten
to use the stack instead. Behaviour is identical, and all upstream unit tests
and shell tests still pass:

- `apps/lib/parse.asm` `parseDecimal` (exx)
- `apps/lib/util.asm` `strskip` (ex af,af')
- `apps/lib/expr.asm` `_parseNumber` (ex af,af')
- `apps/basic/buf.asm` `bufAdd` (exx)

Do not include any other module that uses `exx` or `ex af,af'` (e.g.
`kernel/kbd.asm`, `kernel/sdc.asm`) without fixing it the same way.

### Register preservation

`grid.asm` keeps its loop counter in B and buffer pointer in HL across
`GRID_SETCELL` calls, and `stdioReadLine` keeps state in B and HL across
`STDIO_GETC`. Firmware calls corrupt AF, BC, DE and HL, so `vdpSetCell` and
`kbdGetC` save and restore everything (IX and IY included).

## Firmware addresses used

| Symbol           | Address | Notes |
|------------------|---------|-------|
| KM_WAIT_CHAR     | 0xbb06  | Blocks until a key is available; A = char |
| KM_DISARM_BREAK  | 0xbb48  | So ESC doesn't inject the break token |
| TXT_WR_CHAR      | 0xbb5d  | Prints char at cursor (no control codes) |
| TXT_SET_CURSOR   | 0xbb75  | H = column, L = row, both numbered from 1 |
| TXT_CUR_DISABLE  | 0xbb7e  | grid.asm draws its own cursor |
| TXT_INVERSE      | 0xbb9c  | Used to draw the cursor |
| SCR_SET_MODE     | 0xbc0e  | A = mode; clears the screen |

All of these were checked against the jumpblock in RAM of an emulated 6128.

## Memory map

- `.org 0x4000`. Code is about 2.8K, then `RAMSTART`: grid buffer (1000
  bytes), stdio, BASIC variables and BASIC's 4K line buffer. Everything
  ends at about 0x63b1 (`.out BAS_RAMEND` prints it during the build).
- SP starts at `RAMEND = 0xa600`, below AMSDOS's workspace (0xa67b on a
  6128) and the firmware's RAM (0xb100+). The stack must stay inside
  0x4000-0xbfff. When the firmware runs (its interrupt handler included),
  it pages ROM over 0x0000-0x3fff and 0xc000-0xffff, and it uses our stack.
- Mode 1, 40x25.

## Building

```
make -C ../../emul zasm/zasm     # needs xxd installed!
make                              # os.bin, COLLAPSE.BIN, collapse.dsk
```

- `os.bin`: raw binary for address 0x4000.
- `COLLAPSE.BIN`: the same with a 128-byte AMSDOS header (type binary,
  load and exec address 0x4000). Use this one on floppy or M4 SD card.
- `collapse.dsk`: 40-track AMSDOS DATA-format disc (178K, Extended DSK
  container) holding `COLLAPSE.BIN`.

`emul/bin2c.sh` needs `xxd`. Without it, the zasm emulator is built with
empty bootstrap binaries and "hangs" on every recipe.

## Running

From floppy (real disc or `collapse.dsk` in an emulator, Gotek, HxC...):

```
RUN"COLLAPSE
```

From an M4 board: copy `COLLAPSE.BIN` to the SD card, then

```
|CD,"<folder>"    (if you put it in a folder)
RUN"COLLAPSE.BIN
```

Or keep BASIC around: `MEMORY &3FFF:LOAD"COLLAPSE.BIN":CALL &4000`.

Then type BASIC at the `>` prompt (see `apps/basic/README.md`), e.g.
`print 6*7`, `a=42`, `10 print a`, `list`, `run`.

## Verified (MAME 0.264, cpc6128 and cpc464 + DDI-1)

- `RUN"COLLAPSE`, `RUN"COLLAPSE.BIN"` and `MEMORY/LOAD/CALL` all boot to the
  `Collapse OS` banner and `>` prompt.
- Expressions, variables, negative numbers, program lines, `list`, `run`,
  `goto`/`if`, backspace (DEL), scrolling past 25 lines.
- The M4 board itself can't be emulated here. The M4 loads AMSDOS-headered
  binaries with `RUN"` like a disc drive does, but that part has not been
  tested on M4 hardware.

## Not done

- No block device or filesystem: like the sms recipe, this is a
  BASIC-shell-only port.
