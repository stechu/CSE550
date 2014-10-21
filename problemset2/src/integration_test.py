#!/usr/bin/python

#########################################################################
# proposer_test.py
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
import random

class integration_test(unittest.TestCase):

    ###############################################################
    # Bring up a full Paxos group with multiple server instances
    ###############################################################

    def setUp(self):

        # set test server size
        self.TOTAL_SERVERS = 1

        # initialize server list
        self.server_list = []

        # generate the host numbers and ports of server connections
        for i in range(9001, 9001 + 2 * self.TOTAL_SERVERS, 2):
            port = i
            host = 'localhost'

            self.server_list.append((host, port))

        # bring up each server
        self.servers = []

        # iterate through address list and instantiate servers
        for addr in self.server_list:
            assert(len(addr) == 2)
            client_port = addr[1] - 1
            host = addr[0]

            # instantiate new servers
            new_server = server.server(host, client_port, len(self.servers), len(self.server_list))

            self.servers.append(new_server)

        assert(len(self.servers) == len(self.server_list))
        assert(len(self.servers) == self.TOTAL_SERVERS)

        # initialize new servers
        for i in range(0, len(self.servers)):
            s = self.server_list[i]
            assert(s != None)
            assert(((s[1]-1) % 2) == 0)
            self.servers[i].initialize_paxos(s[0], s[1] - 1, i, len(self.servers), self.server_list)

    ###############################################################
    # Test to see if the Paxos server group shutsdown correctly
    ###############################################################

    def test_bring_up(self):
        # assert processes are running
#        for s in self.servers:
 #           assert(s.listening_process.is_alive())
  #          assert(s.proposer_process.is_alive())
   #         assert(s.acceptor_process.is_alive())
        pass

    ###############################################################
    # Shutdown the Paxos group
    ###############################################################

    def tearDown(self):

        # directly inject an exit message to each of the queues
        exit_msg = message.message(message.MESSAGE_TYPE.EXIT,
                                   None, None, None, 'localhost', 9000, None)
 
        for s in self.servers:
            s.acceptor_queue.put(exit_msg)
            s.proposer_queue.put(exit_msg)

        # join the acceptor and proposer processes for each server
        for s in self.servers:
            s.listening_process.terminate()
            s.listening_process.join(.1)
            s.acceptor_process.join(.1)
            s.proposer_process.terminate()
            s.proposer_process.join(.1)


if __name__ == '__main__':
    unittest.main()
