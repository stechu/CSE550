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

########################################################
# Paxos Server Class Definition
########################################################

class server:

    ######################################################################
    # Server constructor
    # - host = hostname server is instantiated on
    # - port = port number server will listen to
    # - server_number = unique identifier of server in initial Paxos group
    # - total_servers = total number of servers in initial Paxos group
    ######################################################################

    def __init__(self, host, port, server_number, total_servers):
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
        server_socket.bind((host, port))
        server_socket.listen(30)

        #TODO: set up graceful exit
        done = 0

        # while still alive, set up connections and put them on a listening process
        while (done == 0):
            
            # connect to the socket
            connection_socket, address = server_socket.accept()

            # for each connection you accept, fire another process that blocks on receives
            connection_process = Process(target=a, args=(connection_socket))

            pass

        
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
                msg_type = msg.type
                
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
    def initialize_proposer(self, host, port, server_number, total_servers, server_list):

        # create a request queue
        request_queue = Queue()

        # Initialize server connections unless it's to yourself
        
        for serv in total_servers:
            assert(len(serv) == 2)
            target_host = serv[0]
            target_port = serv[1]

            try:
                connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection.connect((target_host, target_port))

            except Exception, e:
                print "Failed to connect to " + str(target_host) + ":" + str(target_port)
                continue

        pass


# TODO:

'''
        self.request_queue = []      # initialize queue for request commands
        self.active_connections = dict()  # initialize map of threads -> client connections
        self.server_connections = []      # a list of server connection sockets to other servers

        # bring up the socket and initialize listening
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(30)
        self.server_socket = server_socket

        # Initialize a listening server connection thread
        self.listening_thread = threading.Thread(target=self.initialize_listening_thread, args = (host, port, server_socket))

        self.listening_thread.start()

        # Initialize a lock to serialize access to the request queue
        self.request_queue_lock = threading.Lock()

        # Initialize lock to serialize access to active connections map
        self.active_connections_lock = threading.Lock()

        # Bring up the connections to the other servers
        # TODO

        # track the server ID and total number of servers to partition proposal number set
        self.server_number = server_number
        self.total_servers = total_servers
        self.host = host
        self.port = port

        # Initialize the array of Paxos instance resolutions
        self.instance_resolutions = dict()

        self.DEBUG_TAG = "[" + str(host) + ":" + str(port) + "]"
        
        self.exit_flag = 0

'''
