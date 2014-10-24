#!/usr/bin/python

#########################################################################
# acceptor_test.py
#########################################################################

import server
import os
import unittest
import pickle
import socket
import time
import message
from message import MESSAGE_TYPE


class acceptor_test(unittest.TestCase):

    def setUp(self):
        """
            Bring up just enough infrastructure to set up a test
            acceptor and send it messages
        """
        # Instantiate a server instance
        self.server_list = [
            {
                "host": "localhost",
                "internal_port": 9001,
                "client_port": 9002
            },
            {
                "host": "localhost",
                "internal_port": 9003,
                "client_port": 9004
            }
        ]
        self.paxos_server = server.PAXOS_member(0, self.server_list)

        # Insert a wait for the server to come online
        time.sleep(1)

        # create a dummy server of test
        self.dummy_server_id = 1

        # start a test remote inter-server socket on 9003
        try:
            self.dummy_server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.dummy_server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.dummy_server_socket.bind(('localhost', 9003))
            self.dummy_server_socket.listen(5)
        except Exception, e:
            os.system("lsof -n -i")
            os.system("ps -a")
            self.dummy_server_socket.close()
            emsg = "[Info] Failed to bind socket for dummy server: " + str(e)
            raise ValueError(emsg)

        # initialize the acceptor which should initiate a connection to 9003
        self.acceptor_process = self.paxos_server.launch_acceptor_process()

        # create a test socket to inject messages to the acceptor
        self.message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.message_socket.connect(('localhost', 9001))

        # accept the incoming connection that should have been made
        # from 9001 to 9003
        self.acceptor_connection, acceptor_address = (
            self.dummy_server_socket.accept())

    def send_prepare(self, prop, ins, rmsg_type, rmsg_prop, rmsg_ins):
        """
            Helper function, send prepare message to server, check
            returned message
            - prop: proposal number to be sent
            - ins: instance number to be sent
            - rmsg_type: expected returned message type
            - rmsg_prop: expected returned message proposal number
            - rmsg_ins: expected returned message instane number
        """
        msg = message.message(
            MESSAGE_TYPE.PREPARE, prop, ins, None, self.dummy_server_id)
        self.message_socket.send(pickle.dumps(msg))

        print "[Info] Sent a proposal to acceptor..."
        rmsgs = self.acceptor_connection.recv(1000)
        rmsg = pickle.loads(rmsgs)
        assert isinstance(rmsg, message.message)

        print "[Info] Received a response from server..."

        assert rmsg.msg_type == rmsg_type
        if rmsg.proposal != rmsg_prop:
            print (rmsg.proposal, rmsg_prop)

        assert rmsg.proposal == rmsg_prop
        assert rmsg.instance == rmsg_ins

        return rmsg

    def send_accept(self, prop, ins, cid, value,
                    rmsg_type, rmsg_prop, rmsg_ins, rmsg_cid):
        """
            Helper function, send accept message to server, check
            returned message
            - prop: proposal number to be sent
            - ins: instance number to be sent
            - cid: client id to be sent
            - value: value to be sent
            - rmsg_type: expected returned message type
            - rmsg_prop: expected returned message proposal number
            - rmsg_ins: expected returned message instane number
            - rmsg_cid: expected returned message client id
        """
        msg = message.message(MESSAGE_TYPE.ACCEPT, prop, ins,
                              value, self.dummy_server_id, cid)
        self.message_socket.send(pickle.dumps(msg))

        rmsgs = self.acceptor_connection.recv(1000)
        rmsg = pickle.loads(rmsgs)
        assert isinstance(rmsg, message.message)

        assert rmsg.msg_type == rmsg_type
        assert rmsg.proposal == rmsg_prop
        assert rmsg.instance == rmsg_ins
        assert rmsg.client_id == rmsg_cid

        return rmsg

    def test_bring_up(self):
        """
            Test acceptor for graceful bring up and exit
        """
        print "\n\n[Info] ##########[BRING UP TEST]##########\n"

    def test_single_proposal_prepare(self):
        """
            Issues a single proposal and tests if response
            is received
        """
        print "\n\n[Info] ##########[SINGLE PROPOSAL TEST]##########\n"

        # craft the message, proposal = 0, instance = 1
        self.send_prepare(0, 1, MESSAGE_TYPE.PREPARE_ACK, 0, 1)

    def test_multiple_proposal_prepare(self):
        """
            Issues multiple proposals for the same instance and tests
            if correct responses are received
        """
        print "\n\n[Info] ##########[MULTIPLE PROPOSAL TEST]##########\n"

        # send and receive a valid proposal, proposal = 1, instance = 0
        self.send_prepare(1, 0, MESSAGE_TYPE.PREPARE_ACK, 1, 0)
        print "[Info] First prepare request successful..."

        # send and receive another valid proposal, proposal = 3, instance = 0
        self.send_prepare(3, 0, MESSAGE_TYPE.PREPARE_ACK, 3, 0)
        print "[Info] Second prepare request successful..."

        # send an not receive a lower numbered proposal
        proposal, instance = 2, 0
        msg = message.message(MESSAGE_TYPE.PREPARE,
                              proposal, instance, None, self.dummy_server_id)
        self.message_socket.send(pickle.dumps(msg))

        try:
            self.acceptor_connection.settimeout(1.0)
            self.acceptor_connection.recv(1000)
            assert False    # time out should happen
        except Exception, e:
            print e
            pass

        print "[Info] Fourth prepare request test successful..."

        # send a higher number proposal just to make sure
        # the proposer didn't die, proposal = 11, instance = 0
        self.send_prepare(11, 0, MESSAGE_TYPE.PREPARE_ACK, 11, 0)
        print "[Info] Fifth prepare request successful..."

    def test_multiple_instance_prepare(self):
        """
            Test multiple instances
        """
        print "\n\n[Info] ##########[MULTIPLE INSTANCE PREAPRE TEST]########\n"

        # send an initial instance number, proposal = 0, instance = 0
        self.send_prepare(0, 0, MESSAGE_TYPE.PREPARE_ACK, 0, 0)

        # send a higher number proposal, proposal = 5, instance = 0
        self.send_prepare(5, 0, MESSAGE_TYPE.PREPARE_ACK, 5, 0)

        # send a different instance, proposal = 1, instance = 2
        self.send_prepare(1, 2, MESSAGE_TYPE.PREPARE_ACK, 1, 2)

        # send original instance with lower proposal number
        proposal, instance = 3, 0
        msg = message.message(MESSAGE_TYPE.PREPARE, proposal, instance,
                              None, self.dummy_server_id)
        self.message_socket.send(pickle.dumps(msg))
        self.acceptor_connection.settimeout(1.0)
        try:
            pickle.loads(self.acceptor_connection.recv(1000))
            assert(False)
        except Exception, e:
            print e
            pass

        # send to new instance with higher proposal number
        # proposal = 7, instance = 2
        self.send_prepare(7, 2, MESSAGE_TYPE.PREPARE_ACK, 7, 2)

    def test_multiple_prepare_accept(self):
        """
            Attempt prepare and then accept of same proposal number
        """
        # send a prepare request, proposal = 5, instance = 1
        self.send_prepare(5, 1, MESSAGE_TYPE.PREPARE_ACK, 5, 1)

        # send a prepare request, proposal = 9, instance = 3
        self.send_prepare(9, 3, MESSAGE_TYPE.PREPARE_ACK, 9, 3)

        # send an accept request, proposal = 5, instance = 1, client_id = 9
        self.send_accept(5, 1, 9, 5, MESSAGE_TYPE.ACCEPT_ACK, 5, 1, 9)

        # send a prepare request, proposal = 0, instance = 2
        self.send_prepare(0, 2, MESSAGE_TYPE.PREPARE_ACK, 0, 2)

        # send a accept request, proposal = 9, instance = 3, client_id = 9
        self.send_accept(9, 3, 9, 5, MESSAGE_TYPE.ACCEPT_ACK, 9, 3, 9)

        # send a accept request, proposal = 0, instance = 2, client_id = 9
        self.send_accept(0, 2, 9, 5, MESSAGE_TYPE.ACCEPT_ACK, 0, 2, 9)

    def test_reject_accept(self):
        """
            Test case where prepare goes through but another proposal
            fires a high proposal before accept comes through
        """
        print "\n\n[Info] ##########[SINGLE PREPARE ACCEPT TEST]##########\n"

        # send a prepare message, proposal = 6, instance = 0
        self.send_prepare(6, 0, MESSAGE_TYPE.PREPARE_ACK, 6, 0)

        # send another prepare message, proposal = 8; instance = 0
        self.send_prepare(8, 0, MESSAGE_TYPE.PREPARE_ACK, 8, 0)

        # send an accept message which should get rejected
        proposal, instance, client_id = 6, 0, 9
        msg = message.message(MESSAGE_TYPE.ACCEPT, proposal, instance,
                              None, self.dummy_server_id, client_id)
        self.message_socket.send(pickle.dumps(msg))

        self.acceptor_connection.settimeout(1.0)
        try:
            pickle.loads(self.acceptor_connection.recv(1000))
            assert(False)
        except Exception, e:
            print e
            pass

        print "[Info] send actual valid accept req"

        # send an actual accept message which should get accepted
        # proposal = 8, instance = 0, client_id = 9
        self.send_accept(8, 0, 9, 5, MESSAGE_TYPE.ACCEPT_ACK, 8, 0, 9)

    def test_return_prepare_nack(self):
        """
            Test that acceptor will return highest proposal accepted and its
            value correctly.
        """
        # send a prepare message, proposal = 1, instance = 0
        self.send_prepare(1, 0, MESSAGE_TYPE.PREPARE_ACK, 1, 0)

        # send an accept message, proposal = 1, instance = 0, value = 5
        self.send_accept(1, 0, 0, 5, MESSAGE_TYPE.ACCEPT_ACK, 1, 0, 0)

        # send a prepare message, proposal = 3, instance = 0,
        rmsg = self.send_prepare(3, 0, MESSAGE_TYPE.PREPARE_NACK, 3, 0)
        assert rmsg.r_proposal == 1
        print "rmsg.value : {}".format(rmsg.value)
        assert rmsg.value == 5

    def tearDown(self):
        """
            Tear down infrastructure and exit
        """
        # shut down the acceptor by sending an exit message from 9003 to 9001
        msg = message.message(message.MESSAGE_TYPE.EXIT,
                              None, None, None, None, None)
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
            print e
            assert(False)

        # terminate the connection process
        self.paxos_server.listening_process.terminate()

if __name__ == '__main__':
    unittest.main()
