#!/usr/bin/python

#########################################################################
# lock_client.py
# - client for the lock service Paxos implementation
# - takes a file and attempt to issue the commands in the file
# - client may issue an arbitrary number of requests
#########################################################################

import sys
import os
import socket
from constants import *
import command
import cPickle as pickle


class lock_client:

    # Initializer for this client
    def __init__(self):
        self.COMMAND_FILE = None
        self.SERVER_FILE = None
        self.CONNECTION_SOCKET = None

    def connect_to_server(self, host, port):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
            self.CONNECTION_SOCKET = client_socket  # set the connection socket
        except Exception, e:
            print "Error: failed to open socket with error - " + str(e)
            exit(-1)

    # Sends the requested command to the server using pickle
    def send_command(self, cmd):
        # serialize the command object
        serialized_command = pickle.dumps(cmd)

        self.CONNECTION_SOCKET.send(serialized_command)

    # Receive data from the server
    def receive_command(self):
        received_data = self.CONNECTION_SOCKET.recv(1024)

        return received_data

    # Validate the command format
    def create_command(self, cmd_str):
        cmd = command.command(cmd_str)
        return cmd

    # Any clean up routines that should be executed
    def exit(self):
        self.CONNECTION_SOCKET.close()
