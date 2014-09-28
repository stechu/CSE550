//#####################################################################################
// server.hpp
//
// File processing I/O functions for server
//#####################################################################################

using namespace std;

int initialize_server(string ip_address, int port);

int worker_thread(string filepath);

int initialize_thread_pool(int num_threads);
