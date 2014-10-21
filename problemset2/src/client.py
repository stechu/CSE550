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
import message
from multiprocessing import Queue, Process, Lock

class client:

    # Initializer for this client
    def __init__(self, cmd_file, server_host, server_port, client_id):
        self.COMMAND_FILE = cmd_file
        self.CONNECTION_SOCKET = None
        self.connect_to_server(server_host, server_port)
        self.client_id = client_id
        self.cmd_file = cmd_file
        c_process = Process(target=self.client_process, args=())
        c_process.start()

    # enables launching of client on a separate thread
    def client_process(self):
        self.send_command_file(self.cmd_file)

    def connect_to_server(self, host, port):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_socket.connect((host, port))
            self.CONNECTION_SOCKET = client_socket  # set the connection socket
        except Exception, e:
            print "Error: failed to open socket with error - " + str(e)
            exit(-1)

    # Sends the requested command to the server using pickle
    def send_command(self, cmd, client_id):
        msg = message.message(message.MESSAGE_TYPE.CLIENT,
                              None, None, cmd, 'localhost', 9000, client_id)
        self.CONNECTION_SOCKET.send(pickle.dumps(msg))

    # Receive data from the server
    def receive_message(self):
        try:
            rmsg = self.CONNECTION_SOCKET.recv(1024)
        except Exception, e:
            print e
            return None
        return rmsg

    # Validate the command format
    def create_command(self, cmd_str):
        cmd = command.command(cmd_str)
        return cmd


    def send_command_file(self, cmd_file):

        cfile = open(cmd_file, "r+")
        
        cmd_list = []

        # load the command file
        for line in cfile:
            try:
                new_cmd = command.command(line)
                cmd_list.append(new_cmd)
            except Exception, e:
                print "Client " + str(self.client_id) + " failed to parse specified file..."
                exit(-1)

        for c in cmd_list:
            # send the command
            self.send_command(c, self.client_id)
            print "Client sent command to server..."

            # wait for an ACK from the server indicating you got an ACK
            rmsg = pickle.loads(self.receive_message())
            print "Client received ACK from server..."

            assert(rmsg.msg_type == message.MESSAGE_TYPE.CLIENT_ACK)
            assert(rmsg.client_id == self.client_id)
            
            # move on to send the next one

    # Any clean up routines that should be executed
    def exit(self):
        self.CONNECTION_SOCKET.close()
