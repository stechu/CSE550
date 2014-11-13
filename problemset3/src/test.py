from pyspark import SparkContext
sc = SparkContext("local", "ExampleSpark")

cites_bucket="s3n://AKIAI6XU3D7NLMMQ5DMQ:rT3dXyT+2U4MoYRDa1qmCnWQXrmX+czTgZMLxuPw@550.cs.washington.edu/cites.csv"

citeData = sc.textFile(cites_bucket)

numWords = citeData.filter(lambda s: '12' in s).count()
print "Lines with '12': %i" % (numWords)
