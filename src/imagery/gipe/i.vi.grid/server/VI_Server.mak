# This file 'VI_Server.mak' was created by ng_gen. Don't edit

CC = cc
include $(NG_DIR)/lib/template.mk

# CompileOptions:
NG_USER_CFLAGS = 

#  Define NG_COMPILER & NG_LINKER as $(CC) if it is not defined.

NG_COMPILER = $(CC)
NG_LINKER = $(CC)

# stub sources

NG_STUB_SRC = _stub_VI_CALC.c 

# stub programs

NG_STUB_PROGRAM = _stub_VI_CALC

# stub inf files
NG_INF_FILES = _stub_VI_CALC.inf

# LDAP dif file
LDAP_DIF = root.ldif

all: $(NG_STUB_PROGRAM) $(NG_INF_FILES) $(LDAP_DIF)

_stub_VI_CALC.o: _stub_VI_CALC.c
	$(NG_COMPILER) $(NG_CPPFLAGS) $(CFLAGS) $(NG_CFLAGS) $(NG_USER_CFLAGS) -c _stub_VI_CALC.c
_stub_VI_CALC: _stub_VI_CALC.o VI_ServerC.o
	$(NG_LINKER) $(NG_CFLAGS) $(CFLAGS) -o _stub_VI_CALC _stub_VI_CALC.o $(LDFLAGS) $(NG_STUB_LDFLAGS) VI_ServerC.o $(LIBS)
_stub_VI_CALC.inf: _stub_VI_CALC
	 ./_stub_VI_CALC -i _stub_VI_CALC.inf



$(LDAP_DIF): $(NG_INF_FILES)
	$(NG_DIR)/bin/ng_gen_dif $(NG_STUB_PROGRAM)

install: $(LDAP_DIF)
	$(INSTALL) *.ldif $(LDIF_INSTALL_DIR)

clean:
	rm -f _stub_VI_CALC.o _stub_VI_CALC.c

veryclean: clean
	rm -f $(NG_STUB_PROGRAM) $(NG_INF_FILES) $(LDAP_DIF) *.ngdef
	rm -f VI_ServerC.o


# END OF Makefile
