# Amstrad CPC. See README.md
TARGET = os.bin
BASE = ../../..
STAGE = $(BASE)/cvm/stage
TOOLS = $(BASE)/tools/cpc
BLKFS = $(BASE)/cvm/blkfs

.PHONY: all
all: $(TARGET) COLLAPS.BIN COLLAPS.BAS COLLAPS.DSK COLLAPS.ZIP

# CPC (AMSDOS and M4) names must be 8.3 at most: the program is COLLAPS

$(TARGET): xcomp.fs $(STAGE) $(BLKFS)
	$(STAGE) < xcomp.fs > $@

$(STAGE) $(BLKFS): $(BASE)/blk.fs
	$(MAKE) -C $(BASE)/cvm stage

COLLAPS.BIN: $(TARGET)
	python3 $(TOOLS)/amsdos.py --load 0x0400 --exec 0x0400 $(TARGET) $@

# Boot stub, POKEd at 0x9000 by the BASIC loader. Loads COLLAPS.BIN
# below HIMEM, which BASIC's own LOAD refuses to do.
boot.bin: boot.fs $(STAGE) $(BLKFS)
	$(STAGE) < boot.fs > $@

COLLAPS.BAS: boot.bin
	python3 $(TOOLS)/mkloader.py boot.bin 0x9000 0x9fff $@

# Block groups: B000.BLK = blocks 0-7, B008.BLK = blocks 8-15...
blkgroups: $(BLKFS)
	rm -rf $@ && mkdir $@
	python3 $(TOOLS)/blkgroups.py $(BLKFS) $@

# The DSK only holds the groups useful on a CPC (a DATA disc is 178K)
DSKGROUPS = 0 8 16 96 104 112 200 208 216 224 232 280 288 296 368
COLLAPS.DSK: COLLAPS.BIN COLLAPS.BAS blkgroups
	python3 $(TOOLS)/mkdsk.py $@ COLLAPS.BAS COLLAPS.BIN \
		$(foreach g,$(DSKGROUPS),blkgroups/B$(shell printf %03d $(g)).BLK)

# For the M4 board: COLLAPS.ZIP holds the loader, the kernel and all
# non-empty groups at its root. Unzip into a folder with an 8.3 name.
COLLAPS.ZIP: COLLAPS.BIN COLLAPS.BAS blkgroups
	rm -f $@
	python3 -c "import zipfile,glob; z=zipfile.ZipFile('$@','w',zipfile.ZIP_DEFLATED); [z.write(f,f.split('/')[-1]) for f in ['COLLAPS.BAS','COLLAPS.BIN']+sorted(glob.glob('blkgroups/*.BLK'))]"

.PHONY: clean
clean:
	rm -rf $(TARGET) boot.bin COLLAPS.BIN COLLAPS.BAS COLLAPS.DSK COLLAPS.ZIP blkgroups m4 \
		COLLAPSE.BIN COLLAPSE.BAS collapse.dsk
