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
        pass

    def test_client_connection_loopback(self):

        # file initialization
        self.test_file_name = "test_file.txt"
        self.test_file = open(self.test_file_name, "w+")
        self.test_file.write("lock 1\n")
        self.test_file.close()

        # Tests if connecting to the server works and that loopback works appropriately
        
        # start up the test loopback server
        SERVER_HOSTNAME = 'localhost'
        SERVER_PORT = 9000

        print "[Lock Client Test] Attempt to open socket for server..."

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((SERVER_HOSTNAME, SERVER_PORT))
        server_socket.listen(10)

        print "[Lock Client Test] Launched server socket..."

        # instantiate a client
        self.client_id = 239
        self.client = client.client(self.test_file_name, 'localhost', 9000, self.client_id)

        print "[Lock Client Test] Client initialized to server..."

        # allow server socket to accept connection from the client
        (connection_socket, connection_address) = server_socket.accept()

        print "[Lock Client Test] Client connected to server..."

        # Server receives and unpickles command
        rmsgs = connection_socket.recv(1024)

        rmsg = pickle.loads(rmsgs)

        assert(isinstance(rmsg, message.message))
        assert(rmsg.value.my_command == command.COMMAND_TYPE.LOCK)
        assert(rmsg.value.my_lock_num == 1)
        assert(rmsg.client_id == self.client_id)
        assert(rmsg.msg_type == message.MESSAGE_TYPE.CLIENT)

        # loopback the data to the client with a modified CLIENT ACK type
        rmsg.msg_type = message.MESSAGE_TYPE.CLIENT_ACK

        connection_socket.send(pickle.dumps(rmsg))

        # shutdown the client
        self.client.exit()
        server_socket.close()
        connection_socket.close()

    def tearDown(self):
        pass
        # Clean up

if __name__ == '__main__':
    unittest.main()
