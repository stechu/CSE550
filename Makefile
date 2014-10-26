# Builds the submission tar file

UWNETID=1323363
TAR_FILE_1=problemset1_submission_$(UWNETID).tar.gz
TAR_FILE_2=problemset2_submission_$(UWNETID).tar.gz

all: $(TAR_FILE_1) $(TAR_FILE_2)

$(TAR_FILE_1): 
	cd problemset1/parta && $(MAKE) clean 
	cd problemset1/partb && $(MAKE) clean
	tar -cvzf $(TAR_FILE_1) problemset1

$(TAR_FILE_2): 
	tar -cvzf $(TAR_FILE_2) problemset2

clean:
	rm -f $(TAR_FILE_1) $(TAR_FILE_2)
