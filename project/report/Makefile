###############################################
# Documentation Makefile
###############################################

DOCUMENT_FILE=report

all:
	pdflatex $(DOCUMENT_FILE)
	bibtex $(DOCUMENT_FILE)
	pdflatex $(DOCUMENT_FILE)
	pdflatex $(DOCUMENT_FILE)

clean:
	rm -f *.out *.aux *.toc *.pdf *.log *~ \#*