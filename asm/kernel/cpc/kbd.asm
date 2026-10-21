; kbd - keyboard input via the CPC firmware Key Manager
;
; This port leaves the CPC firmware ROM resident: the interrupt vector table,
; the RST 0x38 handler and IM 1 are never touched, so the firmware's own
; interrupt-driven keyboard scan keeps running exactly as it does under
; BASIC. This module only exposes KM_WAIT_CHAR as a GRID_GETC-compatible
; routine.
;
; IMPORTANT: the firmware interrupt handler (verified at 0xb941 in a 6128) uses
; AF' and BC' for its own purposes. No code running under this port may use
; "exx" or "ex af, af'" while interrupts are enabled.
;
; *** Consts ***
;
.equ	KM_WAIT_CHAR	0xbb06
.equ	KM_DISARM_BREAK	0xbb48

; *** Code ***

; Disarm the firmware's ESC "break" mechanism. Without this, pressing ESC
; inserts the break token into the key buffer.
kbdInit:
	push	ix
	push	iy
	call	KM_DISARM_BREAK
	pop	iy
	pop	ix
	ret

; Wait for the next character from the keyboard and return it in A.
; Suitable for direct use as GRID_GETC. Callers (stdioReadLine) keep state
; in BC and HL, so everything but A is preserved. Characters >= 0x80
; (cursor keys, COPY, function-key tokens...) are ignored: Collapse OS only
; deals in ASCII.
kbdGetC:
	push	bc
	push	de
	push	hl
	push	ix
	push	iy
.loop:
	call	KM_WAIT_CHAR
	cp	0x80
	jr	nc, .loop
	pop	iy
	pop	ix
	pop	hl
	pop	de
	pop	bc
	ret
