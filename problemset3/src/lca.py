####################################################################
# lca.py - least common ancestor file
####################################################################

from pyspark import SparkContext

print "\n\n################[BEGINNING SPARK APPLICATION]######################\n\n"

sc = SparkContext("local", "LCA_APPLICATION")

cites_bucket="s3://s3-us-west-2.amazonaws.com/550.cs.washington.edu/cites.csv"
papers_bucket="s3://s3-us-west-2.amazonaws.com/550.cs.washington.edu/papers.csv"

cites_data = sc.textFile(cites_bucket)
papers_data = sc.textFile(papers_bucket)

#STUB ADD APPLICATION LOGIC HERE


print "\n\n################[TERMINATING SPARK APPLICATION]######################\n\n"









