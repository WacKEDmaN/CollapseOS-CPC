# Amstrad CPC recipe. See README.md
TARGET = os.bin
BASEDIR = ../..
ZASM = $(BASEDIR)/emul/zasm/zasm
KERNEL = $(BASEDIR)/kernel
APPS = $(BASEDIR)/apps
TOOLS = $(BASEDIR)/tools/cpc

.PHONY: all
all: $(TARGET) collapse.dsk

$(TARGET): glue.asm $(wildcard $(KERNEL)/*.asm $(KERNEL)/cpc/*.asm $(APPS)/*/*.asm)
	$(ZASM) $(KERNEL) $(APPS) < glue.asm > $@

# COLLAPSE.BIN: os.bin with an AMSDOS header (load/exec 0x4000).
COLLAPSE.BIN: $(TARGET)
	python3 $(TOOLS)/amsdos.py --load 0x4000 --exec 0x4000 $(TARGET) $@

collapse.dsk: COLLAPSE.BIN
	python3 $(TOOLS)/mkdsk.py $@ COLLAPSE.BIN

.PHONY: clean
clean:
	rm -f $(TARGET) COLLAPSE.BIN collapse.dsk
