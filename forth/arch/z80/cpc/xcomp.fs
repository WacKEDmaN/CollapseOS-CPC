( Amstrad CPC 464/664/6128, firmware resident. See README.md )
( Memory map: kernel at 0x0400 [loaded by boot.fs], dictionary
  above it up to CASBUF. CASBUF 2K AMSDOS buffer, GRPBUF two 8K
  block-group slots, SYSVARS+DRVMEM, RS grows up from 0x9c00,
  PS down from 0x9ffe.
  Stacks must stay in 0x4000-0xbfff: the firmware pages ROMs
  over the rest and its interrupt handler uses our stack. )
0x9ffe CONSTANT PS_ADDR    0x9c00 CONSTANT RS_ADDR
0x9b00 CONSTANT SYSVARS    SYSVARS 0xa0 + CONSTANT DRVMEM
0 CONSTANT HERESTART
0x5b00 CONSTANT GRPBUF     0x5300 CONSTANT CASBUF
5 LOAD   ( z80 assembler )
370 LOAD ( cpc decl, before boot.z80.decl )
280 LOAD ( boot.z80.decl )
22 tickfactor ! ( 4MHz, CPC rounds to 4 T-states )
200 205 LOADR ( xcomp )
0x0400 BIN( !
281 300 LOADR ( boot.z80 )
210 231 LOADR ( forth core low )
371 377 LOADR ( cpc drivers )
236 239 LOADR ( forth core high )
XWRAP" CPC$ BLK$ FD$ "
