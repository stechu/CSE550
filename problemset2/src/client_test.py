#!/usr/bin/python

#########################################################################
# client_test.py
#
# Unit test for lock client
#########################################################################

import client
import sys
import os
import unittest
import command
import pickle
import socket
import subprocess
import time
import message

class client_test(unittest.TestCase):
    def setUp(self):
        # instantiate a client
        self.client = client.client()

    def test_client_connection_loopback(self):
        """
        Tests if connecting to the server works and that
        loopback works appropriately
        """
        # start up the test loopback server
        SERVER_HOSTNAME = 'localhost'
        SERVER_PORT = 9000

        print "[Lock Client Test] Attempt to open socket for server..."

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((SERVER_HOSTNAME, SERVER_PORT))
        server_socket.listen(10)

        print "[Lock Client Test] Launched server subprocess..."

        # connect to the initialized server socket
        self.client.connect_to_server(SERVER_HOSTNAME, SERVER_PORT)

        # allow server socket to accept connection
        (connection_socket, connection_address) = server_socket.accept()

        print "[Lock Client Test] Client connected to server..."

        client_id = 57

        # Client sends a command to server
        cmd_obj = command.command("lock 45")
        self.client.send_command(cmd_obj, client_id)

        # Server receives and unpickles command
        rmsgs = connection_socket.recv(1024)

        rmsg = pickle.loads(rmsgs)

        assert(isinstance(rmsg, message.message))
        assert(rmsg.value.my_command == command.COMMAND_TYPE.LOCK)
        assert(rmsg.value.my_lock_num == 45)
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.CLIENT)

        # loopback the data to the server

        connection_socket.send(pickle.dumps(rmsg))

        print "[Lock Client Test] Client issued command to server..."

        # Client receives loopback data from server
        rmsgs = self.client.receive_message()

        print "[Lock Client Test] Client received loopback data from server..."

        rmsg = pickle.loads(rmsgs)
        assert(isinstance(rmsg, message.message))
        assert(rmsg.value.my_command == command.COMMAND_TYPE.LOCK)
        assert(rmsg.value.my_lock_num == 45)
        assert(rmsg.client_id == client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.CLIENT)

        # Clean up
        self.client.exit()
        server_socket.close()
        connection_socket.close()

if __name__ == '__main__':
    unittest.main()
