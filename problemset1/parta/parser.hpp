//#################################################################
// parser.hpp
//
// Heade file for parser.cc
//#################################################################

using namespace std;

#include <string>
#include <vector>
#include <assert.h>

vector<string> parse_commands(string raw_input);
int fork_and_pipe_commands(vector<string> commands);
int child_process(string command, pid_t read_fd, pid_t write_fd);
