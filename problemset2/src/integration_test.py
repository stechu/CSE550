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
import lock_file
import client
from lock_file import make_lock_file

class integration_test(unittest.TestCase):

    ###############################################################
    # Bring up a full Paxos group with multiple server instances
    ###############################################################

    def setUp(self):

        # set test server size
        self.TOTAL_SERVERS = 3

        # initialize server list
        self.server_list = []

        # generate the host numbers and ports of server connections
        for i in range(9000, 9000 + 2 * self.TOTAL_SERVERS, 2):
            server_entry = dict()

            server_entry["host"] = "localhost"
            server_entry["internal_port"] = i + 1
            server_entry["client_port"] = i

            self.server_list.append(server_entry)

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
            assert(s != None)
            self.servers[i].initialize_paxos()

    ###############################################################
    # Test to see if the Paxos server group shutsdown correctly
    ###############################################################

    def test_bring_up(self):
   
        print "\n[Info] ##########[INTEGRATION TEST SERVER BRING UP TEST]########## \n\n"

        # assert processes are running
        for s in self.servers:
            assert(s.listening_process.is_alive())
            assert(s.proposer_process.is_alive())
            assert(s.acceptor_process.is_alive())
        pass

    ###############################################################
    # Test to see if the client correctly can connect issue
    #  messages, and sign off
    ###############################################################
    
    def test_single_client_single_server(self):

        print "\n[Info] ##########[INTEGRATION TEST SINGLE CLIENT TEST]########## \n\n"

        # generate a lock file
        CMD_FILE = "client_0.txt"
        LOCKS = 3
        make_lock_file(LOCKS, CMD_FILE)

        # connect to the first server in the list
        port = self.server_list[0]["client_port"]
        host = self.server_list[0]["host"]
        assert((int(port) % 2) == 0)

        # initialize a client
        cli = client.client(CMD_FILE, 'localhost', port, 0)

        # wait for the client process to join
        try:
            cli.c_process.join()
        except Exception, e:
            cli.c_process.terminate()
            assert(False)

    ###############################################################
    # Test to see if multiple client connected to the same server
    #  connect and sign off correctly
    ###############################################################

    def test_multi_client_single_server(self):

        print "\n[Info] ##########[INTEGRATION TEST MULTI CLIENT SINGLE SERVER TEST]########## \n\n"

        # generate a lock file for each client
        CMD_FILES = ["client_0.txt", "client_1.txt"]
        LOCKS = 3
        make_lock_file(LOCKS, CMD_FILES[0])
        make_lock_file(LOCKS, CMD_FILES[1])

        # connect to the first server in the list only
        # connect to the first server in the list
        port = self.server_list[0]["client_port"]
        host = self.server_list[0]["host"]
        assert((int(port) % 2) == 0)

        # initialize the clients
        cli0 = client.client(CMD_FILES[0], 'localhost', port - 1, 0)
        cli1 = client.client(CMD_FILES[1], 'localhost', port - 1, 0)

        failed = False
        try:
            cli0.c_process.join()
            cli1.c_process.join()
        except Exception, e:
            cli0.c_process.terminate()
            cli1.c_process.terminate()
            failed = True

        assert(not failed)

    ###############################################################
    # Test to see if multiple clients connect request and sign
    #  off correctly
    ###############################################################

    def test_multi_client_multi_server(self):

        print "\n[Info] ##########[INTEGRATION TEST MULTIPLE CLIENT MULTIPLE SERVER TEST]########## \n\n"

        LOCKS = 3

        # generate the lock files
        for i in range(0, len(self.server_list)):
            filename = "client_" + str(i) + ".txt"
            make_lock_file(LOCKS, filename)

        # instantiate a client to each server
        client_list = []
        for i in range(0, len(self.server_list)):
            port = self.server_list[i]["client_port"]
            host = self.server_list[i]["host"]
            assert((int(port) % 2) == 0)

            cli = client.client("client_" + str(i) + ".txt", host, port, len(client_list))
            client_list.append(cli)

        # join each client
        failed = False
        for c in client_list:
            try:
                c.c_process.join()
            except Exception, e:
                c.terminate()
                failed = True

        assert(not failed)

    ###############################################################
    # Lock contention test
    ###############################################################

    def test_lock_contention(self):
        
        print "\n[Info] ##########[INTEGRATION TEST MULTIPLE CLIENT MULTIPLE SERVER TEST]########## \n\n"
        
        # generate a contentious lock file
        f = open("contention_test.txt", "w+")
        for i in range(0, 5):
            f.write("lock 1\n")
            f.write("unlock 1\n")
        f.close()
        
        # instantiate each client with a copy of the contentious lock file
        client_list = []
        for i in range(0, len(self.server_list)):
            port = self.server_list[i]["client_port"]
            host = self.server_list[i]["host"]
            assert((int(port) % 2) == 0)

            cli = client.client("contentious_test.txt", host, port, len(client_list))
            client_list.append(cli)

        # join each client
        failed = False
        for c in client_list:
            try:
                c.c_process.join()
            except Exception, e:
                c.terminate()
                failed = True

        assert(not failed)
        
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
