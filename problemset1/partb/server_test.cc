//#############################################################################
// Test cases for server.cc
//
//#############################################################################

#include <stdio.h>
#include <assert.h>
#include <string>
#include <iostream>

#include "constants.hpp"
#include "server.hpp"


using namespace std;

int load_resources_test(){
    set<string> resources;
    assert(reload_resources(resources) == 3);
    return 0;
}

int run_server_tests(){
    int result = -1;
    try {
      result = load_resources_test();
      if (result != 0)
            cout << "[TEST] LOAD RESOURCE TEST: FAILED\n";
      else
            cout << "[TEST] LOAD RESOURCE TEST: PASSED\n";
    } catch (int e)
    {
      cout << "[TEST] LOAD RESOURCE TEST: FAILED\n";
    }

    return 0;
}
