######################################################################
# server.py
#
# - open listening connection for processing of incoming client
#   lock requests; listening thread creates new thread per
#   connection which keeps track of requests made and attempts to
#   issue proposals
# - commands are serialized into queue awaiting issuing by server
# - server attempts to issue command at head of queue
# - if server receives consensus, command is dequeued and sends
#   an acknowledgement to the client
# - if a Paxos round fails, the same command is attempt for issue
# - also runs an acceptor thread listening to connections from other
#   servers
######################################################################

import os
import sys
import socket
import multiprocessing
from multiprocessing import Queue, Process, Lock
import message

class server:
    
    ######################################################################
    # Server constructor
    # - host = hostname server is instantiated on
    # - port = port number server will listen to
    # - server_number = unique identifier of server in initial Paxos group
    # - total_servers = total number of servers in initial Paxos group
    ######################################################################
    
    def __init__(self, host, port, server_number, total_servers):

        # enforce all ports are even such that odd ports can be inter-server communication ports
        assert((int(port) % 2 == 0))   

        self.host = host
        self.port = port
        self.server_number = server_number
        self.total_servers = total_servers

        # Communication queues for this server node
        self.proposer_queue = Queue()  # message queue bound for the proposer process
        self.acceptor_queue = Queue()  # message queue bound for the acceptor process
        self.learner_queue = Queue()   # message queue bound for the leaner process

        # Initialize queue locks
        self.proposer_queue_lock = Lock()
        self.acceptor_queue_lock = Lock()
        self.learner_queue_lock = Lock()

        # Fire up a listener process
        listening_process = Process(target=initialize_listener, args=(host, port))
        listening_process.start()
        self.listening_process = listening_process


    ######################################################################
    # Initializes a listening process which routes listening connections
    # - starts up a listening socket
    # - messages on the listening socket are routed appropriately to the
    #   relevant Paxos member
    ######################################################################
    
    def initialize_listener(self, host, port):
        
        # bring up the listening socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port + 1)) # inter-server connections on port + 1
        server_socket.listen(30)

        #TODO: set up graceful exit
        done = 0

        # while still alive, set up connections and put them on a listening process
        # - these connections are internal server communication channels
        while (done == 0):
            
            # connect to the socket
            connection_socket, address = server_socket.accept()

            # for each connection you accept, fire another process that blocks on receives
            connection_process = Process(target=a, args=(connection_socket))

        
    ######################################################################
    # Handles data incoming on each connection socket
    # - issues a blocking call to the receive function
    # - expects to receive message class type objects after unpickling
    ######################################################################

    def connection_process(self, socket):
        done = 0

        try:
            while (done == 0):
                # receive the message
                smsg = socket.recv()

                # unpack the message data
                msg = pickle.loads(smessage)

                # switch on the message type
                msg_type = msg.msg_type
                
                # route the message to the appropriate process based on the message type
                if (msg_type == message.MESSAGE_TYPE.PREPARE):
                    self.acceptor_queue_lock.lock()
                    self.acceptor_queue.put(msg)
                    self.acceptor_queue_lock.unlock()
                elif(msg_type == message.MESSAGE_TYPE.PREPARE_ACK):
                    self.proposer_queue_lock.lock()
                    self.proposer_queue.put(msg)
                    self.proposer_queue_lock.unlock()
                elif(msg_type == message.MESSAGE_TYPE.ACCEPT):
                    self.acceptor_queue_lock.lock()
                    self.acceptor_queue.put(msg)
                    self.acceptor_queue_lock.unlock()
                elif(msg_type == message.MESSAGE_TYPE.ACCEPT_ACK):
                    self.proposer_queue_lock.lock()
                    self.proposer_queue.put(msg)
                    self.proposer_queue_lock.unlock()
                elif(msg_type == message.MESSAGE_TYPE.CLIENT):
                    self.proposer_queue_lock.lock()
                    self.proposer_queue.put(msg)
                    self.proposer_queue_lock.unlock()
                elif(msg_type == message.MESSAGE_TYPE.CLIENT_ACK):
                    assert(false) # the server should never receive this message type
                else:
                    assert(false) # the server should never get here

        # if the socket closes, handle the disconnect exception and terminate
        except Exception, e:
            continue


    ######################################################################
    # Intializes a proposer process that acts as a proposer Paxos member
    # - creates listening socket for client connections
    # - initializes connections to other server connections
    # - starts main loop for proposer which reads proposal requests off
    #   a queue of requests
    # - server_list is a list of pairs (host, port)
    ######################################################################

    # TODO: figure out how to advance instance number

    def initialize_proposer(self, host, port, server_number, total_servers, server_list):

        # create a request queue
        request_queue = Queue()

        # Initialize server connections unless it's to yourself

        server_connections = []
        
        for serv in total_servers:
            assert(len(serv) == 2)
            target_host = serv[0]
            target_port = serv[1]

            try:
                connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection.connect((target_host, target_port))
                server_connections.append(connection)
            except Exception, e:
                print "Failed to connect to " + str(target_host) + ":" + str(target_port)
                continue

        # Open a client port and listen on port for connections
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.bind((host, port))
        client_socket.listen(30)

        # Enter the main loop of the proposer
        done = 0

        # Initialize proposer state
        PROPOSING = 10   # proposing a proposal to the Paxos group
        ACCEPTING = 11   # waiting for accept messages to come back
        IDLE = 12        # no proposals in flight
        READY = 13       # state in which a proposal is ready for submission
        ACCEPT = 14      # state issuing accept requests
        DISTRIBUTE = 15  # send learner messages to propagate messages

        state = IDLE

        # Initialize proposer data structures
        proposal_instance = 0       # the instance this node is proposing for
        instance_proposal_numbers = dict()   # a mapping of instance -> current proposal number

        # Begin processing messages from the message queue
        while (done == 0):

            # connect to client
            (client_connection, address) = client_socket.connect()

            # client processing loop - service as many message from the client as needed until socket closed
            while (1):

                # receive the client command to propose
                smsg = client_connection.recv()

                # unpack the message and get the command to propose from client
                msg = pickle.loads(smsg)
                assert(isinstance(msg, message.message))
                cmd = msg.value
                assert(isinstance(cmd, command.command))
                assert(msg.msg_type == message.MESSAGE_TYPE.CLIENT)

                state = READY

                ack_count = 0

                # Paxos proposal phase if not IDLE
                while (state != IDLE):

                    # fire off the proposal messages
                    if (state == READY):
                        
                        # if never proposed during this instance, initialize proposal number
                        if (instance_proposal_numbers[proposal_instance] == None):
                            instance_proposal_numbers[proposal_instance] = server_number
                        
                        # craft the proposal packet
                        msg = message.message(message.MESSAGE_TYPE.PREPARE, 
                                              instance_proposal_numbers[proposal_instance],
                                              proposal_instance,
                                              None,
                                              self.host,
                                              self.port)

                        # send the proposal to acceptors
                        for s_socket in server_connections:
                            s_socket.send(pickle.dumps(msg))
                            
                        # update the state
                        state = PROPOSING
                        ack_count = 0

                    # wait for proposals to come back
                    elif (state == PROPOSING):
                        
                        try:
                            # listen to responses on the server message queue
                            msg = self.proposer_queue.get(block=true, timeout=1)
                            
                            assert(isinstance(msg, message.message))
                            assert(msg.instance != None)

                            if (msg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK and
                                msg.instance == proposal_instance):
                                ack_count += 1
                            elif (msg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK):
                                pass            # ignore these messages since they're leftover from previous rounds
                            else:
                                assert(msg.msg_type == -1)   # should never get any other message type

                            # if you get enough acks move to accept the proposal
                            if (ack_count >= int(ack_count/2) + 1):
                                state = ACCEPT
                                ack_count = 0

                        # if an exception occurs and we're not done, consider the proposal failed
                        except Exception, e:
                            # increment the proposal number
                            instance_proposal_numbers[proposal_instance] += total_servers

                            # attempt another proposal round
                            state = READY
                            
                    # fire off the accept requests
                    elif (state == ACCEPT):
                        
                        # craft the accept packet
                        accept_msg = message.message(message.MESSAGE_TYPE.ACCEPT,
                                                     instance_proposal_numbers[proposal_instance],
                                                     proposal_instance,
                                                     cmd,
                                                     self.host,
                                                     self.port)

                        # fire off the accept requests
                        for s_socket in server_connections:
                            s_socket.send(pickle.dumps(accept_msg))

                        # advance state
                        state = ACCEPTING
                        ack_count = 0

                    # wait for messages to come back for accept
                    elif (state == ACCEPTING):
                        
                        try:
                            msg = self.proposer_queue.get(block=true, timeout=1)

                            assert(isinstance(msg, message.message))
                            assert(msg.instance != None)

                            # check messages on the queue for acks
                            if (msg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK and
                                msg.instance == proposal_instance):
                                ack_count += 1
                            elif (msg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK):
                                pass  #ignore leftover prepare ack messages
                            else:
                                assert(msg.msg_type == -1) # should never get here

                            # proposal was accepted
                            if (ack_count >= (int(total_servers/2) + 1)):
                                state = DISTRIBUTE
                                # TODO: add additional state for when the lock is requested but not available

                        except Exception, e:
                            # increment the proposal number
                            instance_proposal_numbers[proposal_instance] += total_servers

                            # attempt another proposal round
                            state = READY
                            ack_count = 0

                    # distribute messages to learners
                    elif (state == DISTRIBUTE):
                        
                        # craft the message for learners and fire them to all learners 
                        msg = message.message(message.MESSAGE_TYPE.LEARNER,
                                              instance_proposal_numbers[proposal_number],
                                              proposal_instance,
                                              cmd,
                                              self.host,
                                              self.port)

                        # fire the messages to each server
                        for s_socket in server_connections:
                            s_socket.send(pickle.dumps(msg))

                        # reset the state now that we finished
                        state = IDLE
                        ack_count = 0

                    # fail - should never get here
                    else:
                        assert(state == IDLE)

                # close command processing loop
            # close while loop
        # close connection processing loop
    # close proposer process definition

    ######################################################################
    # Intializes an acceptor of the Paxos group
    # - initializes connections to other server connections
    # - starts a main loop which processes accept requests
    # - server_list is a list of pairs (host, port)
    ######################################################################

    def initialize_acceptor(self, host, port, server_number, total_servers, server_list):
        # open socket connections to each server with (hostname, port) pairs as keys
        server_connections = dict()
        for s in server_list:

            assert(len(s) == 2)
            target_host = s[0]
            target_port = s[1]

            try:
                connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection.connect((target_host, target_port))
                server_connections[(target_host, target_port)] = connection
            except Exception, e:
                print "Failed to connect to " + str(target_host) + ":" + str(target_port)
                continue

        instance_proposal_map = dict()   # holds the highest promised sequence numbers per instance
        resolved_instances = []          # holds list of resolved instances

        # Enter the proposal processing loop - dequeue message for this proposer and process them
        done = 0

        while (done == 0):

            # get a message of the queue
            msg = self.acceptor_queue.get()

            # switch based on the message type
            if (msg.msg_type == message.MESSAGE_TYPE.PREPARE):
                
                # extract the data fields
                p_instance = msg.instance
                p_proposal = msg.proposal

                # check if the instance has been resolved
                if (p_instance in resolved_instances):
                    pass
                    # TODO: send a PREPARE_NACK with the instance number

                # check if we've ever received a proposal number for this instance
                if (not p_instance in instance_proposal_map.keys()):
                    instance_proposal_map[p_instance] = 0

                # check to see if the proposal number for the instance is high enough
                if (p_proposal >= instance_proposal_map[p_instance]):
                    instance_proposal_map[p_instance] = p_proposal
                    rmsg = message.message(message.MESSAGE_TYPE.PREPARE_ACK,
                                           p_proposal,
                                           p_instance,
                                           self.host,
                                           self.port)
                    assert(server_connections[(msg.origin_host, msg.origin_port)] != None)
                    response_connection = server_connections[(msg.origin_host, msg.origin_port)]
                    response_connection.send(pickle.dumps(rmsg))

            # if the message type is an ACCEPT request
            elif(msg.msg_type == message.MESSAGE_TYPE.ACCEPT):
                
                # extract the data fields
                p_instance = msg.instance
                p_value = msg.value
                p_proposal = msg.proposal
                
                if (p_instance in resolved_instances):
                    pass
                    # TODO: send an ACCEPT_NACK with resolved instance numbers

                # check if we've ever received a proposal number for this instance
                if (not p_instance in instance_proposal_map.keys()):
                    instance_proposal_map[p_instance] = p_proposal

                # check to see if the proposal number for th instance is high enough
                if (p_proposal >= instance_proposal_map[p_instnce]):
                    instance_proposal_map[p_instnace] = p_proposal
                    rmsg = message.message(message.MESSAGE_TYPE.ACCEPT_ACK,
                                           p_proposal,
                                           p_instnace,
                                           self.host,
                                           self.port)
                    assert(server_connections[(msg.origin_host, msg.origin_port)] != None)
                    response_connection = server_connections[(msg.origin_host, msg.origin_port)]
                    response_connection.send(pickle.dumps(rmsg))

            # also subscribe to learner messages to determine the resolved instances
            elif (msg.msg_type == message.MESSAGE_TYPE.LEARNER):
                r_instance = msg.instance
                if (not r_instance in resolved_instances):
                    resolved_instances.append(r_instance)
            # should never get this far
            else:
                assert(msg.msg_type == -1)
    
        # close while (done == 0)
    # close definition of acceptor

    ######################################################################
    # Intializes a learner of the Paxos group
    # - listens to learner messages to construct the command stream
    # - TODO: issue a proposal via the proposer to determine missing 
    #   instance resolutions
    # - TODO: consider combining the proposer and learner into one process
    #   information propagation is then easier to propose and resolve
    ######################################################################

    def initialize_learner(self, host, port, server_number, total_servers):

        # TODO: on every round compute the last known state of the lock set

        # TODO: when you get a message based on the lock state, put a new proposal on the proposer queue

        pass
