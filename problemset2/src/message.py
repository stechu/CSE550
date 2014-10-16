######################################################################
# message.py
#
# - message class for Paxos communication
######################################################################

import os
import sys
import command

class MESSAGE_TYPE:
    PREPARE = 0
    PREPARE_ACK = 1
    ACCEPT = 2
    ACCEPT_ACK = 3
    CLIENT = 4
    CLIENT_ACK = 5

########################################################################################
# PREPARE - proposal mesasge; requires propoal, instance, and type
# PREPARE_ACK - proposal ack message; requires instance, proposal, and type
# ACCEPT - accept request; requires ptoposal, instance, value, and type
# ACCEPT_ACK - accept ack; requires proposal, instance, value, and type
# CLIENT - client request; requires type and value
########################################################################################

# Message class for holding messages between Paxos servers and clients

class message:
    def __init__(self, type, proposal, instance, value, origin):
        self.type = None
        self.proposal = None
        self.instance = None
        self.value = None
        self.origin = None
