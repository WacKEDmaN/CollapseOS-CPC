# CollapseOS -> Amstrad CPC port: working notes

Everything below was verified in this session: in source, in a ROM
disassembly or in the emulator. Things that turned out wrong are marked
"WRONG".

## Deliverables (dist/)
- dist/asm/   assembly-era Collapse OS (BASIC shell): COLLAPSE.BIN, collapse.dsk, os.bin, README.md
- dist/forth/ Forth Collapse OS 2021-04-21: COLLAPS.BAS, COLLAPS.BIN, COLLAPS.DSK,
              COLLAPS.ZIP (M4 SD card, files at zip root), os.bin, README.md
              (dist/forth/previous/ = first delivery with COLLAPSE.* names, superseded)
- dist/src/   patches against upstream (apply with patch -p1). Both rebuild byte-identical.

## Sources (collapseos.org and git.sr.ht are blocked by this sandbox's network policy;
## public GitHub clones work through the git proxy, GitHub API does not)
- Forth era (release 2021-04-21, "v1.0.0"): github.com/kizitoomoit/CollapseOS (tag v1.0.0 / branch main)
  - same content: github.com/DeltaF1/collapseos
- Assembly era (Mar 2020, 792 commits, asm kernel+apps+early forth): github.com/tcheredeev/collapseos
  - libz80 submodule pinned at github.com/ggambetta/libz80 8a1f935
- Very old asm (Oct 2019): github.com/emptymalei/collapseos
- github.com/hsoft/collapseos no longer exists.
- CPC ROMs (CRC match MAME's sets): github.com/ColinPitrat/caprice32 rom/
  - cpc6128.rom crc 9e827fe1; amsdos.rom -> rename cpcados.rom, crc 1fe22ecd; cpc464.rom crc 40852f25
  - MAME cpc464 + `-exp ddi1` wants cpcados.rom in the cpc464 rom dir too.

## Build gotchas
- asm era: emul/bin2c.sh needs `xxd`. Without it kernel-bin.h/zasm-bin.h are EMPTY arrays and
  zasm "hangs" on every recipe (CPU runs through zeroed RAM, SP=0). Fix: apt-get install xxd,
  rm the *-bin.h, rebuild. (This is the failure the user's draft README described.)
- asm era: emul/emul.c needs `#include <stdio.h>` with modern gcc.
- asm era: zasm `.out X` writes X to port 42; the emulator prints it as "Out of bounds I/O write: 42".
- Forth era: upstream ships a stale cvm/vm.o (non-PIE) -> run `make -C cvm clean` first.
- Forth era: `cd cvm && make stage` then `stage < xcomp.fs > os.bin` (stage dumps ORG@..HERE).
  blk.fs blocks: max 16 lines x 64 chars; block numbers ascending.
- Forth xcomp: host words used inside target `:` definitions must be wrapped `[ X LITN ]`.
  A bare host word inside X: ABORTs. Macros used by CODE words must be defined before
  `200 205 LOADR` (after that `:` makes target words).

## CPC firmware facts (verified in MAME 6128 RAM / ROM disassembly)
- Interrupt: &0038 = JP &B941; handler: `di / ex af,af' / jr c,.. / exx / ... out (c),c / call &00B1`.
  => firmware OWNS AF' and BC'. Any EXX / EX AF,AF' with interrupts on => crash at next
  interrupt (lower ROM not paged, execution slides through RAM). Seen with a MAME trace.
- Jumpblock: KM WAIT CHAR BB06, KM READ CHAR BB09 (carry=char in A), KM DISARM BREAK BB48,
  TXT OUTPUT BB5A, TXT WR CHAR BB5D, TXT SET CURSOR BB75 (H=col L=row, 1-based),
  TXT CUR ENABLE BB7B, TXT CUR DISABLE BB7E, TXT CUR ON BB81, TXT INVERSE BB9C, SCR SET MODE BC0E,
  CAS IN OPEN BC77 (B=len HL=name DE=2K buf; carry=ok), CAS IN CLOSE BC7A, CAS IN DIRECT BC83
  (HL=dest), CAS OUT OPEN BC8C, CAS OUT CLOSE BC8F, CAS OUT ABANDON BC92,
  CAS OUT DIRECT BC98 (HL=src DE=len BC=exec A=type), KL FIND COMMAND BCD4 (carry, HL=addr, C=rom),
  KL FAR PCHL at RAM &001B (call RSX: A=nargs IX=arg list).
- `RUN"file.BIN"` resets the firmware: background ROMs (AMSDOS/M4) are gone afterwards,
  CAS calls go to tape ("Press PLAY then any key:"). Use a BASIC loader + CALL instead.
- BASIC `LOAD"x",addr` refuses addr below HIMEM ("Memory full") and needs a 4K buffer below
  HIMEM, so `MEMORY &FFF` also fails. To put code low: POKE a small stub that uses CAS IN DIRECT.
- `RUN"NAME"` without extension tries NAME, then NAME.BAS, then NAME.BIN.
- AMSDOS always prints "<name> not found" on a failed CAS IN OPEN; no flag disables it
  (traced: CEC4 jp nc,D50C -> ld a,6 -> CDB1 -> print). WRONG idea: POKE &BE78,&FF does not help.
- CAS IN DIRECT does NOT work for headerless files (nothing loaded). Keep AMSDOS headers.
- Saving over an existing file renames the old one to .BAK. |ERA "x.BAK" via KL FIND COMMAND works.
- While AMSDOS transfers sectors, interrupts are off: keys pressed then can be missed
  (MAME natkeyboard drops chars typed during disc I/O).
- Firmware routines and their buffers/stack must be in &4000-&BFFF (ROM paging).
- Interrupts push onto whatever SP is: keep stacks in central RAM.

## Emulator harness (/home/user/cpc/emu)
- MAME 0.264 (apt `mame`, binary /usr/games/mame). run.sh <system> <dsk> <steps> <snapdir>
  SYSEXTRA="-exp ddi1" for cpc464 disc; MAMEXTRA="-debug -debugger none" for traces.
- steps: "frame|text@@frame|SNAP@@frame|REGS@@frame|DBG trace file,maincpu,noloop@@frame|EXIT"
  text: \n = Enter, \b = DEL. Don't use ';' as separator (Forth uses it).
- tools/cpcocr.py snap.png [40|80] -> text of the screen (font from ROM &3800; active area x=64 y=37).
- Profiling: sampling PC at frame end is BIASED (always hits the keyboard scan at &1D6x).
  Use a debugger trace window and histogram PCs instead.
- Natkeyboard keys typed while the CPC is busy can be lost: type only after the previous
  command has finished.
- MAME does not write floppy changes back to the .dsk host file in these runs: check writes
  inside the emulation (evict cache, re-read, CAT in BASIC after BYE).

## Port design decisions
- asm: kept the user's draft (firmware-resident, mode 1, grid via TXT), fixed: org 0x8000->0x4000
  (RAM would overrun AMSDOS area), SP 0xbfff->0xa600, register preservation in vdpSetCell/kbdGetC,
  ESC break disarm, grid buffer clear; rewrote 4 lib routines that used EXX/EX AF,AF'
  (parse.asm, util.asm strskip, expr.asm, basic/buf.asm). Upstream unit + shell tests still pass.
- forth: B370 redefines assembler words EXX, EXAFAF' (swap with RAM slots) and HALT, (JP 0),
  loaded before B280, so upstream kernel blocks are unchanged. Drivers in B371-B377.
  Blocks = AMSDOS files of 8 blocks (Bnnn.BLK), 2-slot LRU cache, write-through, .BAK erased.
  Kernel at 0x0400 loaded by a 42-byte stub POKEd by COLLAPSE.BAS.
- DSK: 40-track DATA format in an Extended DSK container (user OK'd EDSK/80 track; 80 track
  not usable by stock AMSDOS, so not used).

## M4 board (user feedback, 2026-10-21)
- User: M4 could not enter a folder whose name is longer than 8 chars, and they renamed
  COLLAPSE -> COLLAPS. Rule: EVERY name the CPC sees (files AND folders, zip root folders)
  must be 8.3 or shorter. Forth port now uses COLLAPS.BAS/.BIN, zip with files at its root.
- "LIST" alone -> "stack underflow" is normal Collapse OS (LIST takes a block number:
  "0 LIST"); same in upstream cvm. Not an M4 problem.

## Not verified
- M4 board (no emulation available). It uses the same CAS vectors, so it should work.

## GitHub repo (/home/user/cpc/github/collapseos-cpc, zip next to it)
- Built from PRISTINE upstream (git archive of the mirrors) + dist/src patches, not from the
  working trees (those have build leftovers).
- Upstream snapshots contain build artifacts: forth cvm/stage, cos-*, vm.o (non-PIE, breaks
  linking), blkfs, grid.bin, emul/z80/*.o, emul/z80/rc2014, memdump, tools/blkpack, tools/common.o.
  Removed in the repo; keep serial.bin, zasm.bin, kernel.bin, z80c.bin, fonts, emul/z80/forth.bin.
- TRAP: upstream asm nested .gitignore files ignore files that upstream tracks (emul/*/*.bin
  bootstrap binaries, recipes/sms/romasm/user.h). In a fresh repo `git add .` silently drops
  them. Fixed with negation rules; verify with git init + git add -A + compare file counts.
- asm libz80 submodule can't nest: asm/emul/get-libz80.sh clones the pinned commit.
- TRAP: Git for Windows (core.autocrlf=true) strips the CRs from COLLAPS.BAS (ASCII BASIC,
  CR LF + 0x1A) on commit (286 -> 280 bytes, verified). Repo has .gitattributes marking
  *.BAS/*.BIN/*.DSK/*.BLK/*.ZIP and release/** binary.
- GitHub push "rejected (non-fast-forward)" on a new repo = GitHub created a README/LICENSE
  commit at creation. Create repos EMPTY, or force-push if the remote only has starter files.
