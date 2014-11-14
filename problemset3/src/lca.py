####################################################################
# lca.py - least common ancestor file
####################################################################

from pyspark import SparkContext

cites_bucket = """s3n://AKIAI6XU3D7NLMMQ5DMQ:\
rT3dXyT+2U4MoYRDa1qmCnWQXrmX+czTgZMLxuPw@550.cs.washington.edu/cites.csv"""
papers_bucket = """s3n://AKIAI6XU3D7NLMMQ5DMQ:\
rT3dXyT+2U4MoYRDa1qmCnWQXrmX+czTgZMLxuPw@550.cs.washington.edu/papers.csv"""


if __name__ == "__main__":
    def filter_header(s):
        """
            filter non-digit items
        """
        return s[0].isdigit() and s[1].isdigit()

    print "\n---------------[BEGINNING SPARK APPLICATION]-----------------\n"

    sc = SparkContext("local", "LCA_APPLICATION")
    parallism = 4

    # read data from s3
    cites = sc.textFile(cites_bucket)
    papers = sc.textFile(papers_bucket)

    # filter the annoying header
    papers = papers.map(lambda x: x.split(",")).filter(filter_header)
    # convert type
    papers = papers.map(lambda x: (int(x[0]), int(x[1])))
    # filter cites
    cites = cites.map(
        lambda x: x.split(",")).filter(filter_header)
    cites = cites.map(lambda x: (int(x[0]), int(x[1])))
    edges = cites.cache()

    # compute reversed shortest path
    N = 10
    vertices = edges.map(
        lambda (x, y): x).distinct().filter(lambda x: x < N)

    print "\n --------- {} valid seeds ----------\n".format(vertices.count())

    # distances: (vertex, seed, distance)
    distances = vertices.map(lambda x: (x, (x, 0))).cache()
    old_count = 0L
    new_count = distances.count()
    while old_count != new_count:
        next_step = distances.join(cites).map(
            lambda (v1, ((s, d), v2)): ((v2, s), d+1))
        dist_seed_pairs = distances.map(lambda (v, (s, d)): ((v, s), d))
        distances = next_step.union(dist_seed_pairs).reduceByKey(
            lambda a, b: a if a < b else b).map(
            lambda ((v, s), d): (v, (s, d)))
        old_count = new_count
        new_count = distances.count()

    print "\n--------------------get all the distances ---------------------\n"

    for e in distances.take(10):
        print e

    print "\n---------------[TERMINATING SPARK APPLICATION]-----------------\n"
