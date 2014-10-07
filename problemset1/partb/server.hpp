//#####################################################################################
// server.hpp
//
// File processing I/O functions for server
//#####################################################################################
#ifndef SERVER_HPP
#define SERVER_HPP

#include <set>
#include <iostream>


int initialize_server(const char * ip_address, const char * port);

int reload_resources(std::set<std::string> & resources);

#endif