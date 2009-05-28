# These belong maybe in Grass.make?
NETA_LIBNAME = grass_neta
NETALIB      = -l$(NETA_LIBNAME) 
NETADEP      = $(ARCH_LIBDIR)/$(LIB_PREFIX)$(NETA_LIBNAME)$(LIB_SUFFIX)
