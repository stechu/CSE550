#!/usr/bin/python

#########################################################################
# failure_test.py
#########################################################################

import server
import unittest
import time
import message
from lock_file import *
import client


class msg_failure_test(unittest.TestCase):

    ###############################################################
    # Bring up a full Paxos group with multiple server instances
    ###############################################################

    def setUp(self):
        pass

    ###############################################################
    # Test Functionality at 50% Message Drop Rate
    ###############################################################

    def test_message_drops(self):

        print "\n\n##########[MESSAGE DROP TEST]##########\n\n"

        # set test server size
        self.TOTAL_SERVERS = 5
        self.client_files = None

        # initialize server list
        self.server_list = []

        # generate the host numbers and ports of server connections
        for i in range(9000, 9000 + 2 * self.TOTAL_SERVERS, 2):
            server_entry = dict()

            server_entry["host"] = "localhost"
            server_entry["internal_port"] = i + 1
            server_entry["client_port"] = i
            server_entry["drop_rate"] = 0.25

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
            time.sleep(.5)  # allow the system to recover

        LOCKS = 100

        # generate the lock files
        for i in range(0, len(self.server_list)):
            filename = "client_" + str(i) + ".txt"
            make_simple_file(LOCKS, filename)

        client_files = []

        # instantiate a client to each server
        client_list = []
        for i in range(0, len(self.server_list)):
            port = self.server_list[i]["client_port"]
            host = self.server_list[i]["host"]
            assert((int(port) % 2) == 0)

            cli = client.client(
                "client_" + str(i) + ".txt", host, port, len(client_list))
            client_list.append(cli)
            client_list.append(cli)
            client_files.append("client_" + str(i) + ".txt")

        self.client_files = client_files

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
    # Test Functionality at 50% Message Duplication Rate
    ###############################################################

    def test_message_duplication(self):

        print "\n\n##########[MESSAGE DUUPLICATION TEST]##########\n\n"

        # set test server size
        self.TOTAL_SERVERS = 5

        # initialize server list
        self.server_list = []

        self.client_files = []

        # generate the host numbers and ports of server connections
        for i in range(9000, 9000 + 2 * self.TOTAL_SERVERS, 2):
            server_entry = dict()

            server_entry["host"] = "localhost"
            server_entry["internal_port"] = i + 1
            server_entry["client_port"] = i
            server_entry["dup_rate"] = 0.5

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
            time.sleep(.5) # allow the system to recover

        LOCKS = 100

        # generate the lock files
        for i in range(0, len(self.server_list)):
            filename = "client_" + str(i) + ".txt"
            make_simple_file(LOCKS, filename)

        # instantiate a client to each server
        client_list = []
        client_files = []
        for i in range(0, len(self.server_list)):
            port = self.server_list[i]["client_port"]
            host = self.server_list[i]["host"]
            assert((int(port) % 2) == 0)

            cli = client.client(
                "client_" + str(i) + ".txt", host, port, len(client_list))
            client_list.append(cli)
            client_list.append(cli)
            client_list.append(cli)
            client_files.append("client_" + str(i) + ".txt")

        self.client_files = client_files

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
            s.listening_process.join(5)
            s.acceptor_process.join(5)
            s.proposer_process.join(5)

        # perform a validation over the files
        for s in self.servers:
            assert(validate_lock_file("server" + str(s.server_id) + ".txt"))

        # check that the correct distributino of lcoks appeared in the log files
        client_files = self.client_files
        server_files = []
        for s in self.servers:
            server_files.append("server" + str(s.server_id) + ".txt")
        assert(len(server_files) == len(self.servers))

        if (self.client_files != None):
            validate_client_file(self.client_files, server_files)
        else:
            print "Warning: skipping client and server log cross validation..."

if __name__ == '__main__':
    unittest.main()
