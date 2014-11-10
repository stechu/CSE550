from pyspark import SparkContext
sc = SparkContext("local", "ExampleSpark")

citesFile = "s3-us-west-2.amazonaws.com/550.cs.washington.edu/cites.csv"
citesFile = "cites.csv"
citeData = sc.textFile(citesFile)

numWords = citeData.filter(lambda s: '12' in s).count()
print "Lines with '12': %i" % (numWords)
