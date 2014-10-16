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
import Queue
import socket
import threading

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

    ########################################################
    # Initializes a listening connection socket
    ########################################################

    def initialize_listening_thread(self, host, port, server_socket):
        
        print "[Server] Server is online on " + str(host) + ":" + str(port) + "\n"

        try:
            while (self.exit_flag == 0):
                # listen for a connection and create a processing thread
                (connection_socket, address) = server_socket.accept()
            
                # create a processing thread to handle connection
                connection_thread = threading.Thread(target=self.processing_thread, args = (connection_socket))
                
                # register thread and connnection
                self.active_connections_lock.acquire()
                self.active_connections[connection_thread] = connection_socket
                self.active_connections_lock.release()

                # launch processing thread
                connection_thread.start()

        except Exception, e:
            pass

        # kill remaining threads and close their connections
        print "[Server] Terminating listening thread..."

        self.server_socket.close()
        # TODO

    ########################################################
    # Establish connections to other servers
    # - connection_list - a list of pairs (hostname, port)
    #   to other members of the Paxos group
    ########################################################

    def establish_server_connections(self, connection_list):
        for connection_pair in connection_list:
            host = connection_pair[0]
            port = connection_pair[1]

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))

            self.server_connections.append(client_socket)

        print self.DEBUG_TAG + " established server connections...\n"
        
    ########################################################
    # Process commands issued by client
    # - use a state machine to determine where in the 
    #   proposal stage you are
    # - also process any accept or learn messages
    ########################################################

    def processing_thread(self, connection_socket):
        print "[Server] Launched a processing thread...\n"
        pass # STUB

    ########################################################
    # Server shutdown routines
    ########################################################

    def terminate_server(self):
        self.exit_flag = 1

        # wait for processing threads to complete
        for thread in self.active_connections.keys():
            if thread.is_alive():
                thread.join()

        # terminate the client sockets to other servers
        for sock in self.server_connections:
            sock.close()
        
        # terminate the listening thread
        if (self.listening_thread.is_alive()):
            self.listening_thread.join()

        self.server_socket.close()
  
        print "[Server] Terminated successfully...\n"
