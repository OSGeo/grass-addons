vectoreps := $(wildcard *.eps)
vectorfinal := $(patsubst %.eps,%.pdf,$(vectoreps))

default: grassflyer.pdf

$(vectorfinal): $(vectoreps)
	eps2eps -sOutputFile=- $< | epstopdf -f 

%.pdf: %.tex
	pdflatex $<
	pdflatex $<

clean:
	rm -f *.aux *.log *.out 

distclean: clean
	rm -f *.pdf

.PHONY: clean distclean default
