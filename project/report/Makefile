###############################################
# Documentation Makefile
###############################################

DOCUMENT_FILE=report

all:
	pdflatex $(DOCUMENT_FILE)
	bibtex $(DOCUMENT_FILE)
	pdflatex $(DOCUMENT_FILE)
	pdflatex $(DOCUMENT_FILE)
	rm -f *.out *.aux *.toc *.log *~ \#* *.bbl *.blg
clean:
	rm -f *.out *.aux *.toc *.pdf *.log *~ \#* *.bbl *.blg