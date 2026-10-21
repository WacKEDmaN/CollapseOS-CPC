( CPC boot stub. The BASIC loader POKEs it at 0x9000 and CALLs
  it. It reads COLLAPS.BIN to 0x0400 through AMSDOS [or the
  M4 board], so the kernel can live below BASIC's HIMEM. )
5 LOAD ( z80 assembler )
0x9000 BIN( ! HERE ORG !
JR, L1 FWR L2 BSET ," COLLAPS.BIN" L1 FSET
B 11 LDri, HL L2 @ LDdi, DE 0x8000 LDdi,
0xbc77 ( CAS IN OPEN ) CALL, IFC,
  HL 0x0400 LDdi, 0xbc83 ( CAS IN DIRECT ) CALL, IFC,
    0xbc7a ( CAS IN CLOSE ) CALL, 0x0400 JP, THEN, THEN,
RET, ( failed: back to BASIC, AMSDOS printed why )
