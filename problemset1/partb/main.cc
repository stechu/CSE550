//#####################################################################################
// main.cc
//
// Main entry method for server550
//#####################################################################################

#include <stdio.h>
#include <iostream>
#include <string.h>
#include <assert.h>
#include "constants.hpp"
#include <pthread.h>
#include <vector>
#include "server.hpp"
#include <stdlib.h>
#include "thread_pool_test.hpp"

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
  return input.substr(start_index, end_index);
}

int validate_ip(string ip_address)
{
  vector<string> ip_fields;
  char * tokenized_field;
  tokenized_field = strtok((char *) ip_address.c_str(), IP_FIELD_DELIMITER);
  while (tokenized_field != NULL)
    {
      string token(tokenized_field);
      ip_fields.push_back(trim(token));
      tokenized_field = strtok(NULL, IP_FIELD_DELIMITER);
    }

  if (ip_fields.size() != IP_FIELDS)
    return -1;

  for (int i = 0; i < IP_FIELDS; i++)
    {
      if (atoi(ip_fields[i].c_str()) < 0 || atoi(ip_fields[i].c_str()) >= 256)
	return -1;
    }
  return 0;
}

//#################################################################################
//main method
//#################################################################################
int main(int argc, char * argv[])
{
#if (TEST == 1)
  cout << "##################[INITIALIZING TEST CASES]#####################\n";

  run_tests();

#else

  //validate we got enough arguments
  if (argc != 3)
    {
      cout << "Fatal: server550 expects 2 arguments - <Server IP Address> <Server Port>\n";
      return -1;
    }

  string ip_address(argv[1]);
  string server_port(argv[2]);

  //validate arguments
  if (validate_ip(ip_address) != 0)
    return -1;
  if (atoi(server_port.c_str()) <= 0 || atoi(server_port.c_str()) > MAX_PORT)
    return -1;

  //call the server initialization function
  initialize_server(ip_address.c_str(), server_port.c_str());

  return 0;

#endif
}
