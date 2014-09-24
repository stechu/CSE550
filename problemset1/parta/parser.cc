//#################################################################
// parser.cc
//
// Provides parsing functions for dealing with the command line
// input
//#################################################################

#include "parser.hpp"
#include "constants.hpp"
#include <iostream>
#include <unistd.h>
#include <stdlib.h>

using namespace std;

// vector<string> parse_commands(string raw_input)
// - takes the raw input and tokenizes the commands by the | delimiter
// - returns a vector of tokens
vector<string> parse_commands(string raw_input)
{
  vector<string> commands;

  int start_index = 0;

  //iterate through and tokenize the command
  //TODO: catch the edge case malformed command with pipe at the beginning
  for (int i = 0; i < (int) raw_input.length(); i++)
    {
      if (raw_input[i] == DELIMITER)
	{
	  assert(i - start_index > 0);
	  string token = raw_input.substr(start_index, i - start_index); //start index, length of string
	  commands.push_back(token);
	  start_index = i + 1;
	}
    }

  //add remaining tail end commands
  string last_token = raw_input.substr(start_index);
  commands.push_back(last_token);

  return commands;
}

// 
// - initializes the necessary pipes before forking the environment
// - forks the execution environment for the command
// - takes a vector<string> of commands to fork child processes for

int fork_and_pipe_commands(vector<string> commands)
{
  int num_commands = commands.size();
  int num_pipes = num_commands - 1;

  vector<pid_t> pids;

  //get the parent pid for comparison
  pid_t parent_pid = getpid();

  //###############################################
  // Pipe creation
  //###############################################
  
  vector<int *> pipe_fd_pairs;
  for (int i = 0; i < num_pipes; i++)
    {
      int fd_pair[2];

      int status = pipe(fd_pair);
      if (status == -1)
	exit(-1);

      //bookkeeping for the pipe fds
      pipe_fd_pairs.push_back(fd_pair);
    }

  //close the first read pipe end
  int * head_fds;
  head_fds = pipe_fd_pairs[0];
  close(head_fds[0]); //close the unused read pipe end
  
  //###############################################
  // Spawn Child Processes
  //###############################################

  bool is_child = false;
  for (int i = 0; i < num_commands; i++)
    {
      pid_t child_pid = fork();

      is_child = (parent_pid != getpid());

      //if child process set the stdio to appropriate pipes
      if (is_child)
	{
	  string command = commands[i];
	  
	  //determine the read stream fd
	  int * read_fd_pair = pipe_fd_pairs[i];
	  int read_fd;
	  int write_fd;

	  if (i == 0)
	    read_fd = NULL;
	  else
	    read_fd = read_fd_pair[1];

	  //determine the write stream fd
	  if (i < num_commands - 1)
	    {
	      int * write_fd_pair = pipe_fd_pairs[i+1];
	      write_fd = write_fd_pair[0];
	    }
	  else
	    {
	      write_fd = NULL;
	    }

	  //call the child process handler
	  child_process(command, read_fd, write_fd);

	  //TODO: figure out how to join the child process and wait until it happens
	  
	  break;
	}
      else
	{
	  pids.push_back(child_pid);
	}
    }

  return 0;
}

int child_process(string command, pid_t read_fd, pid_t write_fd)
{
  //drop some asserts here to verify the pipe stdin source

  //apply dup2 to associate stdin with read_fd and stdout with write_fd
  
  //read input until an EOF is found then executed the child process on the new command

  //TODO: call exec with the command for the child process

  //drop some asserts here to verify the pipe stdout destination

  return 0;
}
