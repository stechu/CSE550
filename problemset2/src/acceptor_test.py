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

    def setUp(self):

        # Remote server message receive socket = 9003
        # Acceptor message receive socket = 9001
        # Acceptor client socket port = 9000

        print "[Info] Initializing acceptor test with PID " + str(os.getpid())

        # Instantiate a server instance
        self.paxos_server = server.server('localhost', 9000, 0, 2)

        # Insert a wait for the server to come online
        time.sleep(1)

        print "[Info] Created a Paxos server instance..."

        # start a test remote inter-server socket on 9003
        try:
            self.test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.test_socket.bind(('localhost', 9003))
            self.test_socket.listen(5)
        except Exception, e:
            os.system("lsof -n -i")
            os.system("ps -a")
            print "[Info] Failed to bind socket for dummy server: " + str(e)
            self.test_socket.close()
            
            assert(False)

        # populate the server list
        self.server_list = [('localhost', 9003)]

        print "[Info] Bound a dummy server port for the acceptor to connect to..."

        # initialize the acceptor which should initiate a connection to 9003
        self.acceptor_process = self.paxos_server.launch_acceptor_process('localhost', 9001, 0, 2, self.server_list)

        print "[Info] Initialized an acceptor instance.."

        # create a test socket to inject messages to the acceptor and connect to 9001
        self.message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.message_socket.connect(('localhost', 9001))

        print "[Info] Connected a dummy server message channel to Paxos server..."

        # accept the incoming connection that should have been made from 9001 to 9003
        (self.acceptor_connection, acceptor_address) = self.test_socket.accept()

        print "[Info] Received test server connection to dummy server.."
        

    ###########################################################
    # Test acceptor for graceful bring up and exit
    ###########################################################

    def test_exit(self):

        # shut down the acceptor by sending an exit message from 9003 to 9001
        msg = message.message(message.MESSAGE_TYPE.EXIT,
                              None, None, None, 'localhost', 9003, None)
        self.message_socket.send(pickle.dumps(msg))

        print "[Info] Issued a shutdown message..."

    def tearDown(self):

        # clean up the sockets
        self.message_socket.close()
        self.test_socket.close()
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
