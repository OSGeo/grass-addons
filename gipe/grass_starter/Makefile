#convenient Makefile (I think) -MN

#targets:
#  make           - builds the text
#  make refcheck  - check \label{} and \ref{} and friends for consistency
#                   Result is in "latex_refs.log"
#  make clean     - removed Latex' auxiliary files
#  make ps        - create PS file
#  make pdf       - create PDF file
#  make html      - create HTML files (into GRASSnews_volX/ subdirectory)
#  make ascii     - extracts ASCII from original ${LATEX} files (into ascii/ subdirectory)
#  make changelog - creates ChangeLog

FILE=main_document
LATEX=pdflatex

all:
	${LATEX} $(FILE)
	#bibtex $(FILE)
	#now loop over ${LATEX} files, until stable:
	echo Rerun > $(FILE).log
	while grep Rerun $(FILE).log >/dev/null 2>&1 ; do ${LATEX} $(FILE).tex ; done

#check references:
refcheck: all
	${LATEX} $(FILE) | grep "undefined" > latex_refs.log
	#@echo "Bibtex errors:" >> latex_refs.log
	#bibtex $(FILE) | grep 'find a database' >> latex_refs.log
	@echo "Check is stored in: latex_refs.log"
	@cat latex_refs.log

#make PostScript:
ps: all
	dvips -o $(FILE).ps $(FILE).dvi

#make PDF:
pdf: all
	@#the new converter script has a different name:
	@(type -p dvipdfpress > /dev/null ; if [ $$? -eq 0 ] ; then dvipdfpress $(FILE).dvi $(FILE).pdf ; else dvipdf $(FILE).dvi $(FILE).pdf ; fi )
	@echo "Generated: $(FILE).pdf"

html:
	$(MAKE) all
	latex2html -init_file l2h.conf  -split=+2 -address "(C) 2005, <a href=http://grass.itc.it/newsletter/>GRASS Newsletter editorial board</a><br>Last modified: `/bin/date +%d-%m-%Y`" $(FILE)
	@echo "HTML Newsletter generated in ./$(FILE)"

# set to your preferred software such as detex, untex, ...
DETEX=detex
ascii:
	@test -d ascii || mkdir ascii ; true
	@(for i in *.tex ; do n=`basename $$i .tex` ; ${DETEX} $$i > ascii/$$n.txt ; done)
	@echo "ASCII newsletter extracted to ./ascii/"

clean:
	rm -f *.log $(FILE).aux $(FILE).dvi $(FILE).bbl $(FILE).blg $(FILE).out $(FILE).cb $(FILE).toc

veryclean: clean
	rm -f *~ latex_refs.log *.ps *.pdf

# cvs2cl.pl creates a GNU style ChangeLog file:
# http://www.red-bean.com/~kfogel/cvs2cl.shtml
changelog:
	cvs2cl.pl
	@echo "Written ChangeLog"
