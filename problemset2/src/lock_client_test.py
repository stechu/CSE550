#!/usr/bin/python

#########################################################################
# lock_client_test.py
#
# Unit test for lock client
#########################################################################

import lock_client
import sys
import os
import unittest
import command
import pickle
import socket
import subprocess
import time

class lock_client_test(unittest.TestCase):
    def setUp(self):
        # instantiate a client
        self.client = lock_client.lock_client()

    # Tests if connecting to the server works and that loopback works appropriately
    def test_client_connection_loopback(self):
        # start up the test loopback server
        subprocess.Popen(["python", "loopback_server.py", "1"])

        # allow the server to initialize
        time.sleep(5)
#        os.system("python loopback_server.py 1")

        print "[Lock Client Test] Launched server..."

        # connect to the initialized server
        self.client.connect_to_server('localhost', 9000)

        print "[Lock Client Test] Client connected to server..."
        
        # Client sends a command to server
        cmd_obj = ["lock", 45]
        self.client.send_command(cmd_obj)

        print "[Lock Client Test] Client issued command to server..."

        # Client receives loopback data from server
        recv_data = self.client.receive_command()

        print "[Lock Client Test] Client received loopback data from server..."

        # Deserialize the data
        recv_cmd = loads(recv_data)

        # Validate the same object came back
        assertTrue(recv_cmd[0] == "lock")
        assertTrue(recv_cmd[1] == 45)

        print "[Lock Client Test] Validated returned data..."

if __name__ == '__main__':
    unittest.main()
