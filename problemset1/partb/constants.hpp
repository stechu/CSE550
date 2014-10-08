//###############################################################################
// constants.hpp
//
// Holds configuration constants for server550
//#############################################################################

#ifndef CONSTANTS_HPP
#define CONSTANTS_HPP


///////////////////////////////////////////////////////////////////////////////
//
// Server Settings
//
///////////////////////////////////////////////////////////////////////////////
#define THREAD_POOL_SIZE 4
#define IP_FIELD_DELIMITER "."
#define IP_FIELDS 4
#define MAX_PORT 65535


static const int BACK_LOG_SIZE = 16;
static const char * SERVER_IP = "127.0.0.1";
static const char * SERVER_PORT = "9000";
static const int MAX_CONNECTIONS = 10;
static const char * RESOURCE_PATH = "./testdata";

///////////////////////////////////////////////////////////////////////////////
//
// Client Settings
//
///////////////////////////////////////////////////////////////////////////////
static const int MAX_DATA_SIZE = 100;
static const int REQUEST_TIMES = 10;

#endif  // CONSTANTS_HPP
