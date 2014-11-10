####################################################################
# lca.py - least common ancestor file
####################################################################

from pyspark import SparkContext

print "\n\n################[BEGINNING SPARK APPLICATION]######################\n\n"

sc = SparkContext("local", "LCA_APPLICATION")

cites_file = "../data/cites.csv"
papers_file = "../data/papers.csv"

cites_data = sc.textFile(cites_file)
papers_data = sc.textFile(papers_file)

#STUB ADD APPLICATION LOGIC HERE


print "\n\n################[TERMINATING SPARK APPLICATION]######################\n\n"









