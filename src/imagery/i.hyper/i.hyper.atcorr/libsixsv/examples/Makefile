# Compile all C examples against the standalone libsixsv.so built in ../testsuite/
#
#   make                 — build all examples
#   make 01_basic_lut    — build a single example
#   make run             — build and run every example
#   make clean

CC      ?= gcc
CFLAGS   = -std=c11 -O2 -I../include -Wall -Wno-unused-result
LIB_DIR  = ../testsuite
LDFLAGS  = -L$(LIB_DIR) -lsixsv -lm -Wl,-rpath,$(abspath $(LIB_DIR))

EXAMPLES = 01_basic_lut \
           02_scene_correction \
           03_retrievals \
           04_brdf \
           05_spatial_filters \
           06_full_pipeline

.PHONY: all run clean

all: $(EXAMPLES)

%: %.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@

run: all
	@for ex in $(EXAMPLES); do \
	    echo "── $$ex ────────────────────────────────"; \
	    ./$$ex; echo; \
	done

clean:
	rm -f $(EXAMPLES)
