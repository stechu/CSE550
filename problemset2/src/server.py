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
import pickle
import command

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
        self.DEBUG_TAG = "[" + str(host) + ":" + str(port) + "]"

        # Communication queues for this server node
        self.proposer_queue = Queue()  # message queue bound for the proposer process
        self.acceptor_queue = Queue()  # message queue bound for the acceptor process
        self.learner_queue = Queue()   # message queue bound for the leaner process

        # Initialize queue locks
        self.proposer_queue_lock = Lock()
        self.acceptor_queue_lock = Lock()
        self.learner_queue_lock = Lock()

        self.instance_resolutions = [] # set of known resolved instances
        self.lock_set = []             # the set of (lock, client_ids) that are locked

        # Fire up a listener process
        listening_process = Process(target=self.initialize_listener, args=(host, port))
        listening_process.start()
        self.listening_process = listening_process

        #print self.DEBUG_TAG + " Done bringing up Paxos member..."

    ######################################################################
    # Initializes a listening process which routes listening connections
    # - starts up a listening socket
    # - messages on the listening socket are routed appropriately to the
    #   relevant Paxos member
    # - Handles the initialization of a process for all inter-server
    #   communication
    ######################################################################
    
    def initialize_listener(self, host, port):
        #print self.DEBUG_TAG + " Starting listener on process " + str(os.getpid())
        
        try:
            # bring up the listening socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, int(port) + 1)) # inter-server connections on port + 1
            server_socket.listen(30)

            #print self.DEBUG_TAG + " Opened inter_server socket on port " + str(port + 1)

            #TODO: set up graceful exit
            done = 0

            # while still alive, set up connections and put them on a listening process
            # - these connections are internal server communication channels
            while (done == 0):
            
                # connect to the socket
                connection_socket, address = server_socket.accept()

                # for each connection you accept, fire another process that blocks on receives
                listening_process = Process(target=self.connection_process, args=(connection_socket,))

                # starts the connection process
                listening_process.start()

        except Exception, e:
            print self.DEBUG_TAG + " ERROR - Error initializing listening process on port " + str(port + 1) + " - " + str(e)

        server_socket.close()

    ######################################################################
    # Handles data incoming on each connection socket
    # - issues a blocking call to the receive function
    # - expects to receive message class type objects after unpickling
    ######################################################################

    def connection_process(self, socket):
        done = 0

        #print self.DEBUG_TAG + " Connection handler initialized with PID " + str(os.getpid())

        try:
            while (done == 0):
                # receive the message
                smsg = socket.recv(1000)

                # unpack the message data
                msg = pickle.loads(smsg)

                assert(isinstance(msg, message.message))

                # switch on the message type
                msg_type = msg.msg_type
                
                # route the message to the appropriate process based on the message type
                if (msg_type == message.MESSAGE_TYPE.PREPARE):
                    print self.DEBUG_TAG + " Got a prepare message."
                    self.acceptor_queue_lock.acquire()
                    self.acceptor_queue.put(msg)
                    self.acceptor_queue_lock.release()
                elif(msg_type == message.MESSAGE_TYPE.PREPARE_ACK):
                    print self.DEBUG_TAG + " Got a prepare ACK message."
                    self.proposer_queue_lock.acquire()
                    self.proposer_queue.put(msg)
                    self.proposer_queue_lock.release()
                elif(msg_type == message.MESSAGE_TYPE.ACCEPT):
                    print self.DEBUG_TAG + " Got an accept message."
                    self.acceptor_queue_lock.acquire()
                    self.acceptor_queue.put(msg)
                    self.acceptor_queue_lock.release()
                elif(msg_type == message.MESSAGE_TYPE.ACCEPT_ACK):
                    print self.DEBUG_TAG + " Got a accept ACK message."
                    self.proposer_queue_lock.acquire()
                    self.proposer_queue.put(msg)
                    self.proposer_queue_lock.release()
                elif(msg_type == message.MESSAGE_TYPE.CLIENT):
                    print self.DEBUG_TAG + " Got a client message."
                    self.proposer_queue_lock.acquire()
                    self.proposer_queue.put(msg)
                    self.proposer_queue_lock.release()
                elif(msg_type == message.MESSAGE_TYPE.CLIENT_ACK):
                    print self.DEBUG_TAG + " Got a client ACK message."
                    assert(false) # the server should never receive this message type
                elif(msg_type == message.MESSAGE_TYPE.EXIT):
                    print self.DEBUG_TAG + " Got an exit message."
                    self.proposer_queue.put(msg)
                    self.acceptor_queue.put(msg)
                    self.learner_queue.put(msg)
                    done = 1
                else:
                    print self.DEBUG_TAG + " ERROR - Got a message which makes no sense."
                    assert(false) # the server should never get here

        # if the socket closes, handle the disconnect exception and terminate
        except Exception, e:
            print self.DEBUG_TAG + " ERROR - exception raised: " + str(e)
            pass

        # close the server socket
        socket.close()

    ######################################################################
    # Initializes the Paxos members on different processes after starting
    # the listening sockets
    ######################################################################

    def initialize_paxos(self, host, port, server_number, total_servers, server_list):
        self.acceptor_process = launch_acceptor_process(self, host, port, server_number, total_servers, server_list)
        self.proposer_process = launch_proposer_process(self, host, port, server_number, total_servers, server_list)

    # abstract initialization processes for testing purposes
    def launch_acceptor_process(self, host, port, server_number, total_servers, server_list):
        # initialize the acceptor process
        acceptor_process = Process(target=self.initialize_acceptor,
                                   args=(host, port, server_number, total_servers, server_list))
        acceptor_process.start()

        #print self.DEBUG_TAG + " Initialized proposer process..."

        return acceptor_process

    # abstract initialization processes for testing purposes
    def launch_proposer_process(self, host, port, server_number, total_servers, server_list):

        # initialize the proposer process
        proposer_process = Process(target=self.initialize_proposer, 
                                   args=(host, port, server_number, total_servers, server_list))
        proposer_process.start()

        #print self.DEBUG_TAG + " Initialized acceptor process..."

        return proposer_process

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

        ######################################################################
        # Data structure initializations
        ######################################################################

        # create a request queue for pending commands
        request_queue = Queue()

        # proposer port must be even
        assert((int(port) % 2) == 0)

        # Initialize server connections unless it's to yourself

        server_connections = []
        
        for serv in server_list:
            assert(len(serv) == 2)
            target_host = serv[0]
            target_port = serv[1]
            assert((int(target_port) % 2) == 1)  # interserver ports are odd

            try:
                connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                connection.connect((target_host, target_port))
                server_connections.append(connection)
            except Exception, e:
                print "Failed to connect to " + str(target_host) + ":" + str(target_port) + " " + str(e)
                continue

        print self.DEBUG_TAG + " Opening client socket on: " + str(self.port)

        # Open a client port and listen on port for connections
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        BROADCAST = 15  # send learner messages to propagate messages

        state = IDLE

        # Initialize proposer data structures
        proposal_instance = 0       # the instance this node is proposing for
        instance_proposal_map = dict()   # a mapping of instance -> current proposal number

        ######################################################################
        # Open connection to the client
        # - accepts a client connection
        # - processes the client requests until client is done
        ######################################################################

        # Begin processing messages from the message queue
        while (done == 0):

            # accept an incoming client connection
            (client_connection, address) = client_socket.accept()

            client_done = 0

            ######################################################################
            # While the client still has messages it wants to issue
            # - check the request queue for commands to propose first
            # - get the messages from the client connection
            # - check the lock set - if the lock you want is held, put the request
            #   on the message request queue and spin in a WAIT state until you get
            #   a lock release
            ######################################################################

            # client processing loop - service as many message from the client as needed until socket closed
            while (client_done == 0):

                # receive the client command to propose - if you get an EOF exit gracefully
                c_msgs = client_connection.recv(1000)

                # unpack the message and get the command to propose from client
                try:
                    c_msg = pickle.loads(c_msgs)
                except EOFError, e:
                    print c_msgs + " - " + str(e)
                    client_done = 1
                    done = 1
                    break

                # validate that you got a valid message with command payload
                assert(isinstance(c_msg, message.message))
                cmd = c_msg.value
                assert(isinstance(cmd, command.command))
                assert(c_msg.msg_type == message.MESSAGE_TYPE.CLIENT)

                # if the lock you want is held, go to a waiting state
                if (cmd.my_command == command.COMMAND_TYPE.LOCK and
                    cmd.my_lock_num in lock_set):
                    request_queue.put(cmd)
                    state = WAIT
                else:
                    state = READY

                # reset the ack count
                ack_count = 0

                # Paxos proposal phase if not IDLE
                while (state != IDLE):

                    ###############################################################################
                    # WAIT - until the lock becomes available
                    ###############################################################################
                    
                    if (state == WAIT):
                        # TODO: dequeue messages
                        pass

                    ###############################################################################
                    # READY - node is ready to propose
                    ###############################################################################
                    elif (state == READY):

                        print self.DEBUG_TAG + " Proposer in READY state..."
                        
                        # if never proposed during this instance, initialize proposal number
                        if (not proposal_instance in instance_proposal_map.keys()):
                            instance_proposal_map[proposal_instance] = server_number
                        
                        # craft the proposal packet
                        msg = message.message(message.MESSAGE_TYPE.PREPARE, 
                                              instance_proposal_map[proposal_instance],
                                              proposal_instance,
                                              None,
                                              self.host,
                                              self.port,
                                              c_msg.client_id)

                        # send the proposal to acceptors
                        for s_socket in server_connections:
                            try:
                                s_socket.send(pickle.dumps(msg))
                            except Exception, e:
                                server_connections.remove(s_socket)
                                pass  # TODO: remove the appropriate connection that has died
                                
                        # update the state
                        state = PROPOSING
                        ack_count = 0

                    ###############################################################################
                    # PROPOSING - wait for the proposals to come back
                    ###############################################################################
                    elif (state == PROPOSING):

                        print self.DEBUG_TAG + " Proposer in PROPOSING state..."
                        
                        try:
                            # listen to responses on the server message queue
                            msg = self.proposer_queue.get(block=True, timeout=1)

                            # TODO: another timeout must be implemented here since a proposer can get constantly flooded with other messages to prevent this one from progressing

                        # if an exception occurs and we're not done, consider the proposal failed
                        except Exception as e:
                            print str(e)
                            # increment the proposal number
                            instance_proposal_map[proposal_instance] += total_servers

                            # attempt another proposal round
                            state = READY
                            
                            continue
                        
                        assert(isinstance(msg, message.message))

                        # if the message ia a prepare ack and matches your proposal/instance, increment ack count
                        if (msg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK):
                            assert(msg.instance != None)
                            if (msg.instance == proposal_instance):
                                ack_count += 1
                                # TODO: MUST MAKE THIS ACK INCREMENT ROBUST AGAINST MESSAGE DUPLICATION
                        elif (msg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK):
                            pass            # ignore these messages since they're leftover from previous rounds
                        elif (msg.msg_type == message.MESSAGE_TYPE.EXIT):
                            print self.DEBUG_TAG + " Proposer got an exit message..."
                            done = 1
                            client_done = 1
                            break
                        else:
                            assert(False)   # should never get any other message type

                        # if you get enough acks move to accept the proposal
                        if (ack_count >= int(len(server_list)/2) + 1):
                            state = ACCEPT
                            ack_count = 0
                            
                    ###############################################################################
                    # ACCEPT - send the accept messages
                    ###############################################################################
                    elif (state == ACCEPT):

                        print self.DEBUG_TAG + " Proposer in ACCEPT state..."
                        
                        # craft the accept packet
                        accept_msg = message.message(message.MESSAGE_TYPE.ACCEPT,
                                                     instance_proposal_map[proposal_instance],
                                                     proposal_instance,
                                                     cmd,
                                                     self.host,
                                                     self.port,
                                                     c_msg.client_id)

                        # fire off the accept requests
                        for s_socket in server_connections:
                            s_socket.send(pickle.dumps(accept_msg))

                        # advance state
                        state = ACCEPTING
                        ack_count = 0

                    ###############################################################################
                    # ACCEPTING - wait for the accepting messages to come back
                    ###############################################################################
                    elif (state == ACCEPTING):
                        
                        print self.DEBUG_TAG + " Proposer in ACCEPTING state..."

                        try:
                            msg = self.proposer_queue.get(block=True, timeout=1)

                        except Exception, e:
                            print self.DEBUG_TAG + " Accepting phase timed out " + str(e)

                            # increment the proposal number
                            instance_proposal_map[proposal_instance] += total_servers

                            # attempt another proposal round
                            state = READY
                            ack_count = 0

                        assert(isinstance(msg, message.message))

                        # check messages on the queue for acks
                        if (msg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK):
                            assert(msg.instance != None)
                            if (msg.instance == proposal_instance):
                                ack_count += 1
                            # TODO: make message receive robust against message duplication
                        elif (msg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK):
                            pass  #ignore leftover prepare ack messages
                        elif (msg.msg_type == message.MESSAGE_TYPE.EXIT):
                            client_done = 1
                            done = 1
                        else:
                            assert(msg.msg_type == -1) # should never get here

                        # proposal was accepted
                        if (ack_count >= (int(len(server_list)/2) + 1)):
                            state = BROADCAST
                            # TODO: add additional state for when the lock is requested but not available

                    ###############################################################################
                    # BROADCAST - distribute messages to all members with chosen value
                    ###############################################################################
                    elif (state == BROADCAST):
                        
                        print self.DEBUG_TAG + " Proposer in BROADCAST state..."

                        # craft the message for learners and fire them to all learners 
                        msg = message.message(message.MESSAGE_TYPE.LEARNER,
                                              instance_proposal_map[proposal_instance],
                                              proposal_instance,
                                              cmd,
                                              self.host,
                                              self.port,
                                              c_msg.client_id)

                        # fire the messages to each server
                        for s_socket in server_connections:
                            s_socket.send(pickle.dumps(msg))

                        # send an acknowledgement message to the client if we got the lock
                        

                        # reset the state now that we finished
                        state = IDLE
                        ack_count = 0

                    ###############################################################################
                    # Failure state
                    ###############################################################################
                    else:
                        assert(False)
                        assert(state == IDLE)

                # by default always look at the learner message queue for resolved instances 
                # TODO: abandon proposals and reset states appropriately when you get colliding instance acks

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

        #print (self.DEBUG_TAG + " Initializing acceptor process with PID " + str(os.getpid()))

        # host port must be even
        assert((int(port) % 2) == 0)

        # open socket connections to each server with (hostname, port) pairs as keys
        server_connections = dict()
        for s in server_list:

            assert(len(s) == 2)
            target_host = s[0]
            target_port = s[1]
            assert((int(target_port) % 2) == 1)  # inter-server ports are odd

            try:
                connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                connection.connect((target_host, target_port))
                server_connections[(target_host, target_port)] = connection
                #print (self.DEBUG_TAG + " Established connection to server at " + target_host + ":" + str(target_port))
            except Exception, e:
                print "Failed to connect to " + str(target_host) + ":" + str(target_port)
                continue

        instance_proposal_map = dict()   # holds the highest promised sequence numbers per instance
        resolved_instances = []          # holds list of resolved instances

        #print (self.DEBUG_TAG + " Done initializing processes...")

        # Enter the proposal processing loop - dequeue message for this proposer and process them
        done = 0

        # TODO: fix the case for 2 servers where a majority is two
        while (done == 0):

            # get a message of the queue
            msg = self.acceptor_queue.get()

            #print (self.DEBUG_TAG + " Received a message with type " + str(msg.msg_type))

            # switch based on the message type
            if (msg.msg_type == message.MESSAGE_TYPE.PREPARE):
                
                # extract the data fields
                p_instance = msg.instance
                p_proposal = msg.proposal
                p_client_id = msg.client_id

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
                                           None,
                                           self.host,
                                           self.port,
                                           p_client_id)
                    assert(server_connections[(msg.origin_host, msg.origin_port)] != None)
                    response_connection = server_connections[(msg.origin_host, msg.origin_port)]
                    response_connection.send(pickle.dumps(rmsg))
                    print self.DEBUG_TAG + " Sent a prepare_ack in response to proposal..."

            # if the message type is an ACCEPT request
            elif(msg.msg_type == message.MESSAGE_TYPE.ACCEPT):
                
                # extract the data fields
                p_instance = msg.instance
                p_value = msg.value
                p_proposal = msg.proposal
                p_client_id = msg.client_id
                
                if (p_instance in resolved_instances):
                    pass
                    # TODO: send an ACCEPT_NACK with resolved instance numbers

                # check if we've ever received a proposal number for this instance
                if (not p_instance in instance_proposal_map.keys()):
                    instance_proposal_map[p_instance] = p_proposal

                # check to see if the proposal number for th instance is high enough
                if (p_proposal >= instance_proposal_map[p_instance]):
                    instance_proposal_map[p_instance] = p_proposal
                    rmsg = message.message(message.MESSAGE_TYPE.ACCEPT_ACK,
                                           p_proposal,
                                           p_instance,
                                           None,
                                           self.host,
                                           self.port,
                                           p_client_id)
                    assert(server_connections[(msg.origin_host, msg.origin_port)] != None)
                    response_connection = server_connections[(msg.origin_host, msg.origin_port)]
                    response_connection.send(pickle.dumps(rmsg))

            # also subscribe to learner messages to determine the resolved instances
            elif (msg.msg_type == message.MESSAGE_TYPE.LEARNER):
                r_instance = msg.instance
                if (not r_instance in resolved_instances):
                    resolved_instances.append(r_instance)
            # if you get an exit flag signal the done flag to break
            elif (msg.msg_type == message.MESSAGE_TYPE.EXIT):
                done = 1
            # should never get this far
            else:
                assert(msg.msg_type == -1)

        # shut down inter-server communication channels
        try:
            assert(len(server_connections.keys()) > 0)
            for skey in server_connections.keys():
                server_connections[skey].close()
        except Exception, e:
            print self.DEBUG_TAG + " ERROR - failed to close server connection..."

        
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
