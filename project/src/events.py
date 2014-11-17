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
MACHINE_EVENTS_RESULTS="../results/machine_events_results.csv"
WARNING_FILE="machine_events_warnings.txt"

# open the target file

data_file = open(MACHINE_EVENTS_FILE, "r+")
warning_file = open(WARNING_FILE, "w+")

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
machines_added = 0
machines_removed = 0
machines_updated = 0

for line in data_file:
    fields = line.split(",")

    if (fields[0]  is "" or fields[1] is "" or fields[2] is "" or fields[3] is "" or fields[4] is "" or fields[5] is ""):
        warnings += 1
        warning_file.write("Warning: a field was blank... ignoring this data point: " + line + "\n")
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
            # add to the platform count
            if platform_id not in machine_dist:
                machine_dist[platform_id] = 1
            else:
                machine_dist[platform_id] += 1

            working_machines.append(machine_id)
        machine_configs[machine_id] = (cpu_capacity, memory_capacity)
        machines_added += 1

    # process a removed machine from the machine distribution
    elif int(event_type) == 1:
        if platform_id not in machine_dist:
            warning_file.write("Warning: machine was removed before being added: " + str(machine_id) + "\n")
            warnings += 1
        elif machine_dist[platform_id] <= 0:
            warning_file.write("Warning: machine was already removed from distribution: " + str(machine_id) + "\n")
            warnings += 1
        else:
            machine_dist[platform_id] -= 1
        
        if machine_id in working_machines:
            working_machines.remove(machine_id)

        machine_configs.pop(machine_id, None)
        machines_removed += 1

    # process an update
    else:
        if machine_id in machine_configs:
            prior_config = machine_configs[machine_id]
            prior_cpu = prior_config[0]
            prior_memory = prior_config[1]
            
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
    
        machine_configs[machine_id] = (cpu_capacity, memory_capacity)
        machines_updated += 1

# compute a machine cpu capacity histogram, memory capacity histogram, and relative cpu to memory histogram

cpu_hist = dict()
memory_hist = dict()
ratio_hist = dict()
for key in machine_configs:
    (c, m) = machine_configs[key]
    
    if c in cpu_hist.keys():
        cpu_hist[c] += 1
    else:
        cpu_hist[c] = 1

    if m in memory_hist.keys():
        memory_hist[m] += 1
    else:
        memory_hist[m] = 1

    # deal with divide by zero issues
    ratio = 0
    if (m == 0):
        ratio = 0
    else:
        ratio = c/m

    if ratio in ratio_hist.keys():
        ratio_hist[ratio] += 1
    else:
        ratio_hist[ratio] = 1

# compute a capacity to ratio histogram

print "[Info] TOTAL WARNINGS: " + str(warnings) + "\n"

data_file.close()

# compute the total relative CPU and memory from machine_configs
v_cpu = 0
v_memory = 0
for key in machine_configs:
    (c, m) = machine_configs[key]
    relative_cpu += c
    relative_memory += m

# log the information to outputs file
result_file = open(MACHINE_EVENTS_RESULTS, "w+")

# dump the relative cpu and memory
result_file.write("RELATIVE CPU, " + str(relative_cpu) + "\n")
result_file.write("RELATIVE MEMORY, " + str(relative_memory) + "\n")
result_file.write("TOTAL MACHINES SEEN, " + str(len(machine_configs.keys())) + "\n")
result_file.write("MACHINES ADDED, " + str(machines_added) + "\n")
result_file.write("MACHINES REMOVED, " + str(machines_removed) + "\n")
result_file.write("MACHINES_UUPDATED, " + str(machines_updated) + "\n")

# write the origin distribution
result_file.write("\nINITIAL MACHINE DISTRIBUTION\n")

for key in init_machine_dist.keys():
    result_file.write(str(key) + "," + str(init_machine_dist[key]) + "\n")

# write the final distribution
result_file.write("\nFINAL MACHINE DISTRIBUTION\n")

for key in machine_dist.keys():
    result_file.write(str(key) + "," + str(init_machine_dist[key]) + "\n")

# write the cpu histogram
result_file.write("\nRELATIVE CPU HISTOGRAM\n")

for key in cpu_hist:
    result_file.write(str(key) + "," + str(cpu_hist[key]) + "\n")

# write the memory histogram
result_file.write("\nMEMORY HISTOGRAM\n")

for key in memory_hist:
    result_file.write(str(key) + "," + str(memory_hist[key]) + "\n")

# write the relative ratio histogram
result_file.write("\nRELATIVE RATIO HISTOGRAM\n")

for key in ratio_hist:
    result_file.write(str(key) + "," + str(ratio_hist[key]) + "\n")

result_file.close()
warning_file.close()
