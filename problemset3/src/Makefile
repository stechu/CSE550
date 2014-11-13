#######################################################
# Application Makefile
#######################################################

TEST_SCRIPT=test.py
APP_SCRIPT=lca.py
INET_ADDRESS=172.31.21.210 #TODO hardcoded

all: 
	spark-submit --master spark://0.0.0.0:7077 lca.py

test:
	spark-submit --master spark://0.0.0.0:7077 test.py

clean:
	rm -f *~ \#* *.txt

cleanall: clean
	rm -f ../data/cites.csv ../data/papers.csv