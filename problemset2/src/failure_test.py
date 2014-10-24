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

        # do a manual clean up of the leftover sockets
        dump = os.popen("lsof -n -i | grep python").read()
        lines = dumps.split("\n")
        for line in lines:
            fields = line.split()
            pid = fields[1]
            os.system("kill " + pid)

        # a manual validation of this test is necessary due to the non-determinism of server failures

    ##########################################################
    # Test if Paxos group completes even with single node
    #  experiencing a failure
    # Do not attempt recovery
    ##########################################################

    def test_single_server_failure(self):

        print "\n[Info] ##########[INTEGRATION TEST MULTIPLE CLIENT MULTIPLE SERVER TEST]########## \n\n"

        LOCKS = 100

        kill_server = self.servers[random.randint(0, len(self.servers)-1)]

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

        # implement a hard terminate on each server
        kill_server.proposer_process.terminate()
        kill_server.acceptor_process.terminate()
        kill_server.listening_process.terminate()
        try:
            kill_server.listening_process.join(1)
        except:
            pass
        try:
            kill_server.acceptor_process.join(1)
        except:
            pass
        try:
            kill_server.proposer_process.join(1)
        except:
            pass

        self.servers.remove(kill_server)

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

        print "\n[Info] ##########[INTEGRATION TEST MULTIPLE CLIENT MULTIPLE SERVER TEST]########## \n\n"

        LOCKS = 100

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


        for i in range(0, len(self.server_list)/2  - 1 + (len(self.server_list) % 2)):
            kill_server = self.servers[i]
            kill_server.proposer_process.terminate()
            kill_server.acceptor_process.terminate()
            kill_server.listening_process.terminate()
            try:
                kill_server.listening_process.join(1)
                print "[Info] Terminated server " + str(i) + "..."
            except:
                pass
            self.server.remove(kill_server)

        # join each client
        failed = False
        for c in client_list:
            try:
                c.c_process.join()
            except Exception, e:
                c.terminate()
                failed = True

        assert(not failed)

if __name__ == '__main__':
    unittest.main()
