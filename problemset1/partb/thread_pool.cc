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

//constructor for thread pool
thread_pool::thread_pool(int num_threads)
{
  pthread_mutex_init(&thread_queue_mutex, NULL);
  pthread_mutex_init(&task_queue_mutex, NULL);
  pthread_mutex_init(&result_queue_mutex, NULL);

  pthread_mutex_lock(&thread_queue_mutex);
  for (int i = 0; i < num_threads; i++)
    {
      pthread_t new_thread;
      pthread_create(&new_thread, NULL, &thread_pool::worker_helper, (void *) i);

      //TODO: set the pthread stack, and memory parameter sizes
    }
  pthread_mutex_unlock(&thread_queue_mutex);

}

//adds a task to the task queue
// SYNCHRONIZED CALL
void thread_pool::queue_task(string s)
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
string thread_pool::dequeue_task()
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
void thread_pool::queue_result(pair<string, char*> s)
{
  pthread_mutex_lock(&result_queue_mutex);
  result_queue.push(s);
  pthread_mutex_unlock(&result_queue_mutex);
}

//removes a worker result from the queue
// SYNCHRONIZAED CALL
pair<string, char *> thread_pool::dequeue_result()
{
  pthread_mutex_lock(&result_queue_mutex);
  pair<string, char *> result = result_queue.front();
  result_queue.pop();
  pthread_mutex_unlock(&result_queue_mutex);
  return result;
}

void thread_pool::destroy()
{
  //TODO: wait for threads to join or kill them if they timeout

  pthread_mutex_destroy(&thread_queue_mutex);
  pthread_mutex_destroy(&task_queue_mutex);
  pthread_mutex_destroy(&result_queue_mutex);

  //TODO: free any allocated memory
}

//############################################################
// Main worker thread to handle the file I/Os
//############################################################
void * thread_pool::worker_thread()
{
  //enter main loop
  bool done = false;
  bool work_available = false; //hacked up flag that indicates if task is available
  string task;

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

      //no work so do nothing and wait for condition variable to fire again
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
      
      //TODO: check to see if termination condition is reached
      //STUB
    }

  return 0;
}
