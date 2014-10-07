//#####################################################################################
// server.cc
//
// File processing I/O functions for server
//#####################################################################################

#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include <queue>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
#include <netdb.h>
#include <iostream>
#include <map>
#include <unistd.h>
#include <errno.h>
#include <set>
#include <dirent.h>

#include "constants.hpp"
#include "thread_pool.hpp"
#include "server.hpp"


// reload resources
// return: number of files in resource folder
int reload_resources(std::set<std::string> & resources){
  struct dirent * de = NULL;
  DIR * d = NULL;

  resources.clear();

  d = opendir(RESOURCE_PATH);
  if (d == NULL){
    return -1;
  }

  while((de = readdir(d)) != NULL){
    std::string file_name (de->d_name);
    if(file_name == "." || file_name == ".."){
      continue;
    }
    resources.insert(file_name);
  }

  closedir(d);
  return resources.size();
}


// receive connections
int receive_connections(const int socket_fd, int & request_id, 
  std::map<int, std::pair<int, std::string> > & requests){
  
  struct sockaddr_storage their_addr;
  socklen_t addr_size = sizeof their_addr;
  
  while(request_id<MAX_CONNECTIONS){
    int new_fd = accept(socket_fd, (struct sockaddr *) & their_addr, &addr_size);
  }
  return 0;
}


//main thread execution call
int initialize_server(const char * ip_address, const char * port)
{
  
  //boilerplates
  int status;
  struct addrinfo hints, *servinfo, *p;
  socklen_t addr_size;
  struct sockaddr_in socket_addr;
  int yes = 1;
  int server_socket = -1;

  //Initialize the thread pool
  thread_pool pool(THREAD_POOL_SIZE);
  
  //Open a TCP listening connection
  // 1 - load up address structs
  // 2 - create a listening socket
  // 3 - bind socket
  // 4 - listen for connections
  // 5 - accept connections

  //load up address structs
  memset(&hints, 0, sizeof(hints));
  hints.ai_family = AF_INET;        // IPv4, we are old fashioned
  hints.ai_socktype = SOCK_STREAM;  // TCP
  hints.ai_flags = AI_PASSIVE;      // fill in my IP for me 

  if((status = getaddrinfo(NULL, port, &hints, &servinfo))!=0){
    fprintf(stderr, "getaddrinfo: %s \n", gai_strerror(status));
    exit(EXIT_FAILURE);
  }

  // loop through all the results and bind to the first we can
  for(p = servinfo; p != NULL; p = p->ai_next){
    // try to create a listening port
    if((server_socket = socket(servinfo->ai_family, servinfo->ai_socktype, servinfo->ai_protocol)) == -1){
      perror("[WARN] error at server:socket, try again.\n");
      continue;
    }

    // set socket option
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1){
      perror("[ERROR] error at setsocket, abort. \n");
      exit(EXIT_FAILURE);
    }

    //bind the socket
    if(bind(server_socket, p->ai_addr, p->ai_addrlen) == -1){
      close(server_socket);
      perror("[WARN] error at binding, try again.");
      continue;
    }

    break;
  }

  if (p == NULL){
    perror("[ERROR] server: fail to bind. \n");
    exit(EXIT_FAILURE);
  }

  freeaddrinfo(servinfo);

  //listening 
  if(listen(server_socket, BACK_LOG_SIZE) == -1){
    perror("[ERROR] Fail to listen, aborted.");
    exit(EXIT_FAILURE);
  } else {
    fprintf(stdout, "[INFO] begin to listen on %d \n", server_socket);
  }

  //load static resources
  std::set<std::string> resources;


  //event based connection handling
  int request_id = 0;                    //unique identifier for each request
  std::map<int, std::pair<int, std::string> > requests; //requests, key=request id, v=sock,url

  //Validate filepath request

  //Offload file I/O to worker thread

  //On SIGINT or SIGTERM join running threads

  //If running threads fail to terminate, kill them

  //Destroy the thread pool
  pool.destroy();

  return 0;
}
