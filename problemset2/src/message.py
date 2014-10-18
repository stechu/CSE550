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
    LEARNER = 6
    PREPARE_NACK = 7

########################################################################################
# PREPARE - proposal mesasge; requires propoal, instance, and type
# PREPARE_ACK - proposal ack message; requires instance, proposal, and type
# ACCEPT - accept request; requires ptoposal, instance, value, and type
# ACCEPT_ACK - accept ack; requires proposal, instance, value, and type
# CLIENT - client request; requires type and value
########################################################################################

# Message class for holding messages between Paxos servers and clients

class message:
    def __init__(self, msg_type, proposal, instance, value, origin):
        self.msg_type = msg_type
        self.proposal = proposal
        self.instance = instance
        self.value = value
        self.origin = origin
