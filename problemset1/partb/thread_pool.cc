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
#include "server.hpp"
#include <fstream>
#include <assert.h>
#include <iostream>

using namespace std;

queue<string> task_queue;
queue< pair<string, char *> > result_queue;

vector<pthread_t> pthreads;

// thread pool initialization
// - threads are created and launched into worker thread function
// - bookkeeping so that threads can be cleaned up later on termination
void initialize_thread_pool(int num_threads)
{
  exit_signal = false;

  pthread_mutex_init(&task_queue_mutex, NULL);
  pthread_mutex_init(&result_queue_mutex, NULL);
  pthread_mutex_init(&exit_mutex, NULL);
  
  cout << "[Debug] Thread pool mutex initialization: SUCCESS\n";

  for (int i = 0; i < num_threads; i++)
    {
      pthread_t new_thread;
      pthread_create(&new_thread, NULL, worker_thread, (void *) i);

      pthreads.push_back(new_thread);
      //TODO: set the pthread stack, and memory parameter sizes
      
    }

  cout << "[Debug] Thread pool thread creation: SUCCESS\n";

}

//adds a task to the task queue
// SYNCHRONIZED CALL
void queue_task(string s)
{
  pthread_mutex_lock(&task_queue_mutex);
  task_queue.push(s);
  pthread_cond_signal(&work_cond_var);      //signal the worker threads that more work has arrived
  pthread_mutex_unlock(&task_queue_mutex);
}

// gets the task at the front of the queue
// THIS IS NOT A PROTECTED REGION
// MUTEX SHOULD BE ACQUIRED BY CONDITION VARIABLE CHECK
// Throws an exception if not work is available
string dequeue_task()
{
  //pthread_mutex_lock(&task_queue_mutex);
  string task;
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

//adds a worker result to the result queue
// SYNCHRONIZED CALL
void queue_result(pair<string, char*> s)
{
  pthread_mutex_lock(&result_queue_mutex);
  result_queue.push(s);
  pthread_mutex_unlock(&result_queue_mutex);
}

//removes a worker result from the queue
// SYNCHRONIZAED CALL
pair<string, char *> dequeue_result()
{
  pthread_mutex_lock(&result_queue_mutex);
  pair<string, char *> result = result_queue.front();
  result_queue.pop();
  pthread_mutex_unlock(&result_queue_mutex);
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
  string task;

  cout << "[Info] Thread creation successful...\n";

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
	  assert(!task.empty());
	}
      catch (int e)
	{
	  work_available = false;
	}

      pthread_mutex_unlock(&task_queue_mutex);

      //no work so do nothing and wait for condition variable to get a signal
      if (work_available == false) 
	{
	  pthread_mutex_lock(&task_queue_mutex);
	  pthread_cond_wait(&work_cond_var, &task_queue_mutex);
	  try
	    {
	      task = dequeue_task();
	      work_available = true;
	    }
	  catch (int e)
	    {
	      work_available = false;
	    }
	  pthread_mutex_unlock(&task_queue_mutex);
	}

      //##########################################################
      // Handle file reading if the task is valid
      //##########################################################

      if (work_available == true)
	{
	  assert(!task.empty());

	  //attempt to open the file
	  ifstream read_file(task.c_str(), ifstream::in);

	  char * char_buffer;

	  //if file opens successfully, append to string then get the char * pointer
	  if (read_file.is_open())
	    {
	      string buffer;
	      string line;
	      while (getline(read_file, line))
		{
		  buffer.append(line);
		}
	      char_buffer = (char *) buffer.c_str();
	      read_file.close();
	    }
	  //if the file fails to open, return a NULL pointer indicating a failure to the result queue
	  else
	    {
	      //NULL pointer returned in the event of a bad file path
	      char_buffer = NULL;
	    }

	  pair<string, char*> result;
	  result.first = task;
	  result.second = char_buffer;

	  //queue the result into the result queue
	  queue_result(result);
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

void destroy_thread_pool()
{
  //kill all of the active threads by setting the 
  pthread_mutex_lock(&exit_mutex);
  exit_signal = true;
  pthread_mutex_unlock(&exit_mutex);
  
  pthread_mutex_lock(&task_queue_mutex);
  pthread_cond_broadcast(&work_cond_var);
  pthread_mutex_unlock(&task_queue_mutex);

  for (int i = 0; i < pthreads.size(); i++)
    {
      pthread_t target_thread = pthreads[i];
      pthread_join(target_thread, NULL);
      cout << "[Debug] Thread exited and joined\n";

      pthread_mutex_lock(&task_queue_mutex);
      pthread_cond_broadcast(&work_cond_var);
      pthread_mutex_unlock(&task_queue_mutex);
    }

  cout << "[Debug] Thread pool worker threads joined\n";

  //kill all of the active mutexes and condition variables
  pthread_mutex_destroy(&task_queue_mutex);
  pthread_mutex_destroy(&result_queue_mutex);
  pthread_mutex_destroy(&exit_mutex);

  pthread_cond_destroy(&work_cond_var);

  cout << "[Debug] Thread pool destroyed mutexes and condition variables: SUCCESS\n";

  //TODO: free any allocated memory
}
