#######################################################
# Application Makefile
#######################################################

TEST_SCRIPT=test.py
APP_SCRIPT=lca.py

all: ../data/cites.csv ../data/papers.csv
	spark-submit --master local[4] lca.py

test:
	spark-submit --master local[4] test.py

../data/cites.csv:
	cd ../data && wget https://s3-us-west-2.amazonaws.com/550.cs.washington.edu/cites.csv

../data/papers.csv:
	cd ../data && wget https://s3-us-west-2.amazonaws.com/550.cs.washington.edu/papers.csv

clean:
	rm -f *~ \#* *.txt

cleanall: clean
	rm -f ../data/cites.csv ../data/papers.csv