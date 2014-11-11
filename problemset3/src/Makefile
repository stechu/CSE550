#######################################################
# Application Makefile
#######################################################

TEST_SCRIPT=test.py
APP_SCRIPT=lca.py

all: 
	spark-submit --master local[4] lca.py

test:
	spark-submit --master local[4] test.py

clean:
	rm -f *~ \#* *.txt

cleanall: clean
	rm -f ../data/cites.csv ../data/papers.csv