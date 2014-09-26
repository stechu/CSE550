//#################################################################
// main.cc
//
// Contains main to fire off shell prompt
//#################################################################

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <iostream>
#include "constants.hpp"
#include <vector>
#include <string>
#include "parser.hpp"

using namespace std;

int main(int argc, char * argv[])
{
  //argument validation
  assert(argc == 2);

  string raw_input = argv[1];

  //TEST HARNESS CODE

  cout << SHELL_PROMPT;
  cout << "Initializing console shell...\n";

  cout << "Received test input: " << raw_input << "\n";

  vector<string> commands = parse_commands(raw_input);

  //dump the command output for all to see
  for (int i = 0; i < (int) commands.size(); i++)
    {
      cout << commands[i] << "\n";      
    }

  //PSEUDOCODE FOR ACTUAL PARSING

  //TODO: display prompt

  //read line of input using system call

  //parse line for commands

  //check if EOF if found and note flag

  //fire off command processing
  fork_and_pipe_commands(commands);

  //repeat if EOF flag not found

  //display consolve terminate message

  return 0;
}
