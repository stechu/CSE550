//#####################################################################################
// server.cc
//
// File processing I/O functions for server
//#####################################################################################

#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include <server.hpp>

using namespace std;

//main thread execution call
int initialize_server(string ip_address, int port)
{
  //PSEUDOCODE
 
  //Initialize the thread pool

  //Open a TCP listening connection
 
  //Loop for connections until server is terminated

  //Validate filepath request

  //Offload file I/O to worker thread

  //On SIGINT or SIGTERM join running threads

  //If running threads fail to terminate, kill them

  //Destroy the thread pool

  return 0;
}

//worker thread
// - takes a file path and reads it into process memory
int worker_thread(string filepath)
{

  return 0;
}

//thread pool initialization call
int initialize_thread_pool(int num_threads)
{

  return 0;
}
