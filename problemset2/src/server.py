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


import socket
from multiprocessing import Queue, Process, Lock
import message
from message import MESSAGE_TYPE
import pickle
import command


class PAXOS_member(object):

    def __init__(self, server_id, server_list):
        """
            PAXOS_member, a member of PAXOS group, act as proposer, acceptor
            - server_id: the index of the server in server_list
            - server_list: list of servers in PAXOS group
        """
        assert len(server_list) > server_id
        self.server_list = server_list
        self.server_id = server_id
        self.host = server_list[server_id]["host"]
        self.internal_port = server_list[server_id]["internal_port"]
        self.client_port = server_list[server_id]["client_port"]
        self.DEBUG_TAG = "[" + str(self.host) + "," + str(self.server_id) + "]"

        # Communication queues for this server node
        self.proposer_queue = Queue()  # message queue for the proposer process
        self.acceptor_queue = Queue()  # message queue for the acceptor process

        # Initialize queue locks
        self.proposer_queue_lock = Lock()
        self.acceptor_queue_lock = Lock()

        self.instance_resolutions = []  # resolved instances
        self.lock_set = []              # (lock, client_ids) that are locked

        # Fire up a listener process
        listening_process = Process(
            target=self.initialize_listener)
        listening_process.start()
        self.listening_process = listening_process

    def group_size(self):
        """
            Return the size of the paxos group
        """
        return len(self.server_list)

    def initialize_listener(self):
        """
        Initializes a listening process which routes listening connections
            - starts up a listening socket
            - messages on the listening socket are routed appropriately to the
              relevant Paxos member
            - Handles the initialization of a process for all inter-server
             communication
        """
        try:
            # bring up the listening socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # inter-server connections on port + 1
            server_socket.bind((self.host, self.internal_port))
            server_socket.listen(30)

            #TODO: set up graceful exit
            done = 0

            # while still alive,
            # set up connections and put them on a listening process
            # - these connections are internal server communication channels
            while (done == 0):

                # connect to the socket
                connection_socket, address = server_socket.accept()

                # for each connection you accept,
                # fire another process that blocks on receives
                listening_process = Process(
                    target=self.connection_process, args=(connection_socket,))

                # starts the connection process
                listening_process.start()

                print "{} Got a connection from {}".format(
                    self.DEBUG_TAG, address)
        except Exception, e:
            print "{}: ERROR - Error listening on port {}. {}".format(
                self.DEBUG_TAG, self.internal_port, e)
        server_socket.close()

    def connection_process(self, socket):
        """
            Handles data incoming on each connection socket
            - issues a blocking call to the receive function
            - expects to receive message class type objects after unpickling
        """
        done = 0
        try:
            while (done == 0):
                # receive the message
                smsg = socket.recv(1000)

                # unpack the message data
                msg = pickle.loads(smsg)

                assert isinstance(msg, message.message)
                print "{} Got a message on the socket... {}".format(
                    self.DEBUG_TAG, msg)

                # switch on the message type
                msg_type = msg.msg_type

                # route the message to the appropriate process based its type
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
                elif(msg_type == message.MESSAGE_TYPE.PREPARE_NACK):
                    print self.DEBUG_TAG + " Got a prepare NACK message."
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
                    raise ValueError("ERROR: Got a client ACK message.")
                elif(msg_type == message.MESSAGE_TYPE.EXIT):
                    print self.DEBUG_TAG + " Got an exit message."
                    self.proposer_queue.put(msg)
                    self.acceptor_queue.put(msg)
                    done = 1
                else:
                    raise ValueError(
                        " ERROR - Got a message which makes no sense.")

        # if the socket closes, handle the disconnect exception and terminate
        except Exception, e:
            print "{} WARN - connection may end: {}".format(self.DEBUG_TAG, e)
            pass

        # close the server socket
        socket.close()

    def initialize_paxos(self):
        """
            Initializes the Paxos members on different processes after starting
            the listening sockets
        """
        self.acceptor_process = self.launch_acceptor_process()
        self.proposer_process = self.launch_proposer_process()

    def launch_acceptor_process(self):
        """
            abstract initialization processes for testing purposes
        """
        # initialize the acceptor process
        acceptor_process = Process(
            target=self.initialize_acceptor, args=())
        acceptor_process.start()

        print self.DEBUG_TAG + " Initialized proposer process..."
        assert(acceptor_process.is_alive())

        return acceptor_process

    def launch_proposer_process(self):
        """
            abstract initialization processes for testing purposes
        """

        print self.DEBUG_TAG + " Launching proposer process..."

        # initialize the proposer process
        proposer_process = Process(
            target=self.initialize_proposer, args=())
        proposer_process.start()

        print self.DEBUG_TAG + " Initialized acceptor process..."
        assert(proposer_process.is_alive())

        return proposer_process

    def initialize_proposer(self):
        """
            Intializes a proposer process that acts as a proposer Paxos member
            - creates listening socket for client connections
            - initializes connections to other server connections
            - starts main loop for proposer which reads proposal requests off
               a queue of requests
            - server_list is a list of pairs (host, port)
        """
        # counter for proposer number
        proposer_cnt = 0

        def prop_num(proposer_cnt):
            """
                make sure proposer number increases and unique
            """
            return proposer_cnt * 100 + self.server_id

        def send_to_acceptors(msg, server_connections):
            assert isinstance(msg, message.message)
            # send the proposal to acceptors
            for s_socket in server_connections:
                try:
                    s_socket.send(pickle.dumps(msg))
                except Exception, e:
                    server_connections.remove(s_socket)
                    print "{}: ERROR - {}".format(self.DEBUG_TAG, e)
                    pass
                    # TODO: remove the dead connections

        # Initialize server connections unless it's to yourself
        server_connections = []

        for (serv_id, serv) in enumerate(self.server_list):
            if serv_id == self.server_id:
                continue
            target_host = serv["host"]
            target_port = serv["internal_port"]
            try:
                connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                connection.connect((target_host, target_port))
                server_connections.append(connection)
                print "{} Proposer init connection to server at {}:{}".format(
                    self.DEBUG_TAG, target_host, target_port)
            except Exception, e:
                print "{} Failed to connect to {}:{}".format(
                    self.DEBUG_TAG, target_host, target_port)

        # Open a client port and listen on port for connections
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_socket.bind((self.host, self.client_port))
            client_socket.listen(30)
        except Exception, e:
            raise Exception(
                self.DEBUG_TAG+": cannot open client port." + str(e))

        print "{} Opening client socket on: {}".format(
            self.DEBUG_TAG, self.client_port)

        # Enter the main loop of the proposer
        done = 0

        # Initialize proposer state
        PROPOSING = 10   # proposing a proposal to the Paxos group
        ACCEPTING = 11   # waiting for accept messages to come back
        IDLE = 12        # no proposals in flight
        READY = 13       # state in which a proposal is ready for submission
        ACCEPT = 14      # state issuing accept requests

        state = IDLE

        # Initialize proposer data structures
        instance = 0       # the instance this node is proposing for

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

            ###################################################################
            # While the client still has messages it wants to issue
            # - check the request queue for commands to propose first
            # - get the messages from the client connection
            # - check the lock set - if the lock you want is held, put the
            #   request on the message request queue and spin in a WAIT
            #   state until you get a lock release
            ###################################################################

            # client processing loop:
            # service as many message from the client as
            # needed until socket closed
            while (client_done == 0):
                # receive the client command to propose:
                # - if you get an EOF exit gracefully
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
                assert isinstance(c_msg, message.message)
                assert isinstance(c_msg.value, command.command)
                assert c_msg.msg_type == message.MESSAGE_TYPE.CLIENT

                # the command sent by client
                client_command = c_msg.value
                # the command learnt by proposer (if any)
                learnt_command = c_msg.value
                # get proposer number
                this_prop = prop_num(proposer_cnt)

                state = READY
                # Paxos proposal phase if not IDLE
                while state != IDLE:
                    ###########################################################
                    # READY - node is ready to propose
                    ###########################################################
                    if state == READY:

                        print self.DEBUG_TAG + " Proposer in READY state..."

                        # get and update proposer number
                        this_prop = prop_num(proposer_cnt)
                        proposer_cnt += 1

                        # craft the proposal packet and send to acceptors
                        msg = message.message(
                            message.MESSAGE_TYPE.PREPARE,
                            this_prop, instance, None,
                            self.host, self.server_id, c_msg.client_id)
                        send_to_acceptors(msg, server_connections)

                        # update the state
                        state = PROPOSING

                    ###########################################################
                    # PROPOSING - wait for the prepare proposals to come back
                    ###########################################################
                    elif (state == PROPOSING):

                        print self.DEBUG_TAG + " Proposer in PROPOSING state.."
                        # TODO: total time out is needed
                        # PREPARE_NACKs received
                        pre_nacks = []
                        # response count
                        response_cnt = 0

                        while response_cnt <= self.group_size() / 2:
                            try:
                                # listen to responses on the server msg queue
                                msg = self.proposer_queue.get(
                                    block=True, timeout=1)
                            # if an exception occurs and we're not done,
                            # consider the proposal failed
                            except Exception as e:
                                print "{} : WARN - {}".format(
                                    self.DEBUG_TAG, e)
                                # attempt another proposal round
                                state = READY
                                break

                            assert(isinstance(msg, message.message))

                            # if the message ia a prepare ack and matches your
                            # proposal/instance, increment ack count
                            if msg.instance != instance:
                                # ignore these messages since they're leftover
                                pass
                            if msg.msg_type == MESSAGE_TYPE.PREPARE_ACK:
                                # good, +1 ack
                                assert msg.instance == instance
                                response_cnt += 1
                            elif msg.msg_type == MESSAGE_TYPE.PREPARE_NACK:
                                # store it
                                nack_msg = (msg.proposal, msg)
                                pre_nacks.append(nack_msg)
                                response_cnt += 1
                            elif (msg.msg_type == message.MESSAGE_TYPE.EXIT):
                                # exit
                                print self.DEBUG_TAG + " Proposer exit..."
                                done = 1
                                client_done = 1
                                break
                            else:
                                raise ValueError(
                                    "Wrong message got by proposer")

                        # if timeout try another round (higher prop number)
                        if response_cnt <= self.group_size() / 2:
                            state = READY
                            continue

                        # learn the value of highest prop from responses
                        if not pre_nacks:
                            highest_p, p_msg = max(pre_nacks)
                            learnt_command = p_msg.value
                        state = ACCEPT

                    ###########################################################
                    # ACCEPT - send the accept messages
                    ###########################################################
                    elif (state == ACCEPT):

                        print self.DEBUG_TAG + " Proposer in ACCEPT state..."

                        # craft the accept packet
                        accept_msg = message.message(
                            MESSAGE_TYPE.ACCEPT,
                            this_prop, instance, learnt_command,
                            self.host, self.server_id, c_msg.client_id)

                        # send the accept requests
                        send_to_acceptors(accept_msg, server_connections)

                        # advance state
                        state = ACCEPTING

                    ###########################################################
                    # ACCEPTING - wait for the accepting messages to come back
                    ###########################################################
                    elif (state == ACCEPTING):

                        print self.DEBUG_TAG + " Proposer in ACCEPTING state.."

                        response_cnt = 0

                        while response_cnt <= self.group_size() / 2:
                            try:
                                msg = self.proposer_queue.get(
                                    block=True, timeout=1)
                            except Exception, e:
                                print "{} Accepting timed out - {}".format(
                                    self.DEBUG_TAG, e)
                                break

                            assert isinstance(msg, message.message)

                            # check messages on the queue for acks
                            if msg.instance != instance:
                                # ignore left over messages from lower instance
                                assert msg.instance < instance
                                pass
                            if msg.msg_type == MESSAGE_TYPE.ACCEPT_ACK:
                                # only care response for this accept req
                                if msg.proposal == this_prop:
                                    response_cnt += 1
                            elif msg.msg_type == MESSAGE_TYPE.PREPARE_ACK:
                                # ignore leftover prepare ack messages
                                pass
                            elif msg.msg_type == message.MESSAGE_TYPE.EXIT:
                                client_done = 1
                                done = 1
                            else:
                                raise ValueError("Should not reach here.")

                        # proposal was accepted
                        if response_cnt > self.group_size() / 2:
                            # yeah! accepted
                            if learnt_command == client_command:
                                state = IDLE
                            else:
                                state = READY
                            instance += 1
                            # TODO: add resolve (inst, prop, v) to shared obj.
                        else:
                            # break by timeout:
                            # propose again
                            state = READY

                    ###########################################################
                    # Failure state
                    ###########################################################
                    else:
                        assert(False)
                        assert(state == IDLE)

                # close command processing loop
            # close while loop
        # close connection processing loop
    # close proposer process definition

    def initialize_acceptor(self):
        """
            Intializes an acceptor of the Paxos group
               - initializes connections to other server connections
               - starts a main loop which processes accept requests
        """

        def response_proposer(msg, prop_id):
            assert server_connections[prop_id]
            response_conn = server_connections[prop_id]
            try:
                response_conn.send(pickle.dumps(rmsg))
            except Exception, e:
                print self.DEBUG_TAG + "WARN - fail to response " + e

        # open socket connections to each server: server_id -> connection
        server_connections = dict()
        for server_id, p_server in enumerate(self.server_list):
            target_host = p_server["host"]
            target_port = p_server["internal_port"]

            try:
                connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                connection.connect((target_host, target_port))
                server_connections[server_id] = connection
            except Exception:
                print "{} Acceptor failed to connect to {}:{}, {}".format(
                    self.DEBUG_TAG, target_host, target_port)
                continue

        accept_history = dict()          # instance -> prep_p, acc_p, acc_v

        # Enter the proposal processing loop
        # - dequeue message for this proposer and process them
        done = 0

        while done == 0:

            # get a message of the queue
            msg = self.acceptor_queue.get()
            ###################################################################
            # handle PREPARE request
            ###################################################################
            if msg.msg_type == MESSAGE_TYPE.PREPARE:

                # extract the data fields
                p_instance = msg.instance
                p_proposal = msg.proposal

                # that is not the first message with this instance
                if p_instance in accept_history:
                    # unpack history info
                    h_prep, h_accp, h_accv = accept_history[p_instance]

                    # only response if p_proposal higher than current
                    if p_proposal > h_prep:

                        # decide message type
                        if h_accp != -1:
                            msg_type = MESSAGE_TYPE.PREPARE_NACK
                        else:
                            msg_type = MESSAGE_TYPE.PREPARE_ACK
                        # send the nack back
                        rmsg = message.message(
                            msg_type, p_proposal, p_instance,
                            h_accv, self.server_id, r_proposal=h_accp)
                        response_proposer(rmsg, msg.origin_id)

                        # update accept_history
                        accept_history[p_instance] = (
                            p_proposal, h_accp, h_accv)
                else:
                    # send ack back
                    rmsg = message.message(
                        MESSAGE_TYPE.PREPARE_ACK, p_proposal, p_instance,
                        None, self.server_id)
                    response_proposer(rmsg, msg.origin_id)

                    # update accept_history
                    accept_history[p_instance] = (p_proposal, -1, None)

            ###################################################################
            # handle ACCEPT request
            ###################################################################
            elif msg.msg_type == MESSAGE_TYPE.ACCEPT:
                # extract the data fields
                p_instance = msg.instance
                p_value = msg.value
                p_proposal = msg.proposal
                p_client_id = msg.client_id

                # check to see if the proposal number for
                # this instance is high enough
                h_prep, h_accp, h_accv = accept_history[p_instance]

                if p_proposal >= h_prep:
                    # send accept_ack message
                    rmsg = message.message(
                        MESSAGE_TYPE.ACCEPT_ACK, p_proposal, p_instance,
                        p_value, self.server_id, client_id=p_client_id)
                    response_proposer(rmsg, msg.origin_id)
                    # update accept_history
                    accept_history[p_instance] = (
                        p_proposal, p_proposal, p_value)
            ###################################################################
            # handle EXIT message
            ###################################################################
            elif (msg.msg_type == message.MESSAGE_TYPE.EXIT):
                done = 1
            # should never get this far
            else:
                raise ValueError("Should not be here.")
        # shut down inter-server communication channels
        try:
            assert(len(server_connections.keys()) > 0)
            for skey in server_connections.keys():
                server_connections[skey].close()
        except Exception, e:
            print "{} ERROR - failed to close server conn... {}".format(
                self.DEBUG_TAG, e)
