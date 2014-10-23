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

    def msg_type_str(self):
        if self.msg_type == MESSAGE_TYPE.PREPARE:
            return "PREPARE"
        elif self.msg_type == MESSAGE_TYPE.PREPARE_ACK:
            return "PREPARE_ACK"
        elif self.msg_type == MESSAGE_TYPE.ACCEPT:
            return "ACCEPT"
        elif self.msg_type == MESSAGE_TYPE.ACCEPT_ACK:
            return "ACCEPT_ACK"
        elif self.msg_type == MESSAGE_TYPE.CLIENT:
            return "CLIENT"
        elif self.msg_type == MESSAGE_TYPE.CLIENT_ACK:
            return "CLIENT_ACK"
        elif self.msg_type == MESSAGE_TYPE.PREPARE_NACK:
            return "PREPARE_NACK"
        elif self.msg_type == MESSAGE_TYPE.EXIT:
            return "EXIT"

    def __str__(self):
        return "msg({}, p={}, i={}, cid={})".format(
            self.msg_type_str(), self.proposal, self.instance, self.client_id)
