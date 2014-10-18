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
        server_socket.bind((SERVER_HOSTNAME, SERVER_PORT))
        server_socket.listen(10)

        print "[Lock Client Test] Launched server subprocess..."

        # connect to the initialized server socket
        self.client.connect_to_server(SERVER_HOSTNAME, SERVER_PORT)

        # allow server socket to accept connection
        (connection_socket, connection_address) = server_socket.accept()

        print "[Lock Client Test] Client connected to server..."

        # Client sends a command to server
        cmd_obj = command.command("lock 45")
        self.client.send_command(cmd_obj)

        # Server receives and unpickles command
        server_recv_cmds = connection_socket.recv(1024)

        server_recv_cmd = pickle.loads(server_recv_cmds)

        assert(server_recv_cmd.my_command == command.COMMAND_TYPE.LOCK)
        assert(server_recv_cmd.my_lock_num == 45)

        # loopback the data to the server

        connection_socket.send(server_recv_cmds)

        # close the connection on the server
        connection_socket.close()

        print "[Lock Client Test] Client issued command to server..."

        # Client receives loopback data from server
        recv_data = self.client.receive_command()

        print "[Lock Client Test] Client received loopback data from server..."

        # Deserialize the data
        recv_cmd_obj = pickle.loads(recv_data)

        # Validate the same object came back
        assert(recv_cmd_obj.my_command == command.COMMAND_TYPE.LOCK)
        assert(recv_cmd_obj.my_lock_num == 45)

        self.client.exit()
        server_socket.close()

if __name__ == '__main__':
    unittest.main()
