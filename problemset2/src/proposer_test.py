#!/usr/bin/python

#########################################################################
# proposer_test.py
#########################################################################

import server
import sys
import os
import unittest
import command
import pickle
import socket
import subprocess
import time
import message
from multiprocessing import Queue, Process, Lock
import random

class proposer_test(unittest.TestCase):

    ###########################################################
    # Bring up just enough infrastructure to set up a test
    #  proposer and send it messages
    ###########################################################

    def setUp(self):

        # Remote server message receive socket = 9003
        # Proposer message receive socket = 9001
        # Proposer client socket port = 9000

        # Instantiate a server instance
        self.paxos_server = server.server('localhost', 9000, 0, 2)

        # Insert a wait for the server to come online
        time.sleep(1)

        # start a test remote inter-server socket on 9003
        try:
            self.dummy_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.dummy_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.dummy_server_socket.bind(('localhost', 9003))
            self.dummy_server_socket.listen(5)
            print "[Info] Opened a dummy server socket on port 9003"
        except Exception, e:
            os.system("lsof -n -i")
            os.system("ps -a")
            print "[Info] Failed to bind socket for dummy server: " + str(e)
            assert(False)

            self.dummy_server_socket.close()
            
            assert(False)

        # populate the server list with dummy server and server instance port on 9001
        self.server_list = [('localhost', 9003)]

        # initialize the proposer which should initiate a connection to 9003
        self.proposer_process = self.paxos_server.launch_proposer_process('localhost', 9000, 0, 2, self.server_list)

        # accept the incoming connection that should have been made from 9001 to 9003
        (self.proposer_connection, proposer_address) = self.dummy_server_socket.accept()

        # create a test socket to inject messages to the proposer and connect to 9001
        self.message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.message_socket.connect(('localhost', 9001))

        # connect a client
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.connect(('localhost', 9000))

    ###########################################################
    # Bring up test
    ###########################################################

    def test_bring_up(self):

        print "\n##########[TEST BRING UP]##########\n\n"

        # fire a proposal to the server to get it to read messages
        cmd = command.command("lock 1")

        msg = message.message(message.MESSAGE_TYPE.CLIENT,
                              None, None, cmd, None, None, 546)
        self.client_socket.send(pickle.dumps(msg))

        # get the prepare messages of the line
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == 546)
        print "[Info] Got a prepare message as expected..."

    ###########################################################
    # Single Paxos round test - test Paxos round with
    #  no interference or failures
    ###########################################################
    
    def test_paxos_round(self):

        print "\n##########[PAXOS ROUND]##########\n\n"

        client_id = random.randint(0, 1000)

        # fire a proposal to the server
        cmd = command.command("lock 1")

        msg = message.message(message.MESSAGE_TYPE.CLIENT,
                              None, None, cmd, None, None, client_id)
        self.client_socket.send(pickle.dumps(msg))

        # get the prepare message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE)
        assert(rmsg.proposal == self.paxos_server.server_number)
        assert(rmsg.instance == 0)

        # respond with a prepare ack
        msg = message.message(message.MESSAGE_TYPE.PREPARE_ACK,
                              rmsg.instance, rmsg.proposal, None,
                              'localhost', 9003, rmsg.client_id)
        self.message_socket.send(pickle.dumps(msg))

        # get an accept message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT)
        assert(rmsg.proposal == self.paxos_server.server_number)
        assert(rmsg.instance == 0)
        assert(isinstance(rmsg.value, command.command))
        assert(rmsg.value.my_lock_num == 1) # matches the command lock request number above
        assert(rmsg.value.my_command == command.COMMAND_TYPE.LOCK)

        # respond with an accept message
        msg = message.message(message.MESSAGE_TYPE.ACCEPT_ACK,
                              rmsg.instance, rmsg.proposal, rmsg.value,
                              'localhost', 9003, rmsg.client_id)
        self.message_socket.send(pickle.dumps(msg))

        # get a broadcast message from the server socket
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.LEARNER)
        assert(rmsg.proposal == self.paxos_server.server_number)
        assert(rmsg.instance == 0)
        assert(isinstance(rmsg.value, command.command))
        assert(rmsg.value.my_lock_num == 1)
        assert(rmsg.value.my_command == command.COMMAND_TYPE.LOCK)

    ###########################################################
    # Test a timeouts and reissuing of prepare messages by
    #  proposer
    ###########################################################

    def test_proposal_timeouts(self):

        print "\n##########[TEST PROPOSAL TIMEOUTS]##########\n\n"

        client_id = random.randint(0, 1000)

        # fire a proposal to the server
        cmd = command.command("lock 1")

        msg = message.message(message.MESSAGE_TYPE.CLIENT,
                              None, None, cmd, None, None, client_id)
        self.client_socket.send(pickle.dumps(msg))

        # get the prepare message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE)
        assert(rmsg.proposal == self.paxos_server.server_number)
        assert(rmsg.instance == 0)

        # ignore it and get the next prepare message

        # get the prepare message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE)
        assert(rmsg.proposal == self.paxos_server.server_number + self.paxos_server.total_servers)
        assert(rmsg.instance == 0)

        # send back a response
        msg = message.message(message.MESSAGE_TYPE.PREPARE_ACK,
                              rmsg.proposal, rmsg.instance, None, 'localhost', 9003, rmsg.client_id)
        self.message_socket.send(pickle.dumps(msg))

        # get the accept message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT)
        assert(rmsg.proposal == self.paxos_server.server_number + self.paxos_server.total_servers)
        assert(rmsg.instance == 0)
        
        # ignore the message and send it back to the proposing state
        
        # get the next prepare message

        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE)
        assert(rmsg.proposal == self.paxos_server.server_number + 2 * self.paxos_server.total_servers)
        assert(rmsg.instance == 0)
        
        # send back a response
        msg = message.message(message.MESSAGE_TYPE.PREPARE_ACK,
                              rmsg.proposal, rmsg.instance, None, 'localhost', 9003, rmsg.client_id)
        self.message_socket.send(pickle.dumps(msg))
                              
        # get the accept message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT)
        assert(rmsg.proposal == self.paxos_server.server_number + 2 * self.paxos_server.total_servers)
        assert(rmsg.instance == 0)
        assert(isinstance(rmsg.value, command.command))
        assert(rmsg.value.my_lock_num == 1)
        assert(rmsg.value.my_command == command.COMMAND_TYPE.LOCK)

        # send back the accept ack
        msg = message.message(message.MESSAGE_TYPE.ACCEPT_ACK,
                              rmsg.proposal, rmsg.instance, rmsg.value, 'localhost', 9003, rmsg.client_id)
        self.message_socket.send(pickle.dumps(msg))

        # get the broadcast messge
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.LEARNER)
        assert(rmsg.proposal == self.paxos_server.server_number + 2 * self.paxos_server.total_servers)
        assert(rmsg.instance == 0)


    ###########################################################
    # Tear down infrastructure and exit
    ###########################################################

    def tearDown(self):

        # shut down the proposer by sending an exit message from 9003 to 9001
        msg = message.message(message.MESSAGE_TYPE.EXIT,
                              None, None, None, 'localhost', 9003, None)
        self.message_socket.send(pickle.dumps(msg))

        print "[Info] Issued a shutdown message..."

        # clean up the sockets
        self.message_socket.close()
        self.dummy_server_socket.close()
        self.proposer_connection.close()
        self.client_socket.close()
        
        # attempt to join the processes
        try:
            self.proposer_process.join(2)
        except Exception, e:
            assert(False)

        # terminate the connection process
        self.paxos_server.listening_process.terminate()

        print "[Info] Terminate listening process..."

        assert(not self.proposer_process.is_alive())
        assert(self.paxos_server.listening_process.is_alive())

if __name__ == '__main__':
    unittest.main()
