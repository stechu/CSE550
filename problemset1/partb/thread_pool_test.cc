//####################################################################
// thread_pool_tests.cc
//
// Test cases for the thread pool
//####################################################################

#include <stdio.h>
#include <string>
#include "constants.hpp"
#include "thread_pool.hpp"
#include <iostream>
#include <fstream>
#include <assert.h>
#include <stdlib.h>
#include <cstring>

using namespace std;

// basic bring up and shut down test
int basic_initialization_test()
{
  //initialize the thread pool
  initialize_thread_pool(THREAD_POOL_SIZE);

  //destroy the thread pool
  destroy_thread_pool();

  return 0;
}

int file_io_test()
{
  //create a test file
  string TEST_FILE = "test_file.txt";
  ofstream test_file;
  test_file.open(TEST_FILE.c_str());
  
  string file_content = "Test string.\n\n";
  test_file << file_content;
  test_file.close();

  char * read_buffer = read_file((char *) TEST_FILE.c_str());

  if (strcmp(read_buffer, (char *) file_content.c_str()) == 0)
    {
      return 0;
    }
  else
    {
      return -1;
    }
}

int bad_file_io_test()
{
  //neglect to create a file and try and read a bad one
  string TEST_FILE = "bad_file_handle.txt";
  char * read_buffer = read_file((char *) TEST_FILE.c_str());
  
  if (read_buffer == NULL)
    {
      return 0;
    }
  else
    {
      return -1;
    }
}

// fires a single file into the thread pool
int basic_file_test()
{
  //create a test file
  string TEST_FILE = "test_file.txt";
  ofstream test_file;
  test_file.open(TEST_FILE.c_str());
  
  string file_content = "Test string.\n";
  test_file << file_content;
  test_file.close();

  //start the thread pool
  initialize_thread_pool(THREAD_POOL_SIZE);

  int identifier = 1337;
  pair<int, string> request;
  request.first = identifier;
  request.second = TEST_FILE;

  //queue the task in the thread pool
  queue_task(request);
  
  //signal that a request made it to the task queue
  //pthread_cond_signal(&work_cond_var);

  //wait for a signal to come back
  pthread_mutex_lock(&result_queue_mutex);
  pthread_cond_wait(&result_cond_var, &result_queue_mutex);

  cout << "[Info] Got the signal, now attempting a dequeue of the result\n";

  //get the result from the queue
  pair<int, char*> result;
  result = dequeue_result();

  cout << "[Info] Dequeued resulting pair...\n";

  //unlock the mutex
  pthread_mutex_unlock(&result_queue_mutex);
  
  //verify the result is correct
  assert(result.first == request.first);
  assert(strcmp(result.second, (char *) file_content.c_str()) == 0);

  //clean up
  destroy_thread_pool();

  return 0;
}

int run_tests()
{
  int result = 0;
  try
    {
      result = basic_initialization_test();
      if (result != 0)
	cout << "[TEST] BASIC INITIALIZATION TEST: FAILED\n";
      else
	cout << "[TEST] BASIC INITIALIZATION TEST: PASSED\n";
    }
  catch (int e)
    {
      cout << "[TEST] BASIC INITIALIZATION TEST: FAILED\n";
    }

  cout << "\n";

  try
    {
      result = file_io_test();
      if (result != 0)
	cout << "[TEST] GOOD FILE I/O TEST: FAILED\n";
      else
	cout << "[TEST] GOOD FILE I/O TEST: PASSED\n";
    }
  catch (int e)
    {
      cout << "[TEST] GOOD FILE I/O TEST: FAILED";
    }

  cout << "\n";

  try
    {
      result = bad_file_io_test();
      if (result != 0)
	cout << "[TEST] BAD FILE I/O TEST: FAILED\n";
      else
	cout << "[TEST] BAD FILE I/O TEST: PASSED\n";
    }
  catch (int e)
    {
      cout << "[TEST] BAD FILE I/O TEST: FAILED";
    }

  cout << "\n";

  try
    {
      result = basic_file_test();
      if (result != 0)
	cout << "[TEST] BASIC FILE TEST: FAILED\n";
      else
	cout << "[TEST] BASIC FILE TEST: PASSED\n";
    }
  catch (int e)
    {
      cout << "[TEST] BASIC FILE TEST: FAILED\n";
    }

  return 0;
}
