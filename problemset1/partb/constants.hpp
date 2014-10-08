//#####################################################################################
// constants.hpp
//
// Holds configuration constants for server550
//#####################################################################################

#ifndef CONSTANTS_HPP
#define CONSTANTS_HPP


///////////////////////////////////////////////////////////////////////////////
//
// Server Settings
//
///////////////////////////////////////////////////////////////////////////////
#define THREAD_POOL_SIZE 2
#define IP_FIELD_DELIMITER "."
#define IP_FIELDS 4
#define MAX_PORT 65535


const static int BACK_LOG_SIZE = 16;
const static char * SERVER_IP = "127.0.0.1";
const static char * SERVER_PORT = "9000";
const static int MAX_CONNECTIONS = 10;
const static char * RESOURCE_PATH = "./testdata";

///////////////////////////////////////////////////////////////////////////////
//
// Client Settings
//
///////////////////////////////////////////////////////////////////////////////
const static int MAX_DATA_SIZE = 100;

#endif // CONSTANTS_HPP