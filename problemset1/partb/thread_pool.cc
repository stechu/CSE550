//###########################################################################################
// thread_pool.cc
//
// Definitions for thread pool object
//###########################################################################################

#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <queue>
#include <pthread.h>
#include "thread_pool.hpp"
#include <fstream>
#include <assert.h>
#include <iostream>
#include "thread_pool_test.hpp"
#include <sstream>

using namespace std;

vector<pthread_t> pthreads;              //bookkeeping to track the threads

//########################################################################
// thread pool initialization
// - threads are created and launched into worker thread function
// - bookkeeping so that threads can be cleaned up later on termination
//########################################################################
void initialize_thread_pool(int num_threads)
{
  exit_signal = false;

  pthread_mutex_init(&task_queue_mutex, NULL);
  pthread_mutex_init(&result_queue_mutex, NULL);
  pthread_mutex_init(&exit_mutex, NULL);

  if (pthread_cond_init(&work_cond_var, NULL) < 0)
    cout << "[Info] Failed to initialize work condition variable...\n";
  if(pthread_cond_init(&result_cond_var, NULL) < 0)
    cout << "[Info] Failed to initialize result condition variable...\n";
  
  //  cout << "[Debug] Thread pool mutex initialization: SUCCESS\n";

  pthread_mutex_lock(&exit_mutex);
  for (int i = 0; i < num_threads; i++)
    {
      pthread_t new_thread;
      pthread_create(&new_thread, NULL, worker_thread, (void *) i);

      pthreads.push_back(new_thread);
      //TODO: set the pthread stack, and memory parameter sizes
      
    }
  pthread_mutex_unlock(&exit_mutex);

  cout << "[Debug] Thread pool thread creation: SUCCESS\n";

}

//########################################################################
// adds a task to the task queue
// - argument is a pair containing [request identifier, filepath name]
// - SYNCHRONIZED CALL
//########################################################################
void queue_task(pair<int, string> s)
{
  pthread_mutex_lock(&task_queue_mutex);
  task_queue.push(s);
  pthread_cond_broadcast(&work_cond_var);      //signal the worker threads that more work has arrived
  pthread_mutex_unlock(&task_queue_mutex);
}

//########################################################################
// gets the task at the front of the queue
// - should only be called from the thread_pool
// - THIS IS NOT A PROTECTED REGION
// - MUTEX SHOULD BE ACQUIRED BY CONDITION VARIABLE CHECK
// - Throws an exception if not work is available
//########################################################################
pair<int, string> dequeue_task()
{
  //pthread_mutex_lock(&task_queue_mutex);
  pair<int, string> task;
  if (task_queue.size() == 0)
    throw 42; //throw an exception if the task_queue is empty
  else
    {
      task = task_queue.front();
      task_queue.pop();
    }
  //pthread_mutex_unlock(&task_queue_mutex);
  return task;
}

//########################################################################
// adds a worker result to the result queue
// - should only be called from the thread_pool
// - SYNCHRONIZED CALL
//########################################################################
void queue_result(pair<int, char*> s)
{
  pthread_mutex_lock(&result_queue_mutex);
  result_queue.push(s);
  pthread_cond_broadcast(&result_cond_var);
  cout << "Queue result has issued a broadcast\n";
  pthread_mutex_unlock(&result_queue_mutex);
}

//########################################################################
// removes a worker result from the queue
// - returns a pair containg [request identification, buffer pointer]
// - a NULL buffer pointer is returned if filepath does not exist
// - does not lock mutex, assumes caller holds mutex after signal
//########################################################################
pair<int, char *> dequeue_result()
{
  //  pthread_mutex_lock(&result_queue_mutex);
  pair<int, char*> result = result_queue.front();
  result_queue.pop();
  //pthread_mutex_unlock(&result_queue_mutex);
  return result;
}

//############################################################
// Main worker thread to handle the file I/Os
//############################################################
void * worker_thread(void * ptr)
{
  //enter main loop
  bool done = false;
  bool work_available = false; //hacked up flag that indicates if task is available
  pair<int, string> task;

  //  cout << "[Info] Thread creation successful...\n";

  while (!done)
    {

      //##########################################################
      // Handle the task dequeueing from the task queue
      //##########################################################

      //check if there is work to do
      pthread_mutex_lock(&task_queue_mutex);
      try
	{
	  task = dequeue_task();
	  work_available = true;
	  //TODO: put assertions here
	}
      catch (int e)
	{
	  work_available = false;
	}
      if (!work_available)
	{
	  pthread_cond_wait(&work_cond_var, &task_queue_mutex);
	  cout << "[Debug] Received a signal on the condition variable...\n";
	  cout << "Length of task queue: " << task_queue.size() << "\n";
	}
      pthread_mutex_unlock(&task_queue_mutex);

      //##########################################################
      // Handle file reading if the task is valid
      //##########################################################

      if (work_available == true)
	{
	  cout << "[Info] Got a filepath for reading: " << task.second << "\n";

	  char * char_buffer = read_file((char *) task.second.c_str());

	  pair<int, char*> result;
	  result.first = task.first;
	  result.second = char_buffer;

	  cout << "[Info] Queueing result: " << result.second << "\n";

	  //queue the result into the result queue
	  queue_result(result);
	  cout << "[Info] Result queue length: " << result_queue.size() << "\n";

	}

      //##########################################################
      // Check for termination conditions
      //##########################################################
      
      pthread_mutex_lock(&exit_mutex);
      if (exit_signal)
	done = true;
      pthread_mutex_unlock(&exit_mutex);
    }

  return 0;
}

char * read_file(char * filepath)
{
  //attempt to open the file
  ifstream read_file(filepath);

  //check if the file opens
  if (!read_file.is_open())
    {
      return NULL;
    }
  
  stringstream buffer_stream;
  buffer_stream << read_file.rdbuf();

  string buffer_string(buffer_stream.str());

  char * char_buffer = (char *) buffer_string.c_str();

  read_file.close();
  
  return char_buffer;
}

//########################################################################
// destroys the thread pool
// - allows threads to terminate before joining
// - signals threads the exit worker thread
// - releases mutexes and condition variables
//########################################################################
void destroy_thread_pool()
{
  //kill all of the active threads by setting the 
  pthread_mutex_lock(&exit_mutex);
  exit_signal = true;
  pthread_mutex_unlock(&exit_mutex);
  
  pthread_mutex_lock(&task_queue_mutex);
  pthread_cond_broadcast(&work_cond_var);
  pthread_mutex_unlock(&task_queue_mutex);

  for (int i = 0; i < (int) pthreads.size(); i++)
    {
      pthread_t target_thread = pthreads[i];
      pthread_join(target_thread, NULL);
      //      cout << "[Debug] Thread exited and joined\n";

      pthread_mutex_lock(&task_queue_mutex);
      pthread_cond_broadcast(&work_cond_var);
      pthread_mutex_unlock(&task_queue_mutex);
    }

  //  cout << "[Debug] Thread pool worker threads joined\n";

  //kill all of the active mutexes and condition variables
  pthread_mutex_destroy(&task_queue_mutex);
  pthread_mutex_destroy(&result_queue_mutex);
  pthread_mutex_destroy(&exit_mutex);

  pthread_cond_destroy(&work_cond_var);
  pthread_cond_destroy(&result_cond_var);

  cout << "[Debug] Thread pool destroyed mutexes and condition variables: SUCCESS\n";

  //TODO: free any allocated memory
}
