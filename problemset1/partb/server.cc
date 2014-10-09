//#####################################################################################
// server.cc
//
// File processing I/O functions for server
//#####################################################################################

// C headers
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <dirent.h>
#include <signal.h>
#include <sys/poll.h>
#include <sys/fcntl.h>

// CPP headers
#include <string>
#include <vector>
#include <queue>
#include <iostream>
#include <map>
#include <set>
#include <utility>
#include <cassert>
#include <iostream>

// local headers
#include "constants.hpp"
#include "thread_pool.hpp"
#include "server.hpp"
#include "utilities.hpp"
#include "bimap.hpp"

using namespace std;

#define EMPTY 0
#define INIT 1
#define RECV 2
#define PROC 3

// SIGCHLD handler
static void sigchld_hdl(int sig){
  // Wait for all dead processes.
  // We use a non-blocking call to be sure this signal handler will not
  // block if a child was cleaned up in another part of the program.
  while (waitpid(-1, NULL, WNOHANG) > 0) {
  }
}

// extract url from request
std::string extract_url(const std::string request) {
  for (size_t i = 0; i < request.size(); i++) {
    if (request[i] == '\n') {
      return request.substr(0, i);
    }
  }
  return request;
}


// serving web pages in blocking mode, a toy example
// return - 0 if success
int blocking_serv(const int socket_fd, int & request_id,
  std::map<int, std::pair<int, std::string> > & requests) {
  // some variables
  struct sockaddr_storage their_addr;
  socklen_t addr_size = sizeof their_addr;
  char s[INET6_ADDRSTRLEN];
  char msg_buf[MAX_DATA_SIZE];
  int numbytes = -1;

  // main accept loop
  while (request_id < MAX_CONNECTIONS) {
    // 1. accept an connection
    int new_fd = accept(socket_fd,
                        (struct sockaddr *) & their_addr,
                        &addr_size);
    if (new_fd == -1) {
      perror("[WARN] unable to accept.");
      continue;
    }

    // 2. log the requesting ip
    inet_ntop(their_addr.ss_family,
      get_in_addr((struct sockaddr *)&their_addr),
      s,
      sizeof s);
    fprintf(stderr, "[DEBUG] Server: get connection from %s, \n", s);

    // 3. receive the request
    if ((numbytes = recv(new_fd, msg_buf, MAX_DATA_SIZE - 1, 0)) == -1) {
      perror("[ERROR] error when receiving client request.");
      exit(EXIT_FAILURE);
    }
    msg_buf[numbytes] = '\0';
    fprintf(stderr, "[DEBUG] Server: receiving %s. \n", msg_buf);

    // 4. send back requested page
    if (send(new_fd, "Hello, world!", 13, 0) == -1) {
        perror("[WARN] send error.");
    }
    close(new_fd);
  }
  return 0;
}



// serving web pages in non-blocking mode
int async_serv(const int socket_fd,
               int & request_id) {
  cout << "server listening socket: " << socket_fd << "\n";

  //initialize the thread pool
  thread_pool tpool(THREAD_POOL_SIZE, 0);

  // some variables
  struct sockaddr_storage their_addr;
  socklen_t addr_size = sizeof their_addr;
  char s[INET6_ADDRSTRLEN];
  char msg_buf[MAX_DATA_SIZE];
  int numbytes = -1;

  struct pollfd ufds[MAX_CONNECTIONS];

  // listening socket is ufds[0]
  ufds[0].fd = socket_fd;
  ufds[0].events = POLLIN;

  int states[MAX_CONNECTIONS]; 
  memset(states, 0, sizeof(int) * MAX_CONNECTIONS);

  // make the socket non-blocking
  fcntl(socket_fd, F_SETFL, O_NONBLOCK);

  bool active_connections[MAX_CONNECTIONS]; //holds a bit indicating if the connection is active
  int ufds_socket[MAX_CONNECTIONS]; //holds the socket number for the ufds socket

  for (int i = 0; i < MAX_CONNECTIONS; i++)
    {
      active_connections[i] = false;
      ufds_socket[i] = -1;
    }

  // loop for event handling
  while(true){
    int new_fd = -1;

    // poll
    poll(ufds, MAX_CONNECTIONS, 100);

    int count = 0;
    
    // event handling
    for(int i = 0; i < MAX_CONNECTIONS; i++){
      if (i == 0) { // if this is the listening socket
        if(ufds[0].revents & POLLIN){ // if the collection is available 
          count++;
	        cout << "Number of connection events: " << count << "\n";

	        // get the new socket descriptor
          new_fd = accept(socket_fd,
                          (struct sockaddr *) & their_addr,
                          &addr_size);
          if (new_fd == -1) {
            //stab
            perror("[WARN] fail to accept. \n");
            continue;
          }
          if(fcntl(new_fd, F_SETFL, O_NONBLOCK) == -1){
            perror("[WARN] fail to fcntl. \n");
            continue;
          };

	        cout << "Acepted connection on server...\n";
          
          //find the correct place
          int k = 2;
          while(k < MAX_CONNECTIONS){
            if(states[k] == EMPTY){
              break;
            }
            k++;
          }

          if(k == MAX_CONNECTIONS){
            perror("exceed maximum connections. \n");
            exit(EXIT_FAILURE);
          }
          ufds[k].fd = new_fd;
          ufds[k].events = POLLIN;
          states[k] = INIT;
	        cout << "Set state of index " << k << " to " << states[k] << "\n";
        }
      } else if (states[i] == RECV) { // if this is active connection socket
        if(ufds[i].revents & POLLIN){
	        count++;
	        int fd = ufds[i].fd; //get the file descriptor 
	        numbytes = recv(fd, msg_buf, MAX_DATA_SIZE - 1, 0);

      	  if(numbytes == -1){
      	    cout << "State of revents " << (ufds[i].revents) << "\n";
      	    perror("[WARN] error on receiving request. \n");
      	    continue;
      	  }
      	  msg_buf[numbytes] = '\0';
      	  std::string url(msg_buf);
      	  url = extract_url(url);

          //change the state
          states[i] = PROC;
      	  
      	  //queue the task into the thread pool
      	  std::pair<int, std::string> task;
      	  task.first = ufds[i].fd;
      	  task.second = url;
      	  tpool.queue_task(task);
	      }
      }
    }
  

    // state transition
    for (int i = 1; i < MAX_CONNECTIONS; ++i)
      {
      	//cout << "State of index " << i << " = " << states[i] << "\n";
      	if(states[i] == INIT){
      	  states[i] = RECV;
      	  cout << "Transitioned connection " << i << " to state RECV\n";
      	}
      }
    
    //get the result data from the queue while results are available
    tpool.lock_result_mutex();
    
    while (tpool.has_result())
    {
    	//dequeue the result from the queue
    	std::pair<int, char *> result;
    	result = tpool.dequeue_result();

	//get file descriptor
	int fd = result.first;
	int bytes_sent;

	//call the Beej's programming guide function to send the bytes
	sendall(fd, result.second, &bytes_sent);

	//	assert(sizeof(result.second) == bytes_sent);

	//close out the connection and remove it
	close(fd);

  // remove fd
  int si = 0;
	while(si < MAX_CONNECTIONS)
  {
    if(ufds[si].fd == fd){
      break;
    }
    si++;
  }

  if(si == MAX_CONNECTIONS){
    perror("fucked");
    exit(EXIT_FAILURE);
  }

  ufds[si].fd = -1;
  ufds[si].events = 0;
  states[si] = EMPTY;

    }
    tpool.unlock_result_mutex();
    
  }

  // Destroy the thread pool when done
  tpool.destroy();

  return 0;
}

// main thread execution call
int initialize_server(const char * ip_address, const char * port) {
  // boilerplates
  int status;
  struct addrinfo hints, *servinfo, *p;
  socklen_t addr_size;
  struct sockaddr_in socket_addr;
  int yes = 1;
  int server_socket = -1;
  struct sigaction childact, pipeact;

  // Handle signals properly
  // 1 - SIGCHLD, reap zombie child process (if any)
  // 2 - SIGPIPE, ignore it
  // 3 - SIGINT or SIGTERM, a clean shutdown

  // Handle SIGCHLD
  memset(&childact, 0, sizeof(childact));
  childact.sa_handler = sigchld_hdl;
  if (sigaction(SIGCHLD, &childact, 0)) {
    perror("[ERROR] error on create SIGCHLD hanlder.");
    exit(EXIT_FAILURE);
  }

  // Handle SIGPIPE
  memset(&pipeact, 0, sizeof(pipeact));
  pipeact.sa_handler = SIG_IGN;
  pipeact.sa_flags = 0;
  if (sigaction(SIGPIPE, &pipeact, 0) == -1) {
    perror("[ERROR] error on create SIGPIPE handler");
    exit(EXIT_FAILURE);
  }

  // TODO: handle SIGINT and SIGTERM, a clean shutdown

  // Initialize the thread pool
  // thread_pool pool(THREAD_POOL_SIZE);

  // Open a TCP listening connection
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

  if ((status = getaddrinfo(NULL, port, &hints, &servinfo))!=0) {
    fprintf(stderr, "getaddrinfo: %s \n", gai_strerror(status));
    exit(EXIT_FAILURE);
  }


  // loop through all the results and bind to the first we can
  for (p = servinfo; p != NULL; p = p->ai_next) {
    // try to create a listening port
    if ((server_socket = socket(servinfo->ai_family, servinfo->ai_socktype, servinfo->ai_protocol)) == -1) {
      perror("[WARN] error at server:socket, try again.\n");
      continue;
    }

    // set socket option
    if (setsockopt(
      server_socket, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes)) == -1) {
      perror("[ERROR] error at setsocket, abort. \n");
      exit(EXIT_FAILURE);
    }

    // bind the socket
    if (bind(server_socket, p->ai_addr, p->ai_addrlen) == -1) {
      close(server_socket);
      perror("[WARN] error at binding, try again.");
      continue;
    }

    break;
  }

  if (p == NULL) {
    perror("[ERROR] server: fail to bind. \n");
    exit(EXIT_FAILURE);
  }

  freeaddrinfo(servinfo);

  // listening
  if (listen(server_socket, BACK_LOG_SIZE) == -1) {
    perror("[ERROR] Fail to listen, aborted.");
    exit(EXIT_FAILURE);
  } else {
    fprintf(stdout, "[INFO] begin to listen on %d \n", server_socket);
  }

  // event based connection handling
  int request_id = 0;                    // unique identifier for each request
  std::map<int, std::pair<int, std::string> > requests;   // requests
  //blocking_serv(server_socket, request_id, requests);
  async_serv(server_socket, request_id);

  return 0;
}
