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
from command import COMMAND_TYPE
import pickle
import command
import time
import random


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

        # set the message error rates
        params = server_list[server_id]
        if "drop_rate" in params:
            r = float(params["drop_rate"])
            assert r >= 0 and r <= 1
            self.drop_rate = params["drop_rate"]
        else:
            self.drop_rate = 0

        if ("dup_rate" in params):
            r = float(params["dup_rate"])
            assert(r >= 0 and r <= 1)
            self.dup_rate = params["dup_rate"]
        else:
            self.dup_rate = 0

        # Communication queues for this server node
        self.proposer_queue = Queue()  # message queue for the proposer process
        self.acceptor_queue = Queue()  # message queue for the acceptor process

        # Initialize queue locks
        self.proposer_queue_lock = Lock()
        self.acceptor_queue_lock = Lock()
        self.read_lock = Lock()

        self.instance_resolutions = dict()  # resolved instances
        self.lock_set = []              # (lock, client_ids) that are locked

        # Fire up a listener process
        listening_process = Process(
            target=self.initialize_listener)
        listening_process.start()
        self.listening_process = listening_process

        self.client_socket = None

#        print "[Info] Server number " + str(self.server_id) + " online..."

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

#                print "{} Got a connection from {}".format(
#                    self.DEBUG_TAG, address)
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
        def push_to_acceptor_queue(q_msg):
            """
                push to acceptor
            """
            self.acceptor_queue_lock.acquire()
            self.acceptor_queue.put(q_msg)
            self.acceptor_queue_lock.release()

        def push_to_proposer_queue(q_msg):
            """
                push to proposer
            """
            self.proposer_queue_lock.acquire()
            self.proposer_queue.put(q_msg)
            self.proposer_queue_lock.release()

        done = 0
        try:
            while (done == 0):

                # receive the message
                smsg = socket.recv(1000)

                # unpack the message data
                msg = pickle.loads(smsg)

                assert isinstance(msg, message.message)

                # switch on the message type
                msg_type = msg.msg_type

                # route the message to the appropriate process based its type
                proposer_msg_types = [
                    MESSAGE_TYPE.PREPARE_ACK,
                    MESSAGE_TYPE.PREPARE_NACK,
                    MESSAGE_TYPE.ACCEPT_ACK,
                    ]
                acceptor_msg_types = [
                    MESSAGE_TYPE.PREPARE,
                    MESSAGE_TYPE.ACCEPT,
                    ]
                # draw a dice here
                dice = random.random()

                if msg_type in proposer_msg_types:      # internal prop msgs
                    # drop message
                    if dice < self.drop_rate:
                        print "drop a messge to proposer"
                        continue
                    # dup message
                    if dice < self.dup_rate:
                        print "duplicate a messge to proposer"
                        push_to_proposer_queue(msg)
                    # actually send message
                    push_to_proposer_queue(msg)
                elif msg_type == MESSAGE_TYPE.CLIENT:   # client msgs
                    push_to_proposer_queue(msg)
                elif msg_type in acceptor_msg_types:    # internal acc msgs
                    # drop message
                    if dice < self.drop_rate:
                        print "drop a messge to acceptor"
                        continue
                    # dup message
                    if dice < self.dup_rate:
                        print "duplicate a messge to acceptor"
                        push_to_acceptor_queue(msg)
                    # actually send message
                    push_to_acceptor_queue(msg)
                elif msg_type == message.MESSAGE_TYPE.CLIENT_ACK:
                    raise ValueError("ERROR: Got a client ACK message.")
                elif msg_type == message.MESSAGE_TYPE.EXIT:
                    self.proposer_queue.put(msg)
                    self.acceptor_queue.put(msg)
                    done = 1
                else:
                    raise ValueError(
                        " ERROR - Got a message which makes no sense.")

                # check if the socket is alive
                socket.send(" ")

        # if the socket closes, handle the disconnect exception and terminate
        except Exception, e:
#            print "{} WARN - connection may end: {}".format(self.DEBUG_TAG, e)
            pass

        # close the server socket
        socket.close()

    def initialize_paxos(self):
        """
            Initializes the Paxos members on different processes after starting
            the listening sockets
        """
        self.launch_acceptor_process()
        self.launch_proposer_process()

    def launch_acceptor_process(self):
        """
            abstract initialization processes for testing purposes
        """
        # initialize the acceptor process
        acceptor_process = Process(
            target=self.initialize_acceptor, args=())
        acceptor_process.start()

#        print self.DEBUG_TAG + " Initialized proposer process..."
        assert(acceptor_process.is_alive())
        self.acceptor_process = acceptor_process

        return acceptor_process

    def launch_proposer_process(self):
        """
            abstract initialization processes for testing purposes
        """

#        print self.DEBUG_TAG + " Launching proposer process..."

        # initialize the proposer process
        proposer_process = Process(
            target=self.initialize_proposer, args=())
        proposer_process.start()

#        print self.DEBUG_TAG + " Initialized acceptor process..."
        assert(proposer_process.is_alive())
        self.proposer_process = proposer_process

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
        # the msg type need to handle dup
        proposer_msg_types = [
            MESSAGE_TYPE.PREPARE_ACK,
            MESSAGE_TYPE.PREPARE_NACK,
            MESSAGE_TYPE.ACCEPT_ACK,
        ]
        msg_history = set()

        def if_dup(msg, msg_history):
            # handle duplication
            if msg.msg_type in proposer_msg_types:
                msg_signature = (
                    msg.msg_type,
                    msg.value,
                    msg.proposal,
                    msg.r_proposal,
                    msg.client_id,
                    msg.instance,
                    msg.origin_id)
                if msg_signature in msg_history:
                    # dup, pass
                    print "dup msg to proposer!"
                    return True
                else:
                    msg_history.add(msg_signature)
                    return False

        # counter for proposer number
        proposer_num = self.server_id

        # log file
        write_lock = Lock()
        write_lock.acquire()
        logfile = open("server" + str(self.server_id) + ".txt", "w+")
        write_lock.release()

#        print "Proposer number is initially: " + str(proposer_num)

        # resolved command
        # self.instance_resolutions = dict()
        # instance_number -> (cmd, client_id)

        def send_to_acceptors(msg, server_connections):
            assert isinstance(msg, message.message)
            # send the proposal to acceptors
            for s_socket in server_connections:
                try:
                    s_socket.sendall(pickle.dumps(msg))
                except Exception, e:
                    server_connections.remove(s_socket)
                    print "{}: ERROR - {}".format(self.DEBUG_TAG, e)
                    pass
                    # TODO: remove the dead connections

        def print_instance_resolutions():
            for i in self.instance_resolutions:
                tcmd = self.instance_resolutions[i][0]
                assert isinstance(tcmd, command.command)
                print "cid: {}: {}".format(
                    self.instance_resolutions[i][1], tcmd)

        def execute_command(exe_command):
            # execute the command on the list
            if exe_command.command_type == COMMAND_TYPE.LOCK:
                assert exe_command.resource_id not in self.lock_set
                self.lock_set.append(exe_command.resource_id)
                assert exe_command.resource_id in self.lock_set
            elif exe_command.command_type == COMMAND_TYPE.UNLOCK:
                assert exe_command.resource_id in self.lock_set
                self.lock_set.remove(exe_command.resource_id)
                assert exe_command.resource_id not in self.lock_set
            else:
                assert(False)

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
#                print "{} Proposer init connection to server at {}:{}".format(
#                    self.DEBUG_TAG, target_host, target_port)
            except Exception, e:
                print "{} Failed to connect to {}:{}".format(
                    self.DEBUG_TAG, target_host, target_port)

        # Open a client port and listen on port for connections
        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client_socket.bind((self.host, self.client_port))
            self.client_socket.listen(30)
            # set the timeout to check for exit conditions
            self.client_socket.settimeout(.1)
        except Exception, e:
            raise Exception(
                self.DEBUG_TAG + ": cannot open client port." + str(e))

#        print "{} Opening client socket on: {}".format(
#            self.DEBUG_TAG, self.client_port)

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

#            print "{} Waiting for a client connection...".format(
#                self.DEBUG_TAG)

            # accept an incoming client connection
            try:
                (client_connection, address) = self.client_socket.accept()
                client_connection.settimeout(.5)
            except Exception, e:
                # check for an exit message
                try:
                    m = self.proposer_queue.get(block=True, timeout=1)
                    if (m.msg_type == MESSAGE_TYPE.EXIT):
                        done = 1
                        client_done = 1
                        break
                    else:
                        self.proposer_queue.put(m)
                except Exception, e:
                    pass
                continue

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
                try:
                    c_msgs = client_connection.recv(1000)
                except Exception, e:
#                    print "{} Client conn timed out, closing socket...".format(
#                        self.DEBUG_TAG)
                    client_connection.close()
                    break

                # unpack the message and get the command to propose from client
                try:
                    c_msg = pickle.loads(c_msgs)
                except EOFError, e:
                    print c_msgs + " - " + str(e)
                    client_done = 1
                    break

                # validate that you got a valid message with command payload
                assert isinstance(c_msg, message.message)
                assert isinstance(c_msg.value, command.command)
                assert c_msg.msg_type == message.MESSAGE_TYPE.CLIENT
                assert c_msg.client_id is not None

                # the command sent by client
                client_command = c_msg.value
                orig_client_id = c_msg.client_id

                # the command learnt by proposer (if any)
                learnt_command = c_msg.value
                learnt_client = c_msg.client_id

                state = READY
                # Paxos proposal phase if not IDLE
                while state != IDLE:

                    ###########################################################
                    # READY - node is ready to propose
                    ###########################################################
                    if state == READY:

#                        print self.DEBUG_TAG + " Proposer in READY state..."

                        # craft the proposal packet and send to acceptors
                        msg = message.message(
                            MESSAGE_TYPE.PREPARE,
                            proposer_num, instance, None,
                            self.server_id, c_msg.client_id)
                        assert msg.client_id is not None
                        send_to_acceptors(msg, server_connections)
                        # update the state
                        state = PROPOSING

                    ###########################################################
                    # PROPOSING - wait for the prepare proposals to come back
                    ###########################################################
                    elif (state == PROPOSING):

#                        print self.DEBUG_TAG + " Proposer in PROPOSING state.."
                        # PREPARE_NACKs received
                        pre_nacks = []
                        # response count
                        response_cnt = 0

                        while response_cnt <= self.group_size() / 2:
                            try:
                                # listen to responses on the server msg queue
                                msg = self.proposer_queue.get(
                                    block=True, timeout=1)
                                assert msg.client_id

                            # if an exception occurs and we're not done,
                            # consider the proposal failed
                            except Exception as e:
#                                print "{} : WARN 2 - {}".format(
#                                    self.DEBUG_TAG, e)
#                                print str(e)
                                # attempt another proposal round
                                state = READY
                                break

                            assert(isinstance(msg, message.message))

                            if if_dup(msg, msg_history):
                                continue

                            # if the message ia a prepare ack and matches your
                            # proposal/instance, increment ack count
                            if msg.instance != instance:
                                # ignore these messages since they're leftover
                                pass
                            else:
                                if msg.msg_type == MESSAGE_TYPE.PREPARE_ACK:
                                    # good, +1 ack
                                    assert msg.instance == instance
                                    response_cnt += 1
                                elif msg.msg_type == MESSAGE_TYPE.PREPARE_NACK:
                                    # store it
                                    nack_msg = (msg.proposal, msg)
                                    pre_nacks.append(nack_msg)
                                    response_cnt += 1
                                elif msg.msg_type == MESSAGE_TYPE.EXIT:
                                    # exit
                                    print self.DEBUG_TAG + " Proposer exit..."
                                    done = 1
                                    client_done = 1
                                    break
                                elif msg.msg_type == MESSAGE_TYPE.ACCEPT_ACK:
                                    pass
                                else:
                                    print self.DEBUG_TAG + str(msg)
                                    raise ValueError(
                                        "Wrong message got by prop {}".format(
                                            msg))

                        # if timeout try another round (higher prop number)
                        if response_cnt <= self.group_size() / 2:
                            # update state
                            state = READY
                            # update proposal num
                            proposer_num += self.group_size()
                            continue

                        # learn the value of highest prop from responses
                        if pre_nacks:
                            highest_p, p_msg = max(pre_nacks)
                            learnt_command = p_msg.value
                            learnt_client = p_msg.client_id

                        # if you won but are blocked, feint a failure
                        if (learnt_client == orig_client_id and
                            learnt_command == client_command and
                            learnt_command.command_type == COMMAND_TYPE.LOCK and
                            client_command.resource_id in self.lock_set):
                            time.sleep(1)
                            state = READY
                        else:
                            state = ACCEPT

                    ###########################################################
                    # ACCEPT - send the accept messages
                    ###########################################################
                    elif (state == ACCEPT):

#                        print self.DEBUG_TAG + " Proposer in ACCEPT state..."

                        # craft the accept packet
                        accept_msg = message.message(
                            MESSAGE_TYPE.ACCEPT,
                            proposer_num, instance, learnt_command,
                            self.server_id, c_msg.client_id)

                        # send the accept requests
                        assert accept_msg.client_id is not None
                        send_to_acceptors(accept_msg, server_connections)

                        # advance state
                        state = ACCEPTING

                    ###########################################################
                    # ACCEPTING - wait for the accepting messages to come back
                    ###########################################################
                    elif (state == ACCEPTING):

#                        print self.DEBUG_TAG + " Proposer in ACCEPTING state.."

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

                            if if_dup(msg, msg_history):
                                continue

                            # check messages on the queue for acks
                            if msg.instance != instance:
                                # ignore left over messages from lower instance
                                assert msg.instance < instance
                                pass
                            else:
                                if msg.msg_type == MESSAGE_TYPE.ACCEPT_ACK:
                                    # only care response for this accept req
                                    if msg.proposal == proposer_num:
                                        response_cnt += 1
                                elif msg.msg_type == MESSAGE_TYPE.PREPARE_ACK:
                                    # ignore leftover prepare ack messages
                                    pass
                                elif msg.msg_type == MESSAGE_TYPE.PREPARE_NACK:
                                    pass
                                elif msg.msg_type == message.MESSAGE_TYPE.EXIT:
                                    client_done = 1
                                    done = 1
                                else:
                                    raise ValueError("Should not reach here.")

                        # update proposer number, in any case
                        proposer_num += self.group_size()

                        # proposal was accepted
                        if response_cnt > self.group_size() / 2:
                            # yeah! accepted
                            if (learnt_command == client_command and
                                    learnt_client == orig_client_id):
                                state = IDLE
                                # send a response message
                                assert msg.client_id is not None
                                client_ack_msg = message.message(
                                    MESSAGE_TYPE.CLIENT_ACK, None, instance,
                                    client_command, self.server_id,
                                    msg.client_id)
                                client_connection.send(
                                    pickle.dumps(client_ack_msg))
                            else:
# print self.DEBUG_TAG + "Failed to get command and/or client id correct."
                                state = READY

                            self.instance_resolutions[instance] = (
                                learnt_command, msg.client_id)

                            write_lock.acquire()
                            logfile.write("{} -> cid:{} - {}\n".format(
                                instance, msg.client_id, learnt_command))
                            write_lock.release()

                            # execute command
                            execute_command(learnt_command)

                            # move to the next instance
                            instance += 1
                            # reset learnt command
                            learnt_command = client_command
                            learnt_client = orig_client_id

#                            print "{} resolve! ins={}, cmd={}, lt={}".format(
#                                self.DEBUG_TAG, instance,
#                                client_command, learnt_command)
                        else:
                            # break by timeout:
                            # propose again
                            state = READY
                            # update proposal num
                            proposer_num += self.group_size()

                    ###########################################################
                    # Failure state
                    ###########################################################
                    else:
                        assert(False)

                # close command processing loop
#            print self.DEBUG_TAG + "DROPPED OUT OF STATE FSM LOOP"
            # close while loop
#        print self.DEBUG_TAG + "DROPPED OUT OF PROPOSER LOOPS"
        # close connection processing loop
        write_lock.acquire()
        logfile.close()
        write_lock.release()

#        print "[Info] Proposer on server " + str(self.server_id) + " exited..."

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
                response_conn.sendall(pickle.dumps(rmsg))
            except Exception, e:
                server_connections.remove(response_conn)
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

        # the msg types that will be duped
        acceptor_msg_types = [
            MESSAGE_TYPE.PREPARE,
            MESSAGE_TYPE.ACCEPT,
        ]

        # msg_history to handle dups
        msg_history = set()

        # Enter the proposal processing loop
        # - dequeue message for this proposer and process them
        done = 0

        while done == 0:

            # get a message of the queue
            msg = self.acceptor_queue.get()

             # handle duplication
            if msg.msg_type in acceptor_msg_types:
                msg_signature = (
                    msg.msg_type,
                    msg.value,
                    msg.proposal,
                    msg.r_proposal,
                    msg.client_id,
                    msg.instance,
                    msg.origin_id)
                if msg_signature in msg_history:
                    # dup, pass
                    print "dup msg to acceptor!"
                    continue
                else:
                    msg_history.add(msg_signature)

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
                        msg.client_id, self.server_id)
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
                if p_instance in accept_history:
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
                else:
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

#        print "[Info] Acceptor on server " + str(self.server_id) + " exited..."
