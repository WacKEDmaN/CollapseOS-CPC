# Testing in MAME

Everything in this port was tested headless in MAME 0.264 with these scripts.

## Setup

    sudo apt-get install mame          # binary may be /usr/games/mame
    git clone --depth 1 https://github.com/ColinPitrat/caprice32 /tmp/caprice32
    mkdir -p test/roms/cpc6128 test/roms/cpc464
    cp /tmp/caprice32/rom/cpc6128.rom test/roms/cpc6128/
    cp /tmp/caprice32/rom/amsdos.rom  test/roms/cpc6128/cpcados.rom
    cp /tmp/caprice32/rom/cpc464.rom  test/roms/cpc464/
    cp /tmp/caprice32/rom/amsdos.rom  test/roms/cpc464/cpcados.rom

The ROM CRCs MAME expects: cpc6128.rom 9e827fe1, cpcados.rom 1fe22ecd,
cpc464.rom 40852f25. The ROMs are not included in this repository.

## Run

    test/run.sh cpc6128 release/forth/COLLAPS.DSK \
      '100|RUN"COLLAPS"\n@@600|0 LIST\n@@1100|SNAP@@1110|EXIT' test/out/t1
    python3 test/cpcocr.py test/out/t1/cpc6128/0000.png 80

`cpcocr.py` turns a screenshot into text (40 columns for mode 1, 80 for
mode 2). A CPC 464 with disc drive: `SYSEXTRA="-exp ddi1" test/run.sh cpc464 ...`.

Tips:
- 50 frames = 1 second. Boot takes ~100 frames, a disc load a few hundred.
- Type the next command only after the previous one finished: keys typed
  while the CPC is busy or doing disc I/O get dropped.
- MAME doesn't write disc changes back to the .dsk here: check writes from
  inside the emulation (e.g. `BYE` then `CAT`).
- Instruction trace: `MAMEXTRA="-debug -debugger none"` plus steps
  `N|DBG trace /abs/path/t.log,maincpu,noloop@@M|DBG trace off,maincpu`.
