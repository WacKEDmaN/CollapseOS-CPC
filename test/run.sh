#!/bin/sh
# Run a CPC in MAME headless, type into it and take screenshots.
# usage: run.sh <system> <dsk-or-""> <steps> <outdir>
#   system: cpc6128, or cpc464 with SYSEXTRA="-exp ddi1" for a disc drive
#   steps:  "frame|text@@frame|SNAP@@frame|REGS@@frame|DBG <cmd>@@frame|EXIT"
#           text: \n = Enter, \b = DEL
# ROMs: $CPC_ROMS (default: test/roms) must hold cpc6128/{cpc6128,cpcados}.rom
#       and cpc464/{cpc464,cpcados}.rom. See test/README.md.
# MAMEXTRA="-debug -debugger none" enables "DBG trace ..." steps.
HERE=$(cd "$(dirname "$0")" && pwd)
ROMS=${CPC_ROMS:-$HERE/roms}
SYS="$1"; DSK=$2; export CPC_STEPS="$3"; OUT=$4
rm -rf "$OUT"; mkdir -p "$OUT/cfg" "$OUT/nv"
FLOP=""; [ -n "$DSK" ] && FLOP="-flop1 $DSK"
MAME=${MAME:-$(command -v mame || echo /usr/games/mame)}
timeout 300 "$MAME" $SYS $SYSEXTRA -rompath "$ROMS" -video none -sound none -nothrottle \
  -skip_gameinfo $MAMEXTRA -snapshot_directory "$OUT" -cfg_directory "$OUT/cfg" \
  -nvram_directory "$OUT/nv" $FLOP -autoboot_script "$HERE/typetest.lua" \
  2>&1 | grep -v -E "XDG_RUNTIME|ALSA|doesn't make much sense"
ls "$OUT"/cpc*/ 2>/dev/null
