#!/usr/bin/python

#########################################################################
# Launches a test server which opens a connection and echos back results
# - opens a connection
# - listens for connections
# - echos received messages
#########################################################################

import socket
import sys
import os

NUM_CONNECTIONS = -1

# if the number of connections is supported server will terminate
#  after receiving specified number of connections
# otherwise server runs indefinitely
if (len(sys.argv) == 2):
    NUM_CONNECTIONS = int(sys.argv[1])

SERVER_HOSTNAME = 'localhost'
SERVER_PORT = 9000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_HOSTNAME, SERVER_PORT))
server_socket.listen(10)

print "[Loopback Server] Initialized loopback server..."

index = 0

while (index < NUM_CONNECTIONS or (NUM_CONNECTIONS == -1)):
    print "[Loopback Server] Awaiting connections to server..."

    (connection_socket, connection_address) = server_socket.accept()

    print "[Loopback Server] Accepted a connection..."

    # loopback the data
    recv_data = connection_socket.recv(1024)
    connection_socket.send(recv_data)

    print "[Loopback Server] Sent back data..."

    connection_socket.close()

    index = index + 1

server_socket.close()

print "[Loopback Server] Terminated loopback server..."
