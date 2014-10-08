# Builds the submission tar file

UWNETID=1323346
TAR_FILE=problemset1_submission_$(UWNETID).tar.gz

all: $(TAR_FILE)

$(TAR_FILE): 
	cd problemset1/parta && $(MAKE) clean 
	cd problemset1/partb && $(MAKE) clean
	tar -cvzf $(TAR_FILE) problemset1

clean:
	rm -f $(TAR_FILE)
