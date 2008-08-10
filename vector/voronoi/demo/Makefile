CC	= gcc 
CFLAGS	= -O0 -g3 $$(pkg-config --cflags --libs cairo)
LDFLAGS	= -lm
INCS 	=\
	data_types.h\
	edge.h\
	error.h\
	geometry.h\
	geom_primitives.h\
	in_out.h\
	memory.h\

SRC 	=\
	edge.c\
	error.c\
	in_out.c\
	main.c\
	memory.c\
	geometry.c


OBJS 	=\
	edge.o\
	error.o\
	in_out.o\
	main.o\
	memory.o\
	geometry.o

TEXT	= Makefile README $(INCS) $(SRC) 

guibas-stolfi	: $(OBJS)
	$(CC) -o $@ $(CFLAGS) $(OBJS) $(LDFLAGS)
	
clean:
	rm -f guibas-stolfi $(OBJS)

