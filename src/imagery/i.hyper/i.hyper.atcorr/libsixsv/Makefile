MODULE_TOPDIR = ../grass

# ── Library identity ───────────────────────────────────────────────────────────
# Follows the GRASS naming convention: grass_<name>.<MAJOR>.<MINOR>
# GRASS_LIB_VERSION_NUMBER is a recursive variable defined in Grass.make and
# therefore available once the include chain below has run.
LIB_NAME = grass_sixsv.$(GRASS_LIB_VERSION_NUMBER)

# ── Sources (all in src/, zero GRASS dependencies) ────────────────────────────
LIBSRCS  := $(sort $(wildcard src/*.c))
MOD_OBJS  = $(notdir $(LIBSRCS:.c=.o))

# ── Compiler / linker flags ────────────────────────────────────────────────────
EXTRA_INC    = -Iinclude -Isrc

# ── OpenMP GPU offload auto-detection ─────────────────────────────────────────
# If OFFLOAD_FLAGS is already defined (command line or environment) it is used
# as-is and all detection is skipped.  Otherwise the build system:
#   1. Detects the GPU vendor via nvidia-smi / rocminfo.
#   2. Picks candidate compiler flags for the detected GPU and compiler family.
#   3. Verifies the flags compile a minimal OpenMP target program.
#   4. Sets OFFLOAD_FLAGS to the verified flags, or leaves it empty on failure.
#
# To override detection:
#   make OFFLOAD_FLAGS="--offload-arch=sm_86"   # Clang + specific NVIDIA arch
#   make OFFLOAD_FLAGS="-foffload=nvptx-none"   # GCC  + NVIDIA (generic nvptx)
#   make OFFLOAD_FLAGS="--offload-arch=gfx1030" # Clang + AMD
#   make OFFLOAD_FLAGS=                         # force CPU-only OpenMP
#
# Detection uses _Pragma() in the probe source (not #pragma) so that Make does
# not misinterpret '#' as a comment inside the $(shell ...) expression.

ifeq ($(origin OFFLOAD_FLAGS), undefined)

  _CC_IS_CLANG := $(shell $(CC) --version 2>&1 | grep -c clang)

  # ── NVIDIA: nvidia-smi reports compute capability as "X.Y" (e.g. "8.6") ──
  _NV_CAP := $(shell nvidia-smi --query-gpu=compute_cap \
                     --format=csv,noheader 2>/dev/null | head -1 | tr -d ' ')
  ifneq ($(_NV_CAP),)
    # "8.6" → "86" → "sm_86" for Clang; GCC targets generic nvptx-none
    _NV_SM := sm_$(subst .,,$(_NV_CAP))
    ifeq ($(_CC_IS_CLANG),0)
      _OFFLOAD_CANDIDATE := -foffload=nvptx-none -foffload-options=-O3
    else
      _OFFLOAD_CANDIDATE := --offload-arch=$(_NV_SM)
    endif
  else
    # ── AMD: rocminfo lists the GFX architecture (e.g. "gfx1030") ──
    _AMD_GFX := $(shell rocminfo 2>/dev/null | grep -o 'gfx[0-9]*' | head -1)
    ifeq ($(_AMD_GFX),)
      # Fallback: some systems only have rocm-smi
      _AMD_GFX := $(shell rocm-smi --showproductname 2>/dev/null \
                           | grep -o 'gfx[0-9]*' | head -1)
    endif
    ifneq ($(_AMD_GFX),)
      _OFFLOAD_CANDIDATE := --offload-arch=$(_AMD_GFX)
    endif
  endif

  # ── Compiler probe ──────────────────────────────────────────────────────────
  # Compile a minimal OpenMP target program with the candidate flags.
  # _Pragma() avoids '#' in the source string (Make treats '#' as a comment).
  ifdef _OFFLOAD_CANDIDATE
    _PROBE_C   := /tmp/_sixsv_omp_probe.c
    _PROBE_BIN := /tmp/_sixsv_omp_probe
    _OFFLOAD_OK := $(shell \
      printf 'int main(void){int n=0;\n_Pragma("omp target map(tofrom:n)")\n{n=1;}return !n;}\n' \
        > $(_PROBE_C) 2>/dev/null && \
      $(CC) -fopenmp $(_OFFLOAD_CANDIDATE) $(_PROBE_C) -o $(_PROBE_BIN) 2>/dev/null \
        && echo ok; \
      rm -f $(_PROBE_C) $(_PROBE_BIN))
    ifeq ($(_OFFLOAD_OK),ok)
      OFFLOAD_FLAGS := $(_OFFLOAD_CANDIDATE)
      $(info lib6sv: GPU offload enabled: $(OFFLOAD_FLAGS))
    else
      OFFLOAD_FLAGS :=
      $(info lib6sv: GPU detected but compiler offload probe failed — CPU OpenMP only)
    endif
  else
    OFFLOAD_FLAGS :=
  endif

endif  # origin OFFLOAD_FLAGS

EXTRA_CFLAGS = -O3 -fopenmp $(OFFLOAD_FLAGS) -std=c11 -fPIC \
               -Wall -Wextra -Wno-unused-parameter

# Runtime dependencies: OpenMP + libm only (no GRASS libraries)
# -lgomp is hardcoded because OPENMP_LIB is empty in GRASS's Platform.make
# (GRASS itself was not configured with --with-openmp on this host).
LIBES = $(OPENMP_LIBPATH) -lgomp $(MATHLIB)

include $(MODULE_TOPDIR)/include/Make/Lib.make

default: lib

# Compile sources from src/ subdirectory
$(OBJDIR)/%.o: src/%.c | $(OBJDIR)
	$(call compiler_c)

# ── Install ────────────────────────────────────────────────────────────────────
# The module-facing public headers are installed to $(INST_DIR)/include/grass/
# so dependent GRASS modules can use the standard -I$(GISBASE)/include path.

GRASS_INC_INST = $(INST_DIR)/include/grass

install: lib
	$(INSTALL) \
	    $(ARCH_LIBDIR)/$(SHLIB_PREFIX)$(LIB_NAME)$(SHLIB_SUFFIX) \
	    $(INST_DIR)/lib/
	$(MKDIR) $(GRASS_INC_INST)
	$(INSTALL_DATA) include/atcorr.h  $(GRASS_INC_INST)/
	$(INSTALL_DATA) include/brdf.h    $(GRASS_INC_INST)/

.PHONY: install

# ── Debian package ─────────────────────────────────────────────────────────────
# Produces libsixsv2_<ver>_<arch>.deb  and  libsixsv-dev_<ver>_<arch>.deb
# in the parent directory (standard dpkg-buildpackage output location).
#
# Usage:
#   make deb                        # unsigned binary-only build (CI / local)
#   make deb DEBBUILD_OPTS="-sa"    # include orig tarball + sign with GPG key
#   make deb-src                    # source-only build  (.dsc + .tar.gz)
#   make deb-clean                  # purge debian/tmp, debian/<pkg>, .deb
#
# GPU offload flags are forwarded so the packaged library matches the host build:
#   make deb OFFLOAD_FLAGS="--offload-arch=sm_86"

DEBBUILD_OPTS ?=

deb:
	dpkg-buildpackage -us -uc -b $(DEBBUILD_OPTS)

deb-src:
	dpkg-buildpackage -us -uc -S $(DEBBUILD_OPTS)

deb-clean:
	dh_clean
	rm -f ../libsixsv*.deb ../libsixsv*.changes ../libsixsv*.buildinfo
	rm -f libsixsv.so libsixsv.so.2 libsixsv.so.2.0.0

.PHONY: deb deb-src deb-clean
