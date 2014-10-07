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
#include "utilities.hpp"


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


// serving web pages in blocking mode
// return - 0 if success
int blocking_serv(const int socket_fd, int & request_id, 
  std::map<int, std::pair<int, std::string> > & requests){
  
  // some variables
  struct sockaddr_storage their_addr;
  socklen_t addr_size = sizeof their_addr;
  char s[INET6_ADDRSTRLEN];

  // main accept loop
  while(request_id<MAX_CONNECTIONS){
    // accept an connection
    int new_fd = accept(socket_fd, (struct sockaddr *) & their_addr, &addr_size);
    if(new_fd == -1){
      perror("[WARN] unable to accept.");
      continue;
    }

    // log the requesting ip
    inet_ntop(their_addr.ss_family,
      get_in_addr((struct sockaddr *)&their_addr),
      s,
      sizeof s);
    fprintf(stdout, "[DEBUG] Server: got connection from %s, \n", s);

    // for now, send hello world
    if (send(new_fd, "Hello, world!", 13, 0) == -1){
        perror("[WARN] send error.");
    }
    close(new_fd);
  
    //TODO: Validate filepath request

    //TODO: Offload file I/O to worker thread

    //TODO: On SIGINT or SIGTERM join running threads
    
    //TODO: If running threads fail to terminate, kill them
  
  }
  return 0;
}

// serving web pages in non-blocking mode
int async_serv(const int socket_fd, int & request_id, 
  std::map<int, std::pair<int, std::string> > & requests){
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
  int page_num = reload_resources(resources);
  if(page_num == 0){
    perror("[ERROR] serving folder does not contain any file. \n");
    exit(EXIT_FAILURE);
  } else {
    fprintf(stdout, "[INFO] serving %d pages. \n", page_num);
  }

  //event based connection handling
  int request_id = 0;                    //unique identifier for each request
  std::map<int, std::pair<int, std::string> > requests; //requests, key=request id, v=sock,url
  blocking_serv(server_socket, request_id, requests);
 

  //Destroy the thread pool
  pool.destroy();

  return 0;
}
