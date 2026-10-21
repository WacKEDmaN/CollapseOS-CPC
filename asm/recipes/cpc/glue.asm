; Amstrad CPC glue file
;
; Unlike the rc2014 and sms recipes, this port does not own the machine from
; reset: the CPC firmware ROM stays resident and enabled the whole time. This
; program is loaded into free RAM and CALLed (or RUN) from BASIC like any other
; machine-code program; it never writes to address 0, never patches the
; RST 0x38 vector, and never touches IM or the interrupt-enable state, because
; the firmware's own interrupt-driven keyboard scan depends on all of that
; being left alone. See kernel/cpc/kbd.asm and kernel/cpc/vdp.asm for how it
; calls back into that resident firmware.
;
; Memory map:
;   0x4000 - code, then RAMSTART (grid buffer, stdio, BASIC vars and its 4K
;            buffer pool). Everything must end below RAMEND.
;   RAMEND = 0xa600 is our initial SP. It is below AMSDOS's workspace (which
;            starts around 0xa67b on a 6128) and below the firmware's own RAM
;            (0xb100+). The stack must stay within 0x4000-0xbfff because the
;            firmware pages ROM over 0x0000-0x3fff and 0xc000-0xffff when it
;            runs (interrupts included), and those use our stack.
; RAMSTART is a label placed at the end of this file, so it always sits exactly
; where the assembled code ends (same technique as the trs80 recipe).
;
.equ	RAMEND		0xa600

.org	0x4000
	jp	init

.inc "err.h"
.inc "ascii.h"
.inc "core.asm"
.inc "str.asm"

.inc "cpc/kbd.asm"
.equ	VDP_RAMSTART	RAMSTART
.inc "cpc/vdp.asm"

.equ	GRID_RAMSTART	VDP_RAMEND
.equ	GRID_COLS	VDP_COLS
.equ	GRID_ROWS	VDP_ROWS
.equ	GRID_SETCELL	vdpSetCell
.equ	GRID_GETC	kbdGetC
.inc "grid.asm"

.equ	STDIO_RAMSTART	GRID_RAMEND
.equ	STDIO_GETC	gridGetC
.equ	STDIO_PUTC	gridPutC
.equ	STDIO_SETCUR	gridSetCurH
.inc "stdio.asm"

; *** BASIC ***

; RAM space used in different routines for short term processing.
.equ	SCRATCHPAD_SIZE	STDIO_BUFSIZE
.equ	SCRATCHPAD	STDIO_RAMEND
.inc "lib/util.asm"
.inc "lib/ari.asm"
.inc "lib/parse.asm"
.inc "lib/fmt.asm"
.equ	EXPR_PARSE	parseLiteralOrVar
.inc "lib/expr.asm"
.inc "basic/util.asm"
.inc "basic/parse.asm"
.inc "basic/tok.asm"
.equ	VAR_RAMSTART	SCRATCHPAD+SCRATCHPAD_SIZE
.inc "basic/var.asm"
.equ	BUF_RAMSTART	VAR_RAMEND
.inc "basic/buf.asm"
.equ	BAS_RAMSTART	BUF_RAMEND
.inc "basic/main.asm"

.out	BAS_RAMEND

init:
	; Do NOT di/ei or set IM here: the firmware is already running with
	; interrupts enabled and IM 1, and its keyboard scan depends on that.
	; We only take over the stack, which is safe and standard practice
	; for any machine-code program taking over from BASIC.
	ld	sp, RAMEND

	; Our RAM (everything from RAMSTART to BAS_RAMEND) holds whatever was
	; in memory before we were loaded. gridInit only clears its first 256
	; bytes, so we zero it all ourselves. A zero cell displays as a space.
	ld	hl, RAMSTART
	ld	de, RAMSTART+1
	ld	bc, BAS_RAMEND-RAMSTART
	ld	(hl), 0
	ldir

	call	kbdInit
	call	gridInit
	call	vdpInit
	call	basInit
	jp	basStart

RAMSTART:
