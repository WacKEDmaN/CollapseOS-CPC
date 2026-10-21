; vdp - console on the CPC's Text VDU (firmware)
;
; Implements the grid.asm contract (GRID_SETCELL, an init routine, GRID_COLS
; and GRID_ROWS) by calling the resident CPC firmware's Text VDU jumpblock.
; This port never disables the firmware ROM and never touches the
; interrupt vector table: it only calls into firmware that is already
; running.
;
; grid.asm addresses cells by row D and column E, both numbered from zero.
; The firmware's TXT_SET_CURSOR expects logical column/row numbered from
; one, so this driver adds one to each coordinate before calling it.
;
; Cursor highlighting (the C parameter of GRID_SETCELL) is implemented by
; swapping pen and paper ink around the character write with TXT_INVERSE,
; then swapping back.
;
; grid.asm's gridPushRow keeps its loop counter in B and its buffer pointer
; in HL across GRID_SETCELL calls, so vdpSetCell must preserve every register
; it is given. The firmware calls below corrupt AF, BC, DE and HL.
;
; *** Defines ***
; VDP_RAMSTART: must be defined by the includer before this file.
;
; *** Consts ***
;
.equ	TXT_WR_CHAR	0xbb5d
.equ	TXT_SET_CURSOR	0xbb75
.equ	TXT_CUR_DISABLE	0xbb7e
.equ	TXT_INVERSE	0xbb9c
.equ	SCR_SET_MODE	0xbc0e

; Mode 1: 320x200 pixels, 40x25 characters, 4 inks. Chosen over mode 2
; (80x25, 2 inks) for legibility on a TV/composite display.
.equ	VDP_MODE	1
.equ	VDP_COLS	40
.equ	VDP_ROWS	25

; *** Variables ***
;
; Holds the cursor-highlight flag (grid.asm's C parameter) across the
; firmware calls.
.equ	VDP_CURFLAG	VDP_RAMSTART
.equ	VDP_RAMEND	@+1

; *** Code ***

vdpInit:
	push	ix
	push	iy
	ld	a, VDP_MODE
	call	SCR_SET_MODE
	; grid.asm draws its own cursor via the C parameter of GRID_SETCELL;
	; disable the firmware's own blinking cursor to avoid showing two.
	call	TXT_CUR_DISABLE
	pop	iy
	pop	ix
	ret

; grid routine. Sets cell at row D and column E to character A. If C is
; nonzero, display it highlighted as the cursor. Preserves all registers.
vdpSetCell:
	push	af
	push	bc
	push	de
	push	hl
	push	ix
	push	iy
	push	af		; --> lvl 1: char
	ld	a, c
	ld	(VDP_CURFLAG), a
	or	a
	jr	z, .skipinv1
	push	de
	call	TXT_INVERSE
	pop	de
.skipinv1:
	; TXT_SET_CURSOR wants H = logical column, L = logical row, both
	; numbered from one.
	ld	a, e
	inc	a
	ld	h, a
	ld	a, d
	inc	a
	ld	l, a
	call	TXT_SET_CURSOR
	pop	af		; <-- lvl 1: char
	call	TXT_WR_CHAR
	ld	a, (VDP_CURFLAG)
	or	a
	jr	z, .end
	call	TXT_INVERSE
.end:
	pop	iy
	pop	ix
	pop	hl
	pop	de
	pop	bc
	pop	af
	ret
