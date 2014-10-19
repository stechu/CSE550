#!/usr/bin/python

#########################################################################
# acceptor_test.py
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

class acceptor_test(unittest.TestCase):

    ###########################################################
    # Bring up just enough infrastructure to set up a test
    #  acceptor and send it messages
    ###########################################################

    def setUp(self):

        # Remote server message receive socket = 9003
        # Acceptor message receive socket = 9001
        # Acceptor client socket port = 9000

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
        except Exception, e:
            os.system("lsof -n -i")
            os.system("ps -a")
            print "[Info] Failed to bind socket for dummy server: " + str(e)
            self.dummy_server_socket.close()
            
            assert(False)

        # populate the server list
        self.server_list = [('localhost', 9003)]

        # initialize the acceptor which should initiate a connection to 9003
        self.acceptor_process = self.paxos_server.launch_acceptor_process('localhost', 9001, 0, 2, self.server_list)

        # create a test socket to inject messages to the acceptor and connect to 9001
        self.message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.message_socket.connect(('localhost', 9001))

        # accept the incoming connection that should have been made from 9001 to 9003
        (self.acceptor_connection, acceptor_address) = self.dummy_server_socket.accept()


    ###########################################################
    # Test acceptor for graceful bring up and exit
    ###########################################################

    def test_bring_up(self):

        print "\n\n[Info] ##########[BRING UP TEST]##########\n"

        pass

    ###########################################################
    # Issues a single proposal and tests if response is
    #  is received
    ###########################################################

    def test_single_proposal_prepare(self):

        print "\n\n[Info] ##########[SINGLE PROPOSAL TEST]##########\n"

        # craft the message
        proposal = 0
        instance = 1
        client_id = 2

        msg = message.message(message.MESSAGE_TYPE.PREPARE, 
                              proposal, instance, None, 'localhost', 9003, client_id)

        self.message_socket.send(pickle.dumps(msg))

        print "[Info] Sent a proposal to acceptor..."
        
        # get a response back from the paxos server
        rmsgs = self.acceptor_connection.recv(1000)
        rmsg = pickle.loads(rmsgs)
        assert(isinstance(rmsg, message.message))

        print "[Info] Received a response from server..."

        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)


    ###########################################################
    # Issues multiple proposals for the same instance and tests
    #  if correct responses are received
    ###########################################################

    def test_multiple_proposal_prepare(self):

        print "\n\n[Info] ##########[MULTIPLE PROPOSAL TEST]##########\n"

        # send and receive a valid proposal
        proposal = 1; instance = 0; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

        print "[Info] First prepare request successful..."

        # send and receive a high number valid proposal
        proposal = 3; instance = 0; client_id = 7
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

        print "[Info] Second prepare request successful..."

        # send and receive same numbered proposal
        proposal = 3; instance = 0; client_id = 7
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

        print "[Info] Third prepare request successful..."

        # send an not receive a lower numbered proposal
        proposal = 2; instance = 0; client_id = 5
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        try:
            self.acceptor_connection.settimeout(1.0)
            rmsg = self.acceptor_connection.recv(1000)
            assert(False) # a timeout should occur
        except Exception, e:
            pass

        print "[Info] Fourth prepare request test successful..."

        # send a higher number proposal just to make sure the proposer didn't die
        # send and receive same numbered proposal
        proposal = 11; instance = 0; client_id = 7
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)
        
        print "[Info] Fifth prepare request successful..."

    ###########################################################
    # Test multiple instances
    ###########################################################

    def test_multiple_instance_prepare(self):
        print "\n\n[Info] ##########[MULTIPLE INSTANCE PREAPRE TEST]##########\n"
        
        # send an initial instance number
        proposal = 0; instance = 0; client_id = 7
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)
        
        # send a higher number proposal
        proposal = 5; instance = 0; client_id = 5
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

        # send a different instance with lower proposal number
        proposal = 1; instance = 2; client_id = 5
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

        # send original instance with lower proposal number
        proposal = 3; instance = 0; client_id = 5
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        self.acceptor_connection.settimeout(1.0)
        try:
            rmsg = pickle.loads(self.acceptor_connection.recv(1000))
            assert(False)
        except Exception, e:
            pass
        
        # send to new instance with higher proposal number
        proposal = 7; instance = 2; client_id = 5
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

    ###########################################################
    # Attempt to send single accept command
    ###########################################################

    def test_single_proposal_accept(self):

        print "\n\n[Info] ##########[SINGLE PREPARE TEST]##########\n"

        # craft the message
        proposal = 0
        instance = 1
        client_id = 2

        msg = message.message(message.MESSAGE_TYPE.ACCEPT, 
                              proposal, instance, None, 'localhost', 9003, client_id)

        self.message_socket.send(pickle.dumps(msg))

        print "[Info] Sent a proposal to acceptor..."
        
        # get a response back from the paxos server
        rmsgs = self.acceptor_connection.recv(1000)
        rmsg = pickle.loads(rmsgs)
        assert(isinstance(rmsg, message.message))

        print "[Info] Received a response from server..."

        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

    ###########################################################
    # Attempt prepare and then accept of same proposal number
    ###########################################################

    def test_single_prepare_accept(self):
        
        print "\n\n[Info] ##########[SINGLE PREPARE ACCEPT TEST]##########\n"

        # send a prepare request
        proposal = 5; instance = 1; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)
        
        # send an accept request
        proposal = 5; instance = 1; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.ACCEPT,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)
        

    def test_multiple_prepare_accept(self):
        # send a prepare request
        proposal = 5; instance = 1; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)
        
        # send a prepare request
        proposal = 9; instance = 3; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)
        
        # send a prepare request
        proposal = 0; instance = 2; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)
        
        # send an accept request
        proposal = 5; instance = 1; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.ACCEPT,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

        # send a accept request
        proposal = 9; instance = 3; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.ACCEPT,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)
        
        # send a accept request
        proposal = 0; instance = 2; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.ACCEPT,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

    ###########################################################
    # Test case where prepare goes through but another proposal
    #  fires a high proposal before accept comes through
    ###########################################################

    def test_reject_accept_test(self):
        print "\n\n[Info] ##########[SINGLE PREPARE ACCEPT TEST]##########\n"
        
        # send a prepare message
        proposal = 6; instance = 0; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

        # send another prepare message with higher proposal number
        proposal = 8; instance = 0; client_id = 13
        msg = message.message(message.MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

        # send an accept message which should get rejected
        proposal = 6; instance = 0; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.ACCEPT,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        self.acceptor_connection.settimeout(1.0)
        try:
            rmsg = pickle.loads(self.acceptor_connection.recv(1000))
            assert(False)
        except Exception, e:
            pass
        
        # send an actual accept message which should get accepted
        proposal = 8; instance = 0; client_id = 9
        msg = message.message(message.MESSAGE_TYPE.ACCEPT,
                              proposal, instance, None, 'localhost', 9003, client_id)
        self.message_socket.send(pickle.dumps(msg))

        rmsg = pickle.loads(self.acceptor_connection.recv(1000))
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT_ACK)
        assert(rmsg.proposal == proposal)
        assert(rmsg.instance == instance)
        assert(rmsg.client_id == client_id)

    ###########################################################
    # Tear down infrastructure and exit
    ###########################################################

    def tearDown(self):

        # shut down the acceptor by sending an exit message from 9003 to 9001
        msg = message.message(message.MESSAGE_TYPE.EXIT,
                              None, None, None, 'localhost', 9003, None)
        self.message_socket.send(pickle.dumps(msg))

        print "[Info] Issued a shutdown message..."


        # clean up the sockets
        self.message_socket.close()
        self.dummy_server_socket.close()
        self.acceptor_connection.close()

        # attempt to join the processes
        try:
            self.acceptor_process.join(1)
        except Exception, e:
            assert(False)

        # terminate the connection process
        self.paxos_server.listening_process.terminate()

if __name__ == '__main__':
    unittest.main()
