#########################################################################
# command.py
#
# Python module for command object definition
#########################################################################

from constants import *

# A makeshift enum
class COMMAND_TYPE():
    LOCK = 0
    UNLOCK = 1
    NONE = 2

class command():
    my_command = COMMAND_TYPE.NONE
    my_lock_num = -1

    def __init__(self, cmd_str):
        assert(type(cmd_str) == str)
        
        cmd = cmd_str.strip(" \t\n")
        cmd_fields = cmd.split(" ")

        assert(len(cmd_fields) == 2)

        command = cmd_fields[0]
        lock_num = int(cmd_fields[1])

        if (command.lower() == LOCK_COMMAND):
            my_command = COMMAND_TYPE.LOCK
        elif (command.lower() == UNLOCK_COMMAND):
            my_command = COMMAND_TYPE.UNLOCK
        else:
            assert(false)

    def command(self):
        return my_command

    def lock_num(self):
        return my_lock_num
