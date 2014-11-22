#!/usr/bin/python

#######################################################################
# Reduce the usage statistics
# - hack up a script to do this since fuck EC2
# - shit is hardcoded, do not recommend anyone trying to edit this
#######################################################################

RESULTS_DIR = "../results"
FILE_PREFIX = "task_usage.csv-part-"
FILE_SUFFIX = ".csv"

NUM_FILES=500

task_files = []

RESULT_FILE = "../results/task_usage_totals.csv"

# dict() of dict() - holds the running total of statistics across the files
STATISTICS = dict() 

TASK_PROCESSED_KEY = "TOTAL TASKS PROCESSED"

for i in range(0, 500):

    # open the file
    r_file = open(RESULTS_DIR + "/" + FILE_PREFIX + str(i) + FILE_SUFFIX, "r+")

    # scan the file and build a fields dictionary
    new_stats = dict()
    field_key = ""

    stat_field = ""

    for raw_line in r_file:
        
        line = raw_line.strip("\n\t ")
        fields = line.split(",")

        # is a blank new line
        if (len(fields) == 1 and fields[0].strip(" \n\t") is ""):
            stat_field = ""
            pass
        # is just a single key value
        elif (len(fields) == 2 and fields[1].strip("\n\t ") is not "" and stat_field is ""):
            field_key = fields[0]
            field_value = float(fields[1])
            
            new_stats[field_key] = field_value
            stat_field = ""

        # if not a single key field create a dictionary
        elif (len(fields) == 2 and fields[1].strip("\n\t ") is ""):
            stat_field = fields[0]
            new_stats[stat_field] = dict()

        # hack up a work around for disk i/o distribution
        elif (len(fields) == 1 and "DISK I/O DISTRIBUTION" in fields[0]):
            stat_field = fields[0]
            new_stats[stat_field] = dict()

        # if is part of a dictionary add to dict
        elif (len(fields) == 2 and stat_field.strip("\n\t ") is not ""):
            field_key = fields[0]
            field_value = fields[1]
            assert(stat_field is not "")
            d = new_stats[stat_field]
            d[field_key] = float(field_value)

        else:
            stat_field = ""
            pass # ignore the whitespace line

    # log the previous total number of tasks
    if TASK_PROCESSED_KEY not in STATISTICS:
        STATISTICS[TASK_PROCESSED_KEY] = 0
    old_num_tasks = STATISTICS[TASK_PROCESSED_KEY]
    assert(old_num_tasks is not None)
            
    # collect all the stats into a dictionary
    for key in new_stats:

        # if is a dictionary combine the dictionaries
        if (type(new_stats[key]) is dict):

            # generate a new dict if is the first time
            if not key in STATISTICS:
                STATISTICS[key] = dict()

            d = new_stats[key]

            for item in d:
                if item not in STATISTICS[key]:
                    STATISTICS[key][item] = d[item]
                else:
                    STATISTICS[key][item] += d[item]

        # otherwise it's a value
        else:
            if key not in STATISTICS:
                STATISTICS[key] = 0

            # check if the sting average appears in the field
            if "AVERAGE" in key:
                
                old_average = STATISTICS[key]
                old_weight = old_average * old_num_tasks

                new_weight = old_weight + new_stats[TASK_PROCESSED_KEY] * new_stats[key]
                STATISTICS[key] = new_weight / (old_num_tasks + new_stats[TASK_PROCESSED_KEY])
                
            else:
                STATISTICS[key] += new_stats[key]

    r_file.close()

# log the final file

result_file = open(RESULT_FILE, "w+")

for key in STATISTICS:

    if (type(STATISTICS[key]) is dict):
        result_file.write("\n" + str(key) + ",\n")

        for k in sorted(STATISTICS[key]):
            result_file.write(str(k) + "," + str(STATISTICS[key][k]) + "\n")

        result_file.write("\n")

    else:
        result_file.write("\n" + str(key) + "," + str(STATISTICS[key]) + "\n")

result_file.close()
