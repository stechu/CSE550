//####################################################################
// thread_pool_test.cc
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
  thread_pool t(THREAD_POOL_SIZE);

  //destroy the thread pool
  t.destroy();

  return 0;
}

int file_io_test()
{
  thread_pool t(THREAD_POOL_SIZE);

  //create a test file
  string TEST_FILE = "test_file.txt";
  ofstream test_file;
  test_file.open(TEST_FILE.c_str());
  
  string file_content = "Test string.\n\n";
  test_file << file_content;
  test_file.close();

  char * read_buffer = t.read_file((char *) TEST_FILE.c_str());

  t.destroy();
  
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
  thread_pool t(THREAD_POOL_SIZE);

  //neglect to create a file and try and read a bad one
  string TEST_FILE = "bad_file_handle.txt";
  char * read_buffer = t.read_file((char *) TEST_FILE.c_str());
  
  t.destroy();

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
  thread_pool t(THREAD_POOL_SIZE);

  int identifier = 1337;
  pair<int, string> request;
  request.first = identifier;
  request.second = TEST_FILE;

  //queue the task in the thread pool
  t.queue_task(request);
  
  //wait for a signal to come back
  t.lock_result_mutex();
  t.wait_for_result();

  //get the result from the queue
  pair<int, char*> result;
  result = t.dequeue_result();

  cout << "[Info] Dequeued resulting pair...\n";

  //unlock the mutex
  t.unlock_result_mutex();
  
  //verify the result is correct
  assert(result.first == request.first);
  assert(strcmp(result.second, (char *) file_content.c_str()) == 0);

  //clean up
  t.destroy();

  return 0;
}

int multi_file_test()
{
  thread_pool t(THREAD_POOL_SIZE);

  //test that the correct identifiers come back in the event of multiple duplicate test files
  string TEST_FILE_0 = "test_file_0.txt";
  string TEST_FILE_1 = "test_file_1.txt";
  
  ofstream test_file_0;
  ofstream test_file_1;
  
  string file_content_0 = "ABRACADABRA\n\n\t\n\t";
  string file_content_1 = "DU\nDUHDUHDU\nDU\nDU\nDUHDUHDU\nDU\n";

  test_file_0.open(TEST_FILE_0.c_str());
  test_file_1.open(TEST_FILE_1.c_str());

  test_file_0 << file_content_0;
  test_file_1 << file_content_1;

  test_file_0.close();
  test_file_1.close();

  //queue up some number of file requests mixed together
  vector<int> requests_0;
  vector<int> requests_1;

  int num_requests = 50;

  //enqueue all the requests
  for (int i = 0; i < num_requests; i++)
    {
      pair <int, string> request;
      request.first = i;
      if (i % 2 == 0)
	{
	  request.second = TEST_FILE_0;
	  requests_0.push_back(i);
	}
      else
	{
	  request.second = TEST_FILE_1;
	  requests_1.push_back(i);
	}
      t.queue_task(request);
    }

  //dequeue or wait for requests to finish processing
  pair <int, char *> result;

  for (int i = 0; i < num_requests; i++)
    { 
      t.lock_result_mutex();
      if (t.has_result())
	{
	  result = t.dequeue_result();
	}
      else
	{
	  //stimulate the threads
	  t.lock_task_mutex();
	  t.signal_task_queue();
	  t.unlock_task_mutex();

	  //wait for a result to come back
	  t.wait_for_result();
	  result = t.dequeue_result();
	}
      t.unlock_result_mutex();

      int identifier = result.first;
      if (identifier % 2 == 0)
	{
	  assert(strlen(result.second) > 0);
	  assert(strcmp(result.second, (char *) file_content_0.c_str()) == 0);
	}
      else
	{
	  assert(strlen(result.second) > 0);
	  assert(strcmp(result.second, (char *) file_content_1.c_str()) == 0);
	}
    }

  return 0;
}

int run_thread_pool_tests()
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

  try
    {
      result = multi_file_test();
      if (result != 0)
	cout << "[TEST] MULTI FILE TEST: FAILED\n";
      else
	cout << "[TEST] MULTI FILE TEST: PASSED\n";
    }
  catch (int e)
    {
      cout << "[TEST] MULTI FILE TEST: FAILED\n";
    }

  return 0;
}
