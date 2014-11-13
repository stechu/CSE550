####################################################################
# lca.py - least common ancestor file
####################################################################

from pyspark import SparkContext

print "\n\n################[BEGINNING SPARK APPLICATION]######################\n\n"

sc = SparkContext("local", "LCA_APPLICATION")

cites_bucket="s3n://AKIAI6XU3D7NLMMQ5DMQ:rT3dXyT+2U4MoYRDa1qmCnWQXrmX+czTgZMLxuPw@550.cs.washington.edu/cites.csv"
cites_bucket="s3n://AKIAI6XU3D7NLMMQ5DMQ:rT3dXyT+2U4MoYRDa1qmCnWQXrmX+czTgZMLxuPw@550.cs.washington.edu/papers.csv"

cites_data = sc.textFile(cites_bucket)
papers_data = sc.textFile(papers_bucket)
print "cite count :{}".format(cites_data.count())
print "paper count ：{}".format(papers_data.count())

#STUB ADD APPLICATION LOGIC HERE


print "\n\n################[TERMINATING SPARK APPLICATION]######################\n\n"

