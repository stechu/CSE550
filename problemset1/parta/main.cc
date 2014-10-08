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
#include <readline/readline.h>
#include <readline/history.h>

using namespace std;

int main()
{
#if (DEBUG)
  cout << "Initializing econsole shell...\n";
#endif

  //main command line loop
  bool done = false;
  while (!done)
  {

      //read line of input using system call
      char * line = readline(SHELL_PROMPT);

      string cmds_line(line);

#if (DEBUG)
      cout<<"executing "<<cmds_line<<endl;
#endif      

      //if EOF is found NULL is returned
      if (line == NULL)
    	{
    	  cout << SHELL_PROMPT << " terminated.\n";
    	  done = true;
    	  
    	  free(line); //clean up the malloced readline
    	  break;
    	}
      else if (cmds_line.compare(EXIT_STRING) == 0)
    	{
    	  done = true;
    	  free(line); //clean up the malloced readline
    	  break;
    	}
      
      //parse line for commands
      vector<string> cmds = parse_commands(cmds_line);

#if (DEBUG)
      cout << "Commands parsed:\n";
      for (int i = 0; i < (int) cmds.size(); i++)
	{
	  cout << "<" << cmds[i] << ">" << "\n";
	}
#endif

      //fire off command processing
      fork_and_pipe_commands(cmds);

      //clean up the malloced readline
      free(line);
    }

  //display consolve terminate message
  cout << SHELL_PROMPT << " terminated.\n";

  return 0;
}
