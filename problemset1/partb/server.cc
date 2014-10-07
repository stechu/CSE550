//#####################################################################################
// server.cc
//
// File processing I/O functions for server
//#####################################################################################

#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include "server.hpp"
#include <queue>
#include "thread_pool.hpp"
#include <sys/socket.h>
#include <sys/types.h>
#include "constants.hpp"
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>

using namespace std;

//main thread execution call
int initialize_server(string ip_address, int port)
{
  //PSEUDOCODE
 
  //Initialize the thread pool
  thread_pool pool(THREAD_POOL_SIZE);
  
  //Open a TCP listening connection
  // - create socket
  // - bind socket
  // - listen for connections
  // - accept connections

  int server_socket = socket(AF_INET, SOCK_DGRAM, 0);
  if (server_socket == -1)
    return -1; //failed to create socket

  struct sockaddr_in socket_addr;

  // initialize some awful socket address data structure
  memset(&socket_addr, 0, sizeof(struct sockaddr_in));
  socket_addr.sin_family = AF_INET;
  socket_addr.sin_port = port;
  socket_addr.sin_addr.s_addr = inet_addr(ip_address.c_str());

  bind(server_socket, (struct sockaddr *) &socket_addr, sizeof(sockaddr_in));
 
  //Loop for connections until server is terminated

  //Validate filepath request

  //Offload file I/O to worker thread

  //On SIGINT or SIGTERM join running threads

  //If running threads fail to terminate, kill them

  //Destroy the thread pool
  pool.destroy_thread_pool();

  return 0;
}
