#!/usr/bin/python

#########################################################################
# lock_client.py
# - client for the lock service Paxos implementation
# - takes a file and attempt to issue the commands in the file
# - client may issue an arbitrary number of requests
#########################################################################

import socket
from constants import *
import command
from command import COMMAND_TYPE
import cPickle as pickle
import message
from message import MESSAGE_TYPE
from multiprocessing import Process


class client:

    # Initializer for this client
    def __init__(self, cmd_file, server_host, server_port, client_id):
        self.COMMAND_FILE = cmd_file
        self.CONNECTION_SOCKET = None
        self.connect_to_server(server_host, server_port)
        self.client_id = client_id
        self.cmd_file = cmd_file
        self.c_process = Process(target=self.client_process, args=())
        self.debug_tag = "[client-{}]".format(client_id)
        self.c_process.start()
        self.server_host = server_host
        self.server_port = server_port

    # enables launching of client on a separate thread
    def client_process(self):
        self.send_commands_from_file(self.cmd_file)

    def connect_to_server(self, host, port):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_socket.connect((host, port))
            # set a timeout for which you assume
            # the server has failed afterwards
            client_socket.settimeout(30)
            self.CONNECTION_SOCKET = client_socket  # set the connection socket
        except Exception, e:
            print "Error: failed to open socket with error - " + str(e)
            raise Exception("Error")

    # Sends the requested command to the server using pickle
    def send_command(self, cmd, client_id):
        msg = message.message(MESSAGE_TYPE.CLIENT,
                              None, None, cmd, client_id, client_id=client_id)
        assert msg.client_id is not None
        try:
            self.CONNECTION_SOCKET.send(pickle.dumps(msg))
        except Exception, e:
            # the server node failed so abort
            print "client - warn {}".format(e)
            pass

    # Receive data from the server
    def receive_message(self):
        try:
            rmsg = self.CONNECTION_SOCKET.recv(1024)
        except Exception, e:
            print "client side error: " + str(e) + " " + str(self.client_id)
            return None
        return rmsg

    def create_command(self, cmd_str):
        """
            validate command string format, return command
        """
        # parse cmd_str
        cmd_items = cmd_str.rstrip(" ").rstrip("\n").split(" ")
        print cmd_items
        action, res_id = cmd_items
        # validate it
        assert action.lower() in ["lock", "unlock"]

        # return command object
        cmd_type = COMMAND_TYPE.LOCK
        if action.lower() == "unlock":
            cmd_type = COMMAND_TYPE.UNLOCK
        return command.command(cmd_type, int(res_id))

    def send_commands_from_file(self, cmd_file):
        """
            read commands from file, send them sequentially
        """
        cfile = open(cmd_file, "r+")
        cmd_list = []

        # load the command file
        for line in cfile:
            cmd_list.append(self.create_command(line))

        for c in cmd_list:
            # send the command
            self.send_command(c, self.client_id)

            # wait for an ACK from the server indicating you got an ACK
            try:
                rmsg = pickle.loads(self.receive_message())
            except Exception, e:
                #the server node died or something bad happened so abort
                break

            assert rmsg.msg_type == message.MESSAGE_TYPE.CLIENT_ACK
            try:
                assert rmsg.client_id == self.client_id
            except Exception, e:
                print "rmsg={}, client_id={}, error={}".format(
                    rmsg.client_id, self.client_id, e)
            # move on to send the next one

    # Any clean up routines that should be executed
    def exit(self):
        self.CONNECTION_SOCKET.close()
