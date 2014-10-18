#!/usr/bin/python

#########################################################################
# server_test.py
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

class server_test(unittest.TestCase):
    def setUp(self):
        NUM_SERVERS = 3

        self.servers = [None] * NUM_SERVERS

        # instantiate the servers
        for i in range(0, NUM_SERVERS):
            hostname = 'localhost'
            port_num = 9000 + i
            self.servers[i] = server.server('localhost', port_num, i, NUM_SERVERS)

    def tearDown(self):
        for i in range(0, len(self.servers)):
            self.servers[i].exit_flag = 1
        self.servers[i].exit_flag = 1

    def test_server_listen_initialize(self):
        for i in range(0, len(self.servers)):
            assert(self.servers[i].listening_thread.is_alive())
        
        for i in range(0, len(self.servers)):
            self.servers[i].terminate_server()

if __name__ == '__main__':
    unittest.main()
