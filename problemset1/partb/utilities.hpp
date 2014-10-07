//#############################################################################
// Utilities.hpp
//
// shared utilities methods
//#############################################################################
#ifndef UTILITIES_HPP
#define UTILITIES_HPP

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>


// get sockaddr, IPv4 or IPv6:
void * get_in_addr(struct sockaddr *sa);

#endif // UTILITIES_HPP
