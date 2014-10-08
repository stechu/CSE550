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
#include <sys/wait.h>
#include <string.h>
#include <stdio.h>
#include <boost/algorithm/string.hpp>

using namespace std;

//hack up a trim function for whitespace
string trim(string input)
{
  int start_index = 0;
  int end_index = input.size();
  int count = 0;
  for (int i = 0; i < (int) input.size(); i++)
    {
      if (input[i] == ' ' || input[i] == '\t' || input[i] == '\n')
	count++;
      else
	break;
    }
  start_index = count;

  count = 0;
  for (int i = (int) (input.size() - 1); i >= 0; i--)
    {
      if (input[i] == ' ' || input[i] == '\t' || input[i] == '\n')
	count++;
      else
	break;
    }
  end_index = input.size() - count;
  assert(start_index <= end_index);
  return input.substr(start_index, end_index - start_index);
}

// vector<string> parse_commands(string raw_input)
// - takes the raw input and tokenizes the commands by the | delimiter
// - returns a vector of tokens
vector<string> parse_commands(string raw_input)
{
  vector<string> commands;

  //tokenize the commands

  char *tokenized_command;

  tokenized_command = strtok((char*) raw_input.c_str(), DELIMITERS);

  while (tokenized_command != NULL)
    {
      string tokenized_command_str(tokenized_command);
      commands.push_back(trim(tokenized_command_str));
      tokenized_command = strtok(NULL, DELIMITERS);
    }

  //TODO: trim leading whitespace if necessary

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

  //pipe fd is returned [read end, write end]
  vector< pair<int, int> > pipe_fd_pairs;
  for (int i = 0; i < num_pipes; i++)
  {
    int pipe_fds[2];
    int status = pipe(pipe_fds);
    if (status == -1) exit(-1);
    pair<int, int> fd_pair;
    fd_pair.first = pipe_fds[0];
    fd_pair.second = pipe_fds[1];

    //bookkeeping for the pipe fds
    pipe_fd_pairs.push_back(fd_pair);

#if (DEBUG)
    cout << "Created pipe " << i << " with fds " << fd_pair.second << " -> "<< fd_pair.first << "\n";
#endif
  }
  
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
	int read_fd;
	int write_fd;
	
	if (i == 0){
	  read_fd = -1; //pass a -1 to indicate no STDIN
	} 
	else 
	  {
	    pair<int, int> read_fd_pair = pipe_fd_pairs[i-1];
	    read_fd = read_fd_pair.first;
	  }
	
	//determine the write stream fd
	if (i < num_commands - 1)
	  {
	    pair <int, int> write_fd_pair = pipe_fd_pairs[i];
	    write_fd = write_fd_pair.second;
	  }
	else {
	  write_fd = STDOUT_FILENO;
	}
	
#if (DEBUG)
	cout << getpid() << ": spawned with command " << command << " with file descriptors: " << read_fd << " -> " << write_fd << "\n";
#endif
	
	//go through and kill all the unused pipe file descriptors
	for (int k = 0; k < num_pipes; k++)
	  {
	    pair<int, int> fd_pair = pipe_fd_pairs[k];
	    if (fd_pair.first != read_fd)
	      close(fd_pair.first);
	    if (fd_pair.second != write_fd)
	      close(fd_pair.second);
	  }
	
	//call the child process handler
	child_process(command, read_fd, write_fd);
	break;
      }
    else 
      {
#if (DEBUG)
      cout << "Fork succeeded with pid_t: " << child_pid << "\n";
#endif
      pids.push_back(child_pid);
    }
  }

  // if parent process - wait for any of the child pid_t's to finish executing - 
  // - must wait for pids.size() times since we spawned that many children
  if (!is_child)
  {
    //close the parent's pipes
    for (int i = 0; i < num_pipes; i++)
      {
	pair<int, int> fd = pipe_fd_pairs[i];
	close(fd.first);
	close(fd.second);
      }

    for (int j = 0; j < (int) pids.size(); j++)
      {
#if (DEBUG)
	cout << "Waiting for child process to die...\n";
#endif	

	int status = 0;
	
#if (DEBUG)
	pid_t exit_child_pid = waitpid(-1, &status, 0);
	cout << "Child with pid: " << exit_child_pid << " terminated...\n";
#else
	waitpid(-1, &status, 0);
#endif
      }
  }

  return 0;
}


// int child_process(string command, int read_fd, int write_fd)
// - redirects the stdin and stdout of the process appropratiately
// - executes the command
int child_process(string command, int read_fd, int write_fd)
{
  //drop some asserts here to verify the pipe stdin source
  assert(command.length() > 0);
  assert(read_fd >= -1);
  assert(write_fd >= 0);
  int status;

  //######################################################################
  // Set the read_fd and write_fd to appropriate stdin and stdou
  //######################################################################

  //redirect the STDIN for this process or close it
  if (read_fd == -1)
    close(STDIN_FILENO);
  else
  {
    //    status = dup2(read_fd, STDIN_FILENO);
    status = dup2(read_fd, STDIN_FILENO);
    if (status == -1)
      exit(-1);
  }
  
  //redirect the STDOUT for this process
  //status = dup2(write_fd, STDOUT_FILENO);
  status = dup2(write_fd, STDOUT_FILENO);
  if (status == -1)
    exit(-1);
  
  
  //######################################################################
  // Launch exec system call to fire off the program
  //######################################################################

  //initialize the execvp call argument array
  int ARGS = 2;
  char * argv[ARGS];
  string cmd_str = command;

  argv[0] = (char *) cmd_str.c_str(); //convention to point to file begin executed
  argv[1] = (char *) NULL; //null terminated array

  //launch exec command and nuke process image
  status = execvp(command.c_str(), argv);

  if (status == -1)
  {
    cout << "Error starting execvp command: " << command << "\n";
    exit(-1);
  }

  //this should never execute since execvp should wipe out the image
  assert(false);

  return 0;
}
