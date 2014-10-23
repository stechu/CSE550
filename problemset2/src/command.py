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

    def __init__(self, command_type, resource_id):
        assert command_type in [
            COMMAND_TYPE.LOCK,
            COMMAND_TYPE.UNLOCK,
            COMMAND_TYPE.NONE]
        assert type(resource_id) == int
        self.command_type = command_type
        self.resource_id = resource_id

    def __eq__(self, other):
        if type(self) == type(other):
            return self.resource_id == other.resource_id \
                and self.command_type == other.command_type
        return False

    def __str__(self):
        ret = ""
        if (self.command_type == COMMAND_TYPE.LOCK):
            ret += "lock "
        elif (self.command_type == COMMAND_TYPE.UNLOCK):
            ret += "unlock "
        else:
            ret += "none "

        ret += str(self.resource_id)

        return ret
