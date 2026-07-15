# lib6sv testsuite — builds a standalone shared library and runs all tests.
#
# Targets:
#   make          — build libsixsv.so and the Fortran compatibility driver
#   make test     — run all Python tests via pytest (falls back to unittest)
#   make test-fortran — run only the Fortran-compatibility subset
#   make test-openmp  — run only the OpenMP / GPU tests
#   make clean    — remove built artefacts
#
# Variables (override on the command line as needed):
#   CC            — C compiler            (default: gcc)
#   FC            — Fortran compiler      (default: gfortran)
#   OFFLOAD_FLAGS — OpenMP target-offload flags copied from the parent Makefile
#   SIXSV2        — path to 6SV2.1 Fortran sources (default: ~/dev/6sV2.1)

SIXSV_DIR = ..
SIXSV2    = $(HOME)/dev/6sV2.1

CC  ?= gcc
FC  ?= gfortran

# Inherit offload flags from the parent build if not set independently
OFFLOAD_FLAGS ?=

CFLAGS  = -std=c11 -O2 -fPIC -fopenmp $(OFFLOAD_FLAGS) \
          -I$(SIXSV_DIR)/include -I$(SIXSV_DIR)/src \
          -Wall -Wno-unused-parameter
LDFLAGS = -shared -lm -fopenmp $(OFFLOAD_FLAGS)

LIB_SO   = libsixsv.so
LIB_SRCS = $(sort $(wildcard $(SIXSV_DIR)/src/*.c))

FORTRAN_DRIVER = test_6sv_compat
FORTRAN_OBJS   = $(addprefix $(SIXSV2)/, \
                   CHAND.o ODRAYL.o VARSOL.o SOLIRR.o CSALBR.o GAUSS.o US62.o)

.PHONY: all lib fortran test test-fortran test-openmp clean

all: lib fortran

# ── Standalone shared library ─────────────────────────────────────────────────
lib: $(LIB_SO)

$(LIB_SO): $(LIB_SRCS)
	$(CC) $(CFLAGS) $(LDFLAGS) $^ -o $@

# ── Fortran compatibility driver ──────────────────────────────────────────────
fortran: $(FORTRAN_DRIVER)

$(FORTRAN_DRIVER): test_6sv_compat.f90 $(FORTRAN_OBJS)
	$(FC) -O $^ -lm -o $@

# Build any missing 6SV2.1 .o files from source
$(SIXSV2)/%.o: $(SIXSV2)/%.f
	$(FC) -O -c $< -o $@

# ── Run tests ─────────────────────────────────────────────────────────────────
PYTEST_CMD = LIB_SIXSV=$(CURDIR)/$(LIB_SO) python3 -m pytest -v --tb=short
UNITTEST_CMD = LIB_SIXSV=$(CURDIR)/$(LIB_SO) python3 -m unittest

test: lib fortran
	$(PYTEST_CMD) . || $(UNITTEST_CMD) discover -v

test-fortran: lib fortran
	$(PYTEST_CMD) test_fortran_compat.py test_lut.py test_solar.py \
	  || $(UNITTEST_CMD) test_fortran_compat test_lut test_solar

test-openmp: lib
	$(PYTEST_CMD) test_openmp.py || $(UNITTEST_CMD) test_openmp

clean:
	rm -f $(LIB_SO) $(FORTRAN_DRIVER) __pycache__ *.pyc
	rm -rf __pycache__ .pytest_cache
