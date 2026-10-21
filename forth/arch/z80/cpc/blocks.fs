( ----- 370 )
( Amstrad CPC declarations. Load before B280. The firmware's
  interrupt handler owns BC' and AF', so EXX, and EXAFAF' are
  replaced by swaps with RAM slots. HALT, (only used by BYE)
  jumps to the reset vector. Needs DRVMEM CASBUF GRPBUF. )
: _d DRVMEM + CONSTANT ; 0 _d _xslot 2 _d _aslot 4 _d _deslot
6 _d _fwtgt 8 _d _xymode 0x0a _d _lru 0x0c _d _fnam ( 8b )
0x14 _d _bak ( 8b ) 0x1c _d _desc ( 3b ) 0x20 _d _plist
0x22 _d _cmd ( 3b ) 0x26 _d _gtab ( 8b )
: EXX, HL PUSH, _xslot LDHL(i), EXDEHL, _xslot LD(i)HL,
  HL POP, ;
: EXAFAF', HL PUSH, AF PUSH, _aslot LDHL(i), EX(SP)HL,
  _aslot LD(i)HL, AF POP, HL POP, ;
: HALT, 0 JP, ;
: FW< _deslot DE LD(i)d, IX PUSH, IY PUSH, ;
: FW> IY POP, IX POP, DE _deslot LDd(i), ;
( ----- 371 )
( Amstrad CPC drivers. Load range: B371-B377 )
( pop args before FW< : it pushes IX IY )
CODE (emit) 1 chkPS, HL POP, FW< A L LDrr, 0xbb5a CALL,
  FW> ;CODE
( Chars >= 0x80 [cursor keys, COPY...] are ignored )
CODE (key?) FW< 0xbb09 CALL, FW> IFC, 0x80 CPi, IFC,
    PUSHA, PUSH1, ELSE, PUSH0, THEN,
  ELSE, PUSH0, THEN, OFLW? ;CODE
CODE AT-XY ( x y -- ) 2 chkPS, HL POP, BC POP, FW<
  H C LDrr, H INCr, L INCr, 0xbb75 CALL, FW> ;CODE
CODE CMOVE ( src dst u -- ) 3 chkPS, _deslot DE LD(i)d,
  BC POP, DE POP, HL POP, A B LDrr, C ORr, IFNZ, LDIR, THEN,
  DE _deslot LDd(i), ;CODE
( ----- 372 )
( FW: call firmware routine at addr. AF BC DE HL are set from
  the stack and returned. A is af's MSB, carry is af's bit 0 )
CODE FW ( af bc de hl addr -- af bc de hl ) 5 chkPS,
  _deslot DE LD(i)d, HL POP, _fwtgt LD(i)HL,
  HL POP, DE POP, BC POP, AF POP, IX PUSH, IY PUSH,
  JR, L2 FWR L3 BSET HL PUSH, _fwtgt LDHL(i), EX(SP)HL, RET,
  L2 FSET L3 @ CALL, IY POP, IX POP,
  AF PUSH, BC PUSH, DE PUSH, HL PUSH, DE _deslot LDd(i), ;CODE
: FW0 ( addr -- ) >R 0 0 0 0 R> FW 2DROP 2DROP ;
: MODE ( n -- ) 8 LSHIFT 0 0 0 0xbc0e FW 2DROP 2DROP ;
80 CONSTANT COLS 25 CONSTANT LINES
_xymode CONSTANT XYMODE
: CELL! ( c pos -- ) COLS /MOD AT-XY (emit) ;
( ----- 373 )
( CPC$: mode 2, ESC break off, firmware text cursor on )
: CPC$ 2 MODE 0xbb48 FW0 0xbb7b FW0 0xbb81 FW0 ;
( Blocks live in AMSDOS files of 8 blocks: Bnnn.BLK holds
  blocks nnn to nnn+7. Works on floppy and on M4 SD cards. )
GRPBUF CONSTANT GRPBUF
: _cf ( af -- f ) 1 AND ;
: _nam ( g -- ) 3 LSHIFT
  10 /MOD SWAP '0' + [ _fnam 3 + LITN ] C!
  10 /MOD SWAP '0' + [ _fnam 2 + LITN ] C!
  '0' + [ _fnam 1+ LITN ] C! ;
: _open ( addr -- f ) >R 0 0x0800 [ CASBUF LITN ]
  [ _fnam LITN ] R> FW 2DROP DROP _cf ;
( ----- 374 )
( AMSDOS prints "Bnnn.BLK not found" for a missing group )
: _rd ( a -- f, read file _fnam to a )
  >R 0xbc77 ( CAS IN OPEN ) _open IF
    0 0 0 R> 0xbc83 ( CAS IN DIRECT ) FW 2DROP DROP _cf
    0xbc7a ( CAS IN CLOSE ) FW0
  ELSE R> DROP 0 THEN ;
: _wr ( a -- f, write 8K at a to file _fnam )
  >R 0xbc8c ( CAS OUT OPEN ) _open IF
    0x0200 0 0x2000 R> 0xbc98 ( CAS OUT DIRECT )
    FW 2DROP DROP _cf IF 0 0 0 0 0xbc8f ( CAS OUT CLOSE )
      FW 2DROP DROP _cf
    ELSE 0xbc92 ( CAS OUT ABANDON ) FW0 0 THEN
  ELSE R> DROP 0 THEN ;
( ----- 375 )
( Call RSX at far addr hl/c with A=a args at IX=ix )
CODE (rsx) ( a c hl ix -- ) 4 chkPS, _deslot DE LD(i)d,
  DE POP, HL POP, BC POP, AF POP, IX PUSH, IY PUSH,
  DE PUSH, IX POP, 0x1b ( KL FAR PCHL ) CALL,
  IY POP, IX POP, DE _deslot LDd(i), ;CODE
( Saving over a file leaves a .BAK: erase it with |ERA )
: _era ( -- ) [ _fnam LITN ] [ _bak LITN ] 5 CMOVE
  LIT" BAK" 1+ [ _bak 5 + LITN ] 3 CMOVE
  8 [ _desc LITN ] C! [ _bak LITN ] [ _desc 1+ LITN ] !
  [ _desc LITN ] [ _plist LITN ] !
  0 0 0 [ _cmd LITN ] 0xbcd4 ( KL FIND COMMAND ) FW
  NIP ROT _cf IF 0x100 ROT> [ _plist LITN ] (rsx)
  ELSE 2DROP THEN ;
( ----- 376 )
( GRPBUF has 2 8K slots, each caching a group. _gtab holds
  group and "file exists" per slot. _lru: next slot to reuse )
: _sa ( slot -- a ) 13 LSHIFT GRPBUF + ;
: _sg ( slot -- a ) 2 LSHIFT [ _gtab LITN ] + ;
: _grp ( g -- slot, get group g in a slot )
  2 0 DO DUP I _sg @ = IF DROP I 1 XOR [ _lru LITN ] !
    I UNLOOP EXIT THEN LOOP
  [ _lru LITN ] @ DUP 1 XOR [ _lru LITN ] ! ( g slot )
  TUCK _sg ! DUP _sg @ _nam DUP _sa _rd ( slot f )
  OVER _sg 2 + ! DUP _sg 2 + @ NOT IF ( no file: empty )
    DUP _sa 0 OVER C! DUP 1+ 0x1fff CMOVE THEN ;
: FD@ ( blk -- ) DUP 3 RSHIFT _grp _sa SWAP 7 AND 10 LSHIFT +
  BLK( 1024 CMOVE ;
( ----- 377 )
: FD! ( blk -- ) DUP 3 RSHIFT _grp ( blk slot ) SWAP 7 AND
  10 LSHIFT OVER _sa + BLK( SWAP 1024 CMOVE ( slot )
  DUP _sg @ _nam DUP _sa _wr NOT IF _sg -1 SWAP !
    LIT" DSKerr" ERR THEN
  _sg 2 + DUP @ IF _era THEN 1 SWAP ! ;
: FD$ ['] FD@ ['] BLK@* **! ['] FD! ['] BLK!* **!
  -1 [ _gtab LITN ] ! -1 [ _gtab 4 + LITN ] ! 0 [ _lru LITN ] !
  LIT" B000.BLK" 1+ [ _fnam LITN ] 8 CMOVE
  LIT" ERA" 1+ [ _cmd LITN ] 3 CMOVE
  'A' 0x80 OR [ _cmd 2 + LITN ] C! ;
