######################################################################
# message.py
#
# - message class for Paxos communication
######################################################################


class MESSAGE_TYPE(object):
    PREPARE = 0
    PREPARE_ACK = 1
    ACCEPT = 2
    ACCEPT_ACK = 3
    CLIENT = 4
    CLIENT_ACK = 5
    LEARNER = 6
    PREPARE_NACK = 7
    EXIT = 8


class message(object):
    """
        Message class for holding messages between Paxos servers and clients
         - msg_type is one of above enum values
         - proposal is proposal number
         - instance is Paxos instance number
         - value is proposed value or command
         - origin_id is paxos member id of the orignal host
         - client_id is id number associated with this request
         - r_proposal is the response proposal number
    """
    def __init__(self, msg_type, proposal, instance,
                 value, origin_id, client_id=-1, r_proposal=-1):
        self.msg_type = msg_type
        self.proposal = proposal
        self.r_proposal = r_proposal
        self.instance = instance
        self.value = value
        self.origin_id = origin_id
        self.client_id = client_id
