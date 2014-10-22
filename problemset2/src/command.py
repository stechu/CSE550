#########################################################################
# command.py
#
# Python module for command object definition
#########################################################################

from constants import *


# A makeshift enum
class COMMAND_TYPE(object):
    LOCK = 0
    UNLOCK = 1
    NONE = 2


class command(object):

    def __init__(self, cmd_str):
        assert(type(cmd_str) == str)

        cmd_s = cmd_str.strip(" \t\n")
        cmd_fields = cmd_s.split(" ")

        assert(len(cmd_fields) == 2)

        cmd = cmd_fields[0]
        self.my_lock_num = int(cmd_fields[1])

        # determine if the command valid
        if (cmd.lower() == LOCK_COMMAND.lower()):
            self.my_command = COMMAND_TYPE.LOCK
        elif (cmd.lower() == UNLOCK_COMMAND.lower()):
            self.my_command = COMMAND_TYPE.UNLOCK
        else:
            assert(false)

