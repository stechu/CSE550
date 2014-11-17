#!/usr/bin/python

#################################################################
# attribute_forensics.py
#
# Go through each of the task usage files to collect statistics
# on the task usage
#################################################################

import os
import sys
from math import *

BASE_DIRECTORY="/scratch/vlee2/google-trace/data/task_usage/"
BASE_FILE_PREFIX="part-"
BASE_FILE_SUFFIX="-of-00500.csv"
RESULTS_FILE="../results/task_usage.csv"
FILE_PARTS=1 # 500
LOG_BASE=10

# track how many tasks we ignore due to too many empty data fields
discarded_tasks = 0

# track the number of logged tasks
tasks_processed = 0

######################################################
# initialize statistics data structures
# - track the totals to find the average at the end
######################################################

# task duration distribution - histogram buckets rounded to nearest .1 of log_10(task_length)
task_duration_distribution = dict()
total_task_durations = 0

# cpu core-seconds used per second - buckets are in .1 increments
cpu_rate_distribution = dict()
total_cpu_rate = 0

# TODO: analyze the memory usage statistics and figure out what they are doing

# percentage disk I/O time (disk_IO - seconds / task_duration) - buckets in log_10 increments
disk_io_distribution = dict()
total_disk_io = 0

# local disk space usage
disk_space_usage_distribution = dict()
total_disk_space_usage = 0

# inst-seconds per cycle
ispc_distribution = dict()
total_ispc = 0

# memory accesses per instruction
mai_distribution = dict()
total_mai = 0

# track the number of reports that are aggregated
aggregation_tasks = 0

# track the total number of entries
tasks_processed = 0

# iterate over the number of files
for i in range(0, FILE_PARTS):

    # construct the file name
    target_file = BASE_FILE_PREFIX + ("%0.5d" % i) + BASE_FILE_SUFFIX

    # open the file
    data_file = open(BASE_DIRECTORY + target_file, "r+")

    # iterate over the file
    for line in data_file:
        
        fields = line.split(",")
        
        # discard the task if one or more fields are empty
        if (fields.count("") > 0):
            discarded_tasks += 1
            continue

        # parse the task statistics
        start_time = int(fields[0])
        end_time = int(fields[1])
        job_id = int(fields[2])
        task_index = int(fields[3])
        machine_id = int(fields[4])
        cpu_usage = float(fields[5])
        canonical_memory_usage = float(fields[6])
        assigned_memory_usage = float(fields[7])
        unmapped_page_cache = float(fields[8])
        total_page_cache = float(fields[9])
        maximum_memory_usage = float(fields[10])
        disk_io_time = float(fields[11])
        local_disk_space_usage = float(fields[12])
        maximum_cpu_rate = float(fields[13])
        maximum_disk_IO_time = float(fields[14])
        cycles_per_instruction = float(fields[15])
        memory_accesses_per_instruction = float(fields[16])
        sample_portion = float(fields[17])
        aggregation_type = fields[18]

        tasks_processed += 1

        # process the task durations
        duration = end_time - start_time
        assert(duration >= 0)
        log_duration = floor(log(duration)/log(LOG_BASE))
        if log_duration not in task_duration_distribution:
            task_duration_distribution[log_duration] = 1
        else:
            task_duration_distribution[log_duration] += 1
        total_task_durations += duration

        # process the cpu rates - in 10ths of a percent
        rate = floor(cpu_usage * 1000) / 1000
        if rate not in cpu_rate_distribution:
            cpu_rate_distribution[rate] = 1
        else:
            cpu_rate_distribution[rate] += 1
        total_cpu_rate += cpu_usage

        # process the disk-time seconds per second / task duration
        disk_percent = float(disk_io_time) / float(duration)
        if (disk_percent != 0):
            fdisk_percent = floor(log(disk_percent)/log(LOG_BASE))
        else:
            fdisk_percent = float('Inf')
        if fdisk_percent not in disk_io_distribution:
            disk_io_distribution[fdisk_percent] = 1
        else:
            disk_io_distribution[fdisk_percent] += 1
        total_disk_io += disk_io_time

        # process the local disk space usage
        if (local_disk_space_usage != 0):
            disk_usage = floor(log(local_disk_space_usage)/log(LOG_BASE))
        else:
            disk_usage = float('Inf')
        if disk_usage not in disk_space_usage_distribution:
            disk_space_usage_distribution[disk_usage] = 1
        else:
            disk_space_usage_distribution[disk_usage] += 1
        total_disk_space_usage += 1

        # process the cpi and get ispc - instruction-seconds per cycle
        ispc = duration / cycles_per_instruction
        if (ispc != 0):
            fispc = floor(log(ispc)/log(LOG_BASE))
        else:
            fispc = float('Inf')
        if fispc not in ispc_distribution:
            ispc_distribution[fispc] = 1
        else:
            ispc_distribution[fispc] += 1
        total_ispc += ispc

        # process the memory accesses per instruction
        if (memory_accesses_per_instruction != 0):
            fmai = floor(log(memory_accesses_per_instruction)/log(LOG_BASE))
        else:
            fmai = float('Inf')
        if fmai not in mai_distribution:
            mai_distribution[fmai] = 1
        else:
            mai_distribution[fmai] += 1
        total_mai += memory_accesses_per_instruction

        aggregation_tasks += int(aggregation_type)

    data_file.close()
    print "[Info] Done processing file: " + target_file

print "[Info] Done processing data files..."

############################################################################
# build the report file
############################################################################

report=open(RESULTS_FILE, "w+")

report.write("TOTAL TASKS PROCESSED, " + str(tasks_processed) + "\n")
report.write("AGGREGATION TASKS, " + str(aggregation_tasks) + "\n")
report.write("TASKS IGNORED, " + str(discarded_tasks) + "\n")

# dump the task duration distribution
text = "\nTASK RECORD DURATION AVERAGE, " + str(total_task_durations / tasks_processed) + "\n"
report.write(text)

text = "\nTASK DURATION DISTRIBUTION (log_" + str(LOG_BASE) + "),\n"
for key in sorted(task_duration_distribution.keys()):
    text += str(key) + "," + str(task_duration_distribution[key]) + "\n"
report.write(text)

# dump the cpu core-seconds per second
text = "\nAVERAGE CPU RATE (core-seconds), " + str(total_cpu_rate / tasks_processed) + "\n"
report.write(text)

text = "\nCPU RATE DISTRIBUTION (core-seconds),\n"
for key in sorted(cpu_rate_distribution.keys()):
    text += str(key) + "," + str(cpu_rate_distribution[key]) + "\n"
report.write(text)

# dump the disk I/O time
text = "\nAVERAGE DISK I/O PERCENTAGE (percent), " + str(total_disk_io / tasks_processed) + "\n"
report.write(text)

text = "\nDISK I/O DISTRIBUTION (disk I/O-seconds)\n"
for key in sorted(disk_io_distribution.keys()):
    text += str(key) + "," + str(disk_io_distribution[key]) + "\n"
report.write(text)

# dump the disk space usage
text = "\nAVERAGE DISK SPACE USAGE, " + str(total_disk_space_usage / tasks_processed) + "\n"
report.write(text)

text = "\nDISK SPACE USAGE,\n"
for key in sorted(disk_space_usage_distribution.keys()):
    text += str(key) + "," + str(disk_space_usage_distribution[key]) + "\n"
report.write(text)

# dump the instruction-cycles per second
text = "\nAVERAGE INSTRUCTION-CYCLES PER SECOND, " + str(total_ispc / tasks_processed) + "\n"
report.write(text)

text = "\nINSTRUCTION-SECONDS PER CYCLE,\n"
for key in sorted(ispc_distribution.keys()):
    text += str(key) + "," + str(ispc_distribution[key]) + "\n"
report.write(text)

# dump the memory accesses per instruction
text = "\nAVERAGE MEMORY ACCESSES PER INSTRUCTION, " + str(total_mai / tasks_processed) + "\n"
report.write(text)

text = "\nMEMORY ACCESSES PER INSTRUCTION, \n"
for key in sorted(mai_distribution.keys()):
    text += str(key) + "," + str(mai_distribution[key]) + "\n"
report.write(text)

report.close()

print "[Info] Done generating report..."
