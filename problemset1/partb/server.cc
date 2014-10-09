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

using namespace std;

#define EMPTY 0
#define INIT 1
#define RECV 2
#define PROC 3
#define SEND 4

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

  int pipe_fds[2];
  if (pipe2(pipe_fds, NULL) < 0)
    {
      cout << "Error: could not make pipe...\n";
      return 0;
    }

  //initialize the thread pool
  thread_pool tpool(THREAD_POOL_SIZE, pipe_fds[1]);

  // some variables
  struct sockaddr_storage their_addr;
  socklen_t addr_size = sizeof their_addr;
  char s[INET6_ADDRSTRLEN];
  char msg_buf[MAX_DATA_SIZE];
  int numbytes = -1;

  struct pollfd ufds[MAX_CONNECTIONS + 1];

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

  //add the read end of the self pipe
  ufds[MAX_CONNECTIONS].fd = pipe_fds[0];
  ufds[MAX_CONNECTIONS].events = POLLIN;
  ufds[MAX_CONNECTIONS].revents = 0;

  fcntl(pipe_fds[0], F_SETFL, O_NONBLOCK);

  vector<string> partial_filepaths(MAX_CONNECTIONS);

  vector< pair< int, pair<int, char*> > > partial_sends(MAX_CONNECTIONS);

  // loop for event handling
  while(true){
    int new_fd = -1;

    // poll
    poll(ufds, MAX_CONNECTIONS + 1, 100);

    int count = 0;
    
    // event handling
    for(int i = 0; i < MAX_CONNECTIONS + 1; i++){

      if ((i == MAX_CONNECTIONS) && (ufds[i].revents & POLLIN))
	{
	  cout << "Attempting to trigger self pipe\n";
	  char buf[5];
	  
	  int status = -1;
	  tpool.lock_self_pipe_mutex();
	  status = read(pipe_fds[0], buf, sizeof(buf));
	  tpool.unlock_self_pipe_mutex();

	  if (status < 0)
	    continue;
	  
	  cout << "Got signal: " << buf << "\n";

	
	  ufds[i].revents = 0;
	}

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
	  string temp("");
	  partial_filepaths[k] = temp;

	  //reset the events
	  ufds[i].revents = 0;
        }
      } 
      else if (states[i] == RECV) { // if this is active connection socket
        cout << "attempt a receive\n";

	if(ufds[i].revents & POLLIN){
	  count++;
	  int fd = ufds[i].fd; //get the file descriptor 
	  numbytes = recv(fd, msg_buf, MAX_DATA_SIZE - 1, 0);
		
	  if(numbytes == -1){
      	    cout << "State of revents " << (ufds[i].revents) << "\n";
      	    perror("[WARN] error on receiving request. \n");
      	    continue;
      	  }
	  
	  //append the partial file paths
	  for (int p = 0; p < numbytes; p++)
	    {
	      if (msg_buf[p] == '\n')
		{
		  cout << "State transition to PROC for " << i << " with filepath #" << partial_filepaths[i] << "#\n";
		  states[i] = PROC;

		  //queue the task into the thread pool
		  std::pair<int, std::string> task;
		  task.first = ufds[i].fd;
	    		  
	
		  task.second = partial_filepaths[i];

		  cout << "queued task: " << task.first << " " << task.second << "\n";

		  tpool.queue_task(task);
		  break;
		}
	      else
		{
		  partial_filepaths[i] += (char) msg_buf[p];
		}
	    }
	  ufds[i].revents = 0;
	}
      } //else if (states[i] == SEND && (ufds[i].revents & POLLIN))
      else if (states[i] == SEND)
	{
	  cout << "attempted a send for " << i << "\n";
	  
	  pair< int, pair< int, char* > > partial_send = partial_sends[i];

	  cout << "got the partial send value..\n";

	  int send_index = partial_send.first;
	  int fd = partial_send.second.first;
	  
	  char * buffer = partial_send.second.second;

	  char * send_ptr = buffer + send_index;

	  int sent_bytes = send(fd, send_ptr, sizeof(buffer) - send_index, 0);

	  if (sent_bytes < 0)
	    {
	      cout << "didnt send anything so need to trigger again\n";
	      tpool.lock_self_pipe_mutex();
	      write(pipe_fds[1], "a", 1);
	      tpool.unlock_self_pipe_mutex();
	      continue;
	    }
	  partial_send.first += sent_bytes;

	  //if all the bytes are sent kill this connction
	  if (partial_send.first >= sent_bytes)
	    {
	      close(fd);
	      states[i] = EMPTY;
	      ufds[i].fd = -1;
	      ufds[i].events = 0;
	      cout << "sent the data now closing the connection\n";
	    }
	  else
	    {
	      //not done sending so self pipe again
	      cout << "didnt send everything so need to trigger again\n";
	      tpool.lock_self_pipe_mutex();
	      write(pipe_fds[1], "a", 1);
	      tpool.unlock_self_pipe_mutex();
	    }
	  ufds[i].revents = 0;
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
    
    //get the results that are ready from the thread pool
    while (tpool.has_result())
    {
    	//dequeue the result from the queue
    	std::pair<int, char *> result;
    	result = tpool.dequeue_result();

	//get file descriptor
	int fd = result.first;
	int bytes_sent = sizeof(result.second);

	assert(result.first > 0);

	int state_index = -1;
	for (int y = 0; y < MAX_CONNECTIONS; y++)
	  {
	    if (ufds[y].fd == fd)
	      {
		state_index = y;
	       
		break;
	      }
	  }
	assert(state_index != -1);

	if (result.second == NULL)
	  {
	    close(fd);
	    ufds[state_index].fd = -1;
	    ufds[state_index].events = 0;
	    ufds[state_index].revents = 0;
	    states[state_index] = EMPTY;
	    continue;
	  }

	//if you get a NULL character

	pair<int, pair<int, char *> > partial_send;
	partial_send.first = 0;
	partial_send.second.first = result.first;
	partial_send.second.second = result.second;

	partial_sends[state_index] = partial_send;

	cout << "Set state for " << state_index << " to SEND for \n";
	states[state_index] = SEND;
    }

    tpool.unlock_result_mutex();
    
  }

  // Destroy the thread pool when done
  tpool.destroy();
  close(pipe_fds[0]);
  close(pipe_fds[1]);

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
