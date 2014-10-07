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
#include <netdb.h>

using namespace std;

//main thread execution call
int initialize_server(const char * ip_address, const char * port)
{
  
  //boilerplates
  int status;
  struct addrinfo hints, *res, *p;
  socklen_t addr_size;
  struct sockaddr_in socket_addr;

  //Initialize the thread pool
  thread_pool pool(THREAD_POOL_SIZE);
  
  //Open a TCP listening connection
  // 1 - load up address structs
  // 2 - create a listening socket
  // 3 - bind socket
  // 4 - listen for connections
  // 5 - accept connections

  // load up address structs
  memset(&hints, 0, sizeof(hints));
  hints.ai_family = AF_INET;        // IPv4, we are old fashioned
  hints.ai_socktype = SOCK_STREAM;  // TCP
  hints.ai_flags = AI_PASSIVE;      // fill in my IP for me 

  if((status = getaddrinfo(NULL, port, &hints, &res))!=0){
    fprintf(stderr, "getaddrinfo: %s \n", gai_strerror(status));
    exit(EXIT_FAILURE);
  }

  // create a listening socket
  int server_socket = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
  if (server_socket == -1){
    perror("Cannot create socket, aborted.");
    exit(EXIT_FAILURE);
  }

  // bind socket
  if(bind(server_socket, res->ai_addr, res->ai_addrlen) == -1){
    perror("Cannot bind socket.");
    exit(EXIT_FAILURE);
  }

  //Loop for connections until server is terminated

  //Validate filepath request

  //Offload file I/O to worker thread

  //On SIGINT or SIGTERM join running threads

  //If running threads fail to terminate, kill them

  //Destroy the thread pool
  pool.destroy_thread_pool();

  //Free memory
  freeaddrinfo(res); 

  return 0;
}
