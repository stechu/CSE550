#!/usr/bin/python

#########################################################################
# failure_test.py
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
from lock_file import *
import client

class failure_test(unittest.TestCase):

    ###############################################################
    # Bring up a full Paxos group with multiple server instances
    ###############################################################

    def setUp(self):

        # set test server size
        self.TOTAL_SERVERS = 5

        # initialize server list
        self.server_list = []

        # generate the host numbers and ports of server connections
        for i in range(9000, 9000 + 2 * self.TOTAL_SERVERS, 2):
            server_entry = dict()

            server_entry["host"] = "localhost"
            server_entry["internal_port"] = i + 1
            server_entry["client_port"] = i

            self.server_list.append(server_entry)

        print self.server_list

        # bring up each server
        self.servers = []

        # iterate through address list and instantiate servers
        for i in range(0, len(self.server_list)):
            # instantiate new servers
            new_server = server.PAXOS_member(i, self.server_list)
            self.servers.append(new_server)

        assert(len(self.servers) == len(self.server_list))
        assert(len(self.servers) == self.TOTAL_SERVERS)

        # initialize new servers
        for i in range(0, len(self.servers)):
            s = self.server_list[i]
            assert s
            self.servers[i].initialize_paxos()
            time.sleep(.5) # allow the system to recover

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
            s.listening_process.join(5)
            s.acceptor_process.join(5)
            s.proposer_process.join(5)

    ##########################################################
    # Test if Paxos group completes even with single node
    #  experiencing a failure
    # Do not attempt recovery
    ##########################################################

    def test_single_server_failure(self):

        print "\n[Info] ##########[INTEGRATION TEST MULTIPLE CLIENT MULTIPLE SERVER TEST]########## \n\n"

        LOCKS = 10

        kill_server = self.servers[0]

        # generate the lock files
        for i in range(0, len(self.server_list)):
            filename = "client_" + str(i) + ".txt"
            make_simple_file(LOCKS, filename)

        # instantiate a client to each server
        client_list = []
        for i in range(0, len(self.server_list)):
            port = self.server_list[i]["client_port"]
            host = self.server_list[i]["host"]
            assert((int(port) % 2) == 0)

            cli = client.client(
                "client_" + str(i) + ".txt", host, port, len(client_list))
            client_list.append(cli)

        time.sleep(1)

        # simulate a graceful server kill instead of a hard terminate
        exit_msg = message.message(message.MESSAGE_TYPE.EXIT,
                                   None, None, None, None, None, None)
#        kill_server.proposer_queue.put(exit_msg)
#        kill_server.acceptor_queue.put(exit_msg)

#        kill_server.proposer_process.join(1)
#        kill_server.acceptor_process.join(1)

        kill_server.proposer_process.terminate()
        kill_server.acceptor_process.terminate()
        kill_server.listening_process.terminate()
        try:
            kill_server.listening_process.join(1)
        except:
            pass

        # join each client
        failed = False
        for c in client_list:
            try:
                c.c_process.join()
            except Exception, e:
                c.terminate()
                failed = True

        assert(not failed)

    ##########################################################
    # Test if Paxos group completes even with slightly less 
    # than a majority of nodes experiencing a failure
    # Do not attempt recovery
    ##########################################################

    def test_multi_server_failure(self):
        
        # write a bunch of lock files
        client_list = []
        for i in range(0, len(self.server_list)):
            make_simple_file(100, "client_" + str(i) + ".txt")

        # start a bunch of clients
        for i in range(0, len(self.server_list)):
            host = self.server_list[i]["host"]
            port = self.server_list[i]["client_port"]
            assert((port % 2) == 0)
            new_client = client.client("client_" + str(i) + ".txt", host, port, i)

        # randomly kill the first set of servers until you've killed slightly less than a majority
        for i in range(0, int(len(self.servers)/2)):
            s = self.servers[i]
            s.listening_process.terminate()
            s.proposer_process.terminate()
            s.acceptor_process.terminate()
        
if __name__ == '__main__':
    unittest.main()
