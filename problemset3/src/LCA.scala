import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf

val citeBucket = "s3n://AKIAI6XU3D7NLMMQ5DMQ:rT3dXyT+2U4MoYRDa1qmCnWQXrmX+czTgZMLxuPw@550.cs.washington.edu/cites.csv"
val paperBucket = "s3n://AKIAI6XU3D7NLMMQ5DMQ:rT3dXyT+2U4MoYRDa1qmCnWQXrmX+czTgZMLxuPw@550.cs.washington.edu/papers.csv"

val cites = sc.textFile(citeBuckets)
println(cites.count()) 