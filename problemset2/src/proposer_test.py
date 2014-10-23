#!/usr/bin/python

#########################################################################
# proposer_test.py
#########################################################################

import server
import os
import unittest
import command
from command import COMMAND_TYPE
import pickle
import socket
import time
import message
from message import MESSAGE_TYPE
import random

# constant for test
R_SERVER_MSG_PORT = 9003
CLIENT_PORT = 9000
INTERNAL_PORT_SERVER = 9001


class proposer_test(unittest.TestCase):

    def setUp(self):
        """
            Bring up just enough infrastructure to set up a test
            proposer and send it messages.
        """
        # Proposer message receive socket = INTERNAL_PORT_SERVER
        # Proposer client socket port = CLIENT_PORT
        # Remote server message receive socket = R_SERVER_MSG_PORT
        self.server_list = [
            {
                "host": "localhost",
                "internal_port": INTERNAL_PORT_SERVER,
                "client_port": CLIENT_PORT
            },
            {
                "host": "localhost",
                "internal_port": R_SERVER_MSG_PORT,
                "client_port": 9002
            }
        ]

        # Instantiate a server instance
        self.paxos_server = server.PAXOS_member(0, self.server_list)

        # Insert a wait for the server to come online
        time.sleep(1)

        # start a test remote inter-server socket on R_SERVER_MSG_PORT
        try:
            self.dummy_server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.dummy_server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.dummy_server_socket.bind(('localhost', R_SERVER_MSG_PORT))
            self.dummy_server_socket.listen(5)
            print "[Info] Opened a dummy server socket on port R_SERVER_MSG_PORT"
        except Exception, e:
            os.system("lsof -n -i")
            os.system("ps -a")
            self.dummy_server_socket.close()
            raise Exception(
                "[Error] Failed to bind socket for dummy server: " + str(e))

        # initialize the proposer which should initiate a connection to R_SERVER_MSG_PORT
        self.proposer_process = self.paxos_server.launch_proposer_process()

        # accept the incoming connection that
        # should have been made from INTERNAL_PORT_SERVER to R_SERVER_MSG_PORT
        (self.proposer_connection, proposer_address) = (
            self.dummy_server_socket.accept())

        # create a test socket to inject messages
        # to the proposer and connect to INTERNAL_PORT_SERVER
        self.message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.message_socket.connect(('localhost', INTERNAL_PORT_SERVER))

        # connect a client
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.connect(('localhost', CLIENT_PORT))

    def internal_msg_to_test_server(self):
        pass

    def client_msg_to_test_server(self, cmd_type, resource_id, client_id):
        """
            send a client msg to test server
        """
        try:
            cmd = command.command(COMMAND_TYPE.LOCK, resource_id)
            msg = message.message(message.MESSAGE_TYPE.CLIENT,
                                  None, None, cmd, None, client_id)
            self.client_socket.sendall(pickle.dumps(msg))
        except Exception, e:
            print "Error when send client msg {} - {}".format(msg, e)
            raise Exception("exit")

    def test_bring_up(self):
        """
            test bring up test environment
        """
        print "\n##########[TEST BRING UP]##########\n\n"

        # fire a proposal to the server to get it to read messages
        self.client_msg_to_test_server(COMMAND_TYPE.LOCK, 5, 546)

        # get the prepare messages of the line
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert isinstance(rmsg, message.message)
        assert rmsg.client_id == 546
        print "[Info] Got a prepare message as expected..."

    def test_paxos_round(self):
        """
            Single Paxos round test - test Paxos round with
            no interference or failures.
        """
        print "\n##########[PAXOS ROUND]##########\n\n"

        client_id = random.randint(0, 1000)

        # fire a proposal to the server
        self.client_msg_to_test_server(COMMAND_TYPE.LOCK, 1, client_id)

        # get the prepare message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        print "rmsg: {}".format(rmsg)
        assert isinstance(rmsg, message.message)
        assert rmsg.client_id == client_id
        assert rmsg.msg_type == MESSAGE_TYPE.PREPARE
        assert rmsg.proposal == self.paxos_server.server_id
        assert rmsg.instance == 0

        # respond with two prepare acks
        msg = message.message(message.MESSAGE_TYPE.PREPARE_ACK,
                              rmsg.instance, rmsg.proposal, None,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))
        msg = message.message(message.MESSAGE_TYPE.PREPARE_ACK, #should be PREPARE-ACK
                              rmsg.instance, rmsg.proposal, None,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))

        # get an accept message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert isinstance(rmsg, message.message)
        assert rmsg.client_id == client_id
        assert rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT
        assert rmsg.proposal == self.paxos_server.server_id
        assert rmsg.instance == 0
        assert isinstance(rmsg.value, command.command)
        # matches the command lock request number above
        assert rmsg.value.resource_id == 1
        assert rmsg.value.command_type == command.COMMAND_TYPE.LOCK

        # respond with two accept message
        msg = message.message(message.MESSAGE_TYPE.ACCEPT_ACK,
                              rmsg.instance, rmsg.proposal, rmsg.value,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))
        self.message_socket.sendall(pickle.dumps(msg))

    def test_proposal_timeouts(self):
        """
            Test a timeouts and reissuing of prepare messages by
            proposer
        """

        print "\n##########[TEST PROPOSAL TIMEOUTS]##########\n\n"
        # make life a little bit easier
        ps = self.paxos_server

        client_id = random.randint(0, 1000)

        # fire a proposal to the server
        self.client_msg_to_test_server(COMMAND_TYPE.LOCK, 1, client_id)

        # get the prepare message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE)
        assert(rmsg.proposal == self.paxos_server.server_id)
        assert(rmsg.instance == 0)

        print "[Info] Got a prepare message and ignored it..."

        # ignore it and get the next prepare message

        # get the prepare message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert isinstance(rmsg, message.message)
        assert rmsg.client_id == client_id
        assert rmsg.msg_type == message.MESSAGE_TYPE.PREPARE
        assert rmsg.proposal == ps.server_id + ps.group_size()
        assert rmsg.instance == 0

        print "[Info] Got a second prepare message.."

        # send back responses
        msg = message.message(message.MESSAGE_TYPE.PREPARE_ACK,
                              rmsg.proposal, rmsg.instance, None,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))
        self.message_socket.sendall(pickle.dumps(msg))

        print "[Info] Sent a response message..."

        # get the accept message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert isinstance(rmsg, message.message)
        assert rmsg.client_id == client_id
        assert rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT
        assert rmsg.proposal == ps.server_id + ps.group_size()
        assert rmsg.instance == 0

        # ignore the message and send it back to the proposing state

        print "[Info] Ignored an accept message..."

        # get the next prepare message

        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert isinstance(rmsg, message.message)
        assert rmsg.client_id == client_id
        assert rmsg.msg_type == message.MESSAGE_TYPE.PREPARE
        print "rmsg : {}".format(rmsg)
        assert rmsg.proposal == ps.server_id + 2 * ps.group_size()
        assert rmsg.instance == 0

        print "[Info] Got a prepare message..."

        # send back a response
        msg = message.message(message.MESSAGE_TYPE.PREPARE_ACK,
                              rmsg.proposal, rmsg.instance, None,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))
        self.message_socket.sendall(pickle.dumps(msg))

        print "[Info] Sent two response messages..."

        # get the accept message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert isinstance(rmsg, message.message)
        assert rmsg.client_id == client_id
        assert rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT
        assert rmsg.proposal == ps.server_id + 2 * ps.group_size()
        assert rmsg.instance == 0
        assert isinstance(rmsg.value, command.command)
        assert rmsg.value.resource_id == 1
        assert rmsg.value.command_type == command.COMMAND_TYPE.LOCK

        print "[Info] Got and accept message..."

        # send back the accept ack
        msg = message.message(MESSAGE_TYPE.ACCEPT_ACK,
                              rmsg.proposal, rmsg.instance, rmsg.value,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))
        self.message_socket.sendall(pickle.dumps(msg))

        print "[Info] Sent and accept response..."

    def test_instance_advancement(self):
        """
            Tests if the instances advance appropriately
        """

        print "\n##########[TEST PROPOSAL TIMEOUTS]##########\n\n"
        # make life a little bit easier
        ps = self.paxos_server

        client_id = random.randint(0, 1000)
        expected_instance = 0

        # fire a proposal to the server
        self.client_msg_to_test_server(COMMAND_TYPE.LOCK, 1, client_id)

        # get the prepare message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE)
        assert(rmsg.proposal == self.paxos_server.server_id)
        assert(rmsg.instance == expected_instance)
        
        # send back responses
        msg = message.message(message.MESSAGE_TYPE.PREPARE_ACK,
                              rmsg.proposal, rmsg.instance, None,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))
        self.message_socket.sendall(pickle.dumps(msg))

        # get the accept message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT)
        assert(rmsg.proposal == self.paxos_server.server_id)
        assert(rmsg.instance == expected_instance)

        # send back two response messages
        msg = message.message(message.MESSAGE_TYPE.ACCEPT_ACK,
                              rmsg.proposal, rmsg.instance, None,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))
        self.message_socket.sendall(pickle.dumps(msg))

        # we should now be done with the first instance, start the second instance

        expected_instance += 1

        # fire a proposal to the server
        self.client_msg_to_test_server(COMMAND_TYPE.LOCK, 1, client_id)

        # get the prepare message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.PREPARE)
        assert(rmsg.proposal == self.paxos_server.server_id + len(self.paxos_server.server_list))
        assert(rmsg.instance == expected_instance)
        
        # send back responses
        msg = message.message(message.MESSAGE_TYPE.PREPARE_ACK,
                              rmsg.proposal, rmsg.instance, None,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))
        self.message_socket.sendall(pickle.dumps(msg))

        # get the accept message
        rmsg = pickle.loads(self.proposer_connection.recv(1000))
        assert(isinstance(rmsg, message.message))
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.ACCEPT)
        assert(rmsg.proposal == self.paxos_server.server_id + len(self.paxos_server.server_list))
        assert(rmsg.instance == expected_instance)

        # send back two response messages
        msg = message.message(message.MESSAGE_TYPE.ACCEPT_ACK,
                              rmsg.proposal, rmsg.instance, None,
                              None, rmsg.client_id)
        self.message_socket.sendall(pickle.dumps(msg))
        self.message_socket.sendall(pickle.dumps(msg))


    def tearDown(self):
        """
            Tear down infrastructure and exit
        """
        # shut down the proposer by sending an exit message from R_SERVER_MSG_PORT to INTERNAL_PORT_SERVER
        msg = message.message(message.MESSAGE_TYPE.EXIT,
                              None, None, None, None, None)
        self.message_socket.sendall(pickle.dumps(msg))

        print "[Info] Issued a shutdown message..."

        # clean up the sockets
        self.message_socket.close()
        self.dummy_server_socket.close()
        self.proposer_connection.close()
        self.client_socket.close()

        self.paxos_server.listening_process.join(1)
        self.paxos_server.proposer_process.join(1)

        # attempt to join the processes
        # try:
        #    self.proposer_process.join(2)
        # except Exception, e:
        #    assert(False)

        # terminate the connection process
        self.paxos_server.listening_process.terminate()
        self.paxos_server.proposer_process.terminate()

        print "PAXOS INSTANCE RESOLUTIONS:\n" + str(self.paxos_server.instance_resolutions)
            
        print "[Info] Terminate listening process..."

        print "\n##########[END TEST]##########\n"


if __name__ == '__main__':
    unittest.main()
