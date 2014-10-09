//###########################################################################################
// thread_pool.cc
//
// Definitions for thread pool object
//###########################################################################################

#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <queue>
#include <pthread.h>
#include "thread_pool.hpp"
#include <fstream>
#include <assert.h>
#include <iostream>
#include "thread_pool_test.hpp"
#include <sstream>

using namespace std;

//########################################################################
// thread pool initialization
// - threads are created and launched into worker thread function
// - bookkeeping so that threads can be cleaned up later on termination
//########################################################################
thread_pool::thread_pool(int num_threads, int self_pipe_fd)
{
  exit_signal = false;

  //initiliazations for the mutex and condition variables
  if(pthread_mutex_init(&task_queue_mutex, NULL) < 0)
    cout << "[Info] Failed to initialize task queue mutex...\n";
  if(pthread_mutex_init(&result_queue_mutex, NULL) < 0)
    cout << "[Info] Failed to initialize result queue mutex...\n";
  if(pthread_mutex_init(&exit_mutex, NULL) < 0)
    cout << "[Info] Failed to initialize exit mutex...\n";
  if(pthread_mutex_init(&self_pipe_mutex, NULL) < 0)
    cout << "goddamnit \n";

  if (pthread_cond_init(&task_cond_var, NULL) < 0)
    cout << "[Info] Failed to initialize work condition variable...\n";
  if(pthread_cond_init(&result_cond_var, NULL) < 0)
    cout << "[Info] Failed to initialize result condition variable...\n";
  
  self_pipe_write_fd = self_pipe_fd;

  //create the pthreads for the pool and launch them into the workers
  pthread_mutex_lock(&exit_mutex);
  for (int i = 0; i < num_threads; i++)
    {
      pthread_t new_thread;
      pthread_create(&new_thread, NULL, thread_pool::launch_worker, this);

      pthreads.push_back(new_thread);
    }
  pthread_mutex_unlock(&exit_mutex);
}

//########################################################################
// External Facing Mutex Acquire/Unlock/Wait Functions
//########################################################################

void thread_pool::lock_task_mutex()
{
  pthread_mutex_lock(&task_queue_mutex);
}
void thread_pool::lock_result_mutex()
{
  pthread_mutex_lock(&result_queue_mutex);
}
void thread_pool::unlock_task_mutex()
{
  pthread_mutex_unlock(&task_queue_mutex);
}
void thread_pool::unlock_result_mutex()
{
  pthread_mutex_unlock(&result_queue_mutex);
}

void thread_pool::lock_self_pipe_mutex()
{
  pthread_mutex_lock(&self_pipe_mutex);
}

void thread_pool::unlock_self_pipe_mutex()
{
  pthread_mutex_unlock(&self_pipe_mutex);
}

//result_queue_mutex must be acqired before calling this
void thread_pool::wait_for_result()
{
  pthread_cond_wait(&result_cond_var, &result_queue_mutex);
}

//task_queue_mutex must be acqired before calling this
void thread_pool::wait_for_task() 
{
  pthread_cond_wait(&task_cond_var, &task_queue_mutex);
}

//notify that there are new tasks waiting in the task queue
void thread_pool::signal_task_queue()
{
  pthread_cond_broadcast(&task_cond_var);
}

//notify that there are new results waiting in the task queue
void thread_pool::signal_result_queue()
{
  pthread_cond_broadcast(&result_cond_var);
}

//return if there are tasks in the queue - NOT ATOMIC
bool thread_pool::has_task()
{
  bool task_flag;
  task_flag = (task_queue.size() > 0) ? true : false;
  return task_flag;
}

//return if there are results in the queue - NOT ATOMIC
bool thread_pool::has_result()
{
  bool result_flag;
  result_flag = (result_queue.size() > 0) ? true : false;
  return result_flag;
}

//########################################################################
// Task/Result Queueing Call Definitions
//########################################################################

//########################################################################
// adds a task to the task queue
// - argument is a pair containing [request identifier, filepath name]
// - CALL IS ATOMIC - do not acquire task_queue_mutex before call
//########################################################################

void thread_pool::queue_task(pair<int, string> s)
{
  pthread_mutex_lock(&task_queue_mutex);
  task_queue.push(s);
  pthread_cond_broadcast(&task_cond_var);      //signal the worker threads that more work has arrived
  pthread_mutex_unlock(&task_queue_mutex);
}

//########################################################################
// gets the task at the front of the queue
// - should only be called from the thread_pool
// - Throws an exception if not work is available
// - THIS CALL IS NOT ATOMIC
//########################################################################

pair<int, string> thread_pool::dequeue_task()
{
  pair<int, string> task;
  if (task_queue.size() == 0)
    throw 42; //throw an exception if the task_queue is empty
  else
    {
      task = task_queue.front();
      task_queue.pop();
    }
  return task;
}

//########################################################################
// adds a worker result to the result queue
// - should only be called from the thread_pool
// - CALL IS ATOMIC - result_queue_mutex must be freed before call
//########################################################################

void thread_pool::queue_result(pair<int, char*> s)
{
  pthread_mutex_lock(&result_queue_mutex);
  result_queue.push(s);
  pthread_cond_broadcast(&result_cond_var);
  notify_self_pipe();
  pthread_mutex_unlock(&result_queue_mutex);
}

//########################################################################
// removes a worker result from the queue
// - returns a pair containg [request identification, buffer pointer]
// - a NULL buffer pointer is returned if filepath does not exist
// - does not lock mutex, assumes caller holds mutex after signal
// - THIS CALL IS NOT ATOMIC
//########################################################################

pair<int, char *> thread_pool::dequeue_result()
{
  pair<int, char*> result = result_queue.front();
  result_queue.pop();
  return result;
}

//############################################################
// Main worker thread to handle the file I/Os
//############################################################
void * thread_pool::worker_thread()
{
  //enter main loop
  bool done = false;
  bool work_available = false; //hacked up flag that indicates if task is available
  pair<int, string> task;

  while (!done)
    {

      //##########################################################
      // Handle the task dequeueing from the task queue
      //##########################################################

      //check if there is work to do
      pthread_mutex_lock(&task_queue_mutex);
      try
	{
	  work_available = has_task();
	  if (work_available)
	    task = dequeue_task();
	  //TODO: put assertions here
	}
      catch (int e)
	{
	  work_available = false;
	}
      if (!work_available)
	{
	  pthread_cond_wait(&task_cond_var, &task_queue_mutex);
	  work_available = has_task();
	  if (work_available)
	    task = dequeue_task();
	}
      pthread_mutex_unlock(&task_queue_mutex);

      //##########################################################
      // Handle file reading if the task is valid
      //##########################################################

      if (work_available == true)
	{
	  char * char_buffer = read_file((char *) task.second.c_str());

	  pair<int, char*> result;
	  result.first = task.first;
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

//########################################################################
// reads the file from the given filepath input
// - returns the entire file contents in a char *
//########################################################################

char * thread_pool::read_file(char * filepath)
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
// writes a byte to the self-pipe to notify main thread
//########################################################################
void thread_pool::notify_self_pipe()
{
  //write a byte to the pipe
  pthread_mutex_lock(&self_pipe_mutex);
  write(self_pipe_write_fd, "A", 1);
  pthread_mutex_unlock(&self_pipe_mutex);
  cout << "Sent a self-pipe signal... " << self_pipe_write_fd << "\n";
}

//########################################################################
// destroys the thread pool
// - allows threads to terminate before joining
// - signals threads the exit worker thread
// - releases mutexes and condition variables
//########################################################################
void thread_pool::destroy()
{
  //signal to all the threads to exit
  pthread_mutex_lock(&exit_mutex);
  exit_signal = true;
  pthread_mutex_unlock(&exit_mutex);
  
  //broadcast a wake up signal for waiting threads to exit
  pthread_mutex_lock(&task_queue_mutex);
  pthread_cond_broadcast(&task_cond_var);
  pthread_mutex_unlock(&task_queue_mutex);

  //thread join loop
  for (int i = 0; i < (int) pthreads.size(); i++)
    {
      //attempt to join the target thread
      pthread_t target_thread = pthreads[i];
      pthread_join(target_thread, NULL);

      //signal to each of the threads to ensure they terminate
      pthread_mutex_lock(&task_queue_mutex);
      pthread_cond_broadcast(&task_cond_var);
      pthread_mutex_unlock(&task_queue_mutex);
    }

  //kill all of the active mutexes and condition variables
  pthread_mutex_destroy(&task_queue_mutex);
  pthread_mutex_destroy(&result_queue_mutex);
  pthread_mutex_destroy(&exit_mutex);
  pthread_mutex_destroy(&self_pipe_mutex);

  pthread_cond_destroy(&task_cond_var);
  pthread_cond_destroy(&result_cond_var);

}
