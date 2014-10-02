//#################################################################
// parser.hpp
//
// Heade file for parser.cc
//#################################################################

#include <string>
#include <vector>
#include <assert.h>

using namespace std;

vector<string> parse_commands(string raw_input);
int fork_and_pipe_commands(vector<string> commands);
int child_process(string command, pid_t read_fd, pid_t write_fd);
