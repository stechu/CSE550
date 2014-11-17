#!/usr/bin/python

#################################################################
# attribute_forensics.py
#
# Forensics scripts to attempt to figure out obfuscated data
#################################################################

import os
import sys

MACHINE_ATTRIBUTES_FILE="/scratch/vlee2/google-trace/data/machine_attributes/part-00000-of-00001.csv"
MACHINE_ATTRIBUTES_FORENSICS="../results/attribute_forensics.txt"

# declare attributes map
attribute_map = dict()

# holds a dict of all the attributes seen so far

data_file = open(MACHINE_ATTRIBUTES_FILE, "r+")

attributes_added = 0
attributes_deleted = 0

processed = 0

# parse the data file to scan for range of attributes
for line in data_file:
    
    fields = line.split(",")
    
    # validate that fields are not empty
    if (fields[0] is "" or fields[1] is "" or fields[2] is "" or fields[3] is "" or fields[4] is ""):
        if fields[4] is not "":
            pass
        else:
            print "Warning: a field is blank, discarding: " + line + "\n"
            continue

    timestamp = long(fields[0])
    machine_id = fields[1]
    attribute_name = fields[2]
    attribute_value = fields[3]
    attribute_deleted = int(fields[4])

    # update the attribute add/del count
    if (attribute_deleted == 1):
        attributes_deleted += 1
    else:
        attributes_added += 1

    # log the attribute and it's range of values
    if attribute_deleted == 0:
        if attribute_name not in attribute_map:
            attribute_map[attribute_name] = []
            dist = attribute_map[attribute_name].append(attribute_value)
        else:
            dist = attribute_map[attribute_name]
            if attribute_value not in dist:
                attribute_map[attribute_name].append(attribute_value)
            else:
                # ignore duplicate already seen
                pass

    processed += 1
    if ((processed % 1000000) == 0):
        print "Progress: " + str(processed) + "\r"

data_file.close()

forensics_file = open(MACHINE_ATTRIBUTES_FORENSICS, "w+")

# dump the distribution keys
for key in attribute_map:
    dist = attribute_map[key]
    forensics_file.write("\n" + key + "," + str(len(dist)) + "\n")
    for x in dist:
        forensics_file.write(x + "\n")

forensics_file.close()
