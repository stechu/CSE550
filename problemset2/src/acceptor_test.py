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
    

    # Tests the acceptor in isolation
    def test_acceptor(self):

        # Remote server message receive socket = 9003
        # Acceptor message receive socket = 9001
        # Acceptor client socket port = 9000

        print "[Info] Initializing acceptor test with PID " + str(os.getpid())

        # Instantiate a server instance
        paxos_server = server.server('localhost', 9000, 0, 2)

        # Insert a wait for the server to come online
        time.sleep(1)

        print "[Info] Created a Paxos server instance..."

        # start a test remote inter-server socket on 9003
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind(('localhost', 9003))
            test_socket.listen(5)
        except Exception, e:
            os.system("lsof -n -i")
            os.system("ps -a")
            print "[Info] Failed to bind socket for dummy server: " + str(e)
            test_socket.close()
            
            assert(False)

        # populate the server list
        server_list = [('localhost', 9003)]

        print "[Info] Bound a dummy server port for the acceptor to connect to..."

        # initialize the acceptor which should initiate a connection to 9003
        acceptor_process = paxos_server.launch_acceptor_process('localhost', 9001, 0, 2, server_list)

        print "[Info] Initialized an acceptor instance.."

        # create a test socket to inject messages to the acceptor and connect to 9001
        message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        message_socket.connect(('localhost', 9001))

        print "[Info] Connected a dummy server message channel to Paxos server..."

        # accept the incoming connection that should have been made from 9001 to 9003
        (acceptor_connection, acceptor_address) = test_socket.accept()

        print "[Info] Received test server connection to dummy server.."
        
        # shut down the acceptor by sending an exit message from 9003 to 9001
        msg = message.message(message.MESSAGE_TYPE.EXIT,
                              None, None, None, 'localhost', 9003, None)
        message_socket.send(pickle.dumps(msg))

        print "[Info] Issued a shutdown message..."

        # clean up the sockets
        message_socket.close()
        test_socket.close()

        # attempt to join the processes
        try:
            acceptor_process.join(1)
        except Exception, e:
            assert(False)

        # terminate the connection process
        paxos_server.listening_process.terminate()

if __name__ == '__main__':
    unittest.main()
