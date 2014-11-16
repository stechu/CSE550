#!/usr/bin/python

#######################################################################################
# machine_events.py
# 
# Parse the machine events file since it's small and easy to do
# Fields:
# 1. timestamp
# 2. machine ID
# 3. event type - 0 = ADD, 1 = REMOVE, 2 = UPDATE
# 4. platform ID
# 5. CPU capacity (relative)
# 6. memory capacity (relative)
#######################################################################################

import os
import sys

MACHINE_EVENTS_FILE="/scratch/vlee2/google-trace/data/machine_events/part-00000-of-00001.csv"
MACHINE_EVENTS_RESULTS="machine_events_results.csv"

# open the target file

data_file = open(MACHINE_EVENTS_FILE, "r+")

# initialize the data structures

# tracks the distribution of machine types for the first appearance of each machine
init_machine_dist = dict()

# keeps track of the actual distribution of each machine type including failures, decommissions, and additions
machine_dist = dict()

# keeps track of machines IDs that are in the working set
seen_machines = []
working_machines = []

# track the relative amount of total CPU core capacity in terms of the largest CPU cores
relative_cpu = 0

# track the relative amount of total memory capacity in terms of the largest memory capacity
relative_memory = 0

warnings = 0
machine_configs = dict()

for line in data_file:
    fields = line.split(",")

    if (fields[0]  is "" or fields[1] is "" or fields[2] is "" or fields[3] is "" or fields[4] is "" or fields[5] is ""):
        warnings += 1
        print "Warning: a field was blank... ignoring this data point: " + line
        continue

    timestamp = int(fields[0].strip(" \n\t"))
    machine_id = int(fields[1].strip(" \n\t"))
    event_type = fields[2].strip(" \n\t")
    platform_id = fields[3].strip(" \n\t")
    cpu_capacity = float(fields[4].strip(" \n\t"))
    memory_capacity = float(fields[5].strip(" \n\t"))


    # process an machine add event
    if int(event_type) == 0:
        # if this is the first time you see the machine log it
        if machine_id not in seen_machines:
            if platform_id not in init_machine_dist:
                init_machine_dist[platform_id] = 1
            else:
                init_machine_dist[platform_id] += 1
            seen_machines.append(machine_id)
        # bookkeep the machine distribution
        if machine_id not in working_machines:
            if platform_id not in machine_dist:
                machine_dist[platform_id] = 1
            else:
                machine_dist[platform_id] += 1
            working_machines.append(machine_id)
        relative_cpu += float(cpu_capacity)
        relative_memory += float(memory_capacity)
        machine_configs[machine_id] = (cpu_capacity, memory_capacity)

    # process a removed machine
    elif int(event_type) == 1:
        if machine_id not in machine_dist:
            print "Warning: machine was removed before being added..."
            warnings += 1
        elif machine_dist[machine_id] <= 0:
            print "Warning: machine was already removed from distribution..."
            warnings += 1
        else:
            machine_dist[machine_id] -= 1
        machine_configs[machine_id] = (0, 0)

    # process an update
    else:
        if machine_id in machine_configs:
            prior_config = machine_configs[machine_id]
            prior_cpu = prior_config[0]
            prior_memory = prior_config[1]
            
            # don't have to tweek the platform distribution since hardware isn't changed, just the resource availability
            relative_cpu = relative_cpu - prior_cpu + cpu_capacity
            relative_memory = relative_memory - prior_memory + memory_capacity
        else:
            # if this is the first time you see the machine log it
            if machine_id not in seen_machines:
                if platform_id not in init_machine_dist:
                    init_machine_dist[platform_id] = 1
                else:
                    init_machine_dist[platform_id] += 1
                    seen_machines.append(machine_id)
                # bookkeep the machine distribution
            if machine_id not in working_machines:
                if platform_id not in machine_dist:
                    machine_dist[platform_id] = 1
                else:
                    machine_dist[platform_id] += 1
                working_machines.append(machine_id)
            relative_cpu += float(cpu_capacity)
            relative_memory += float(memory_capacity)
    
        machine_configs[machine_id] = (cpu_capacity, memory_capacity)

print "[Info] TOTAL WARNINGS: " + str(warnings) + "\n"

data_file.close()

# log the information to outputs file
result_file = open(MACHINE_EVENTS_RESULTS, "w+")

# dump the relative cpu and memory
result_file.write("RELATIVE CPU, " + str(relative_cpu) + "\n")
result_file.write("RELATIVE MEMORY, " + str(relative_memory) + "\n")

# write the origin distribution
result_file.write("\nINITIAL MACHINE DISTRIBUTION\n")

for key in init_machine_dist.keys():
    result_file.write(str(key) + "," + str(init_machine_dist[key]) + "\n")

# write the final distribution
result_file.write("\nFINAL MACHINE DISTRIBUTION\n")

for key in machine_dist.keys():
    result_file.write(str(key) + "," + str(init_machine_dist[key]) + "\n")

result_file.close()
