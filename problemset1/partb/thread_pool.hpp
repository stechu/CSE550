//###########################################################################################
// thread_pool.hpp
//
// Header file definitions for thread pool
//###########################################################################################

#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <queue>
#include <pthread.h>

using namespace std;

class thread_pool
{
private:
  queue< pair<int, string> > task_queue;   //task queue, holds [request identifier, filepath]
  queue< pair<int, char *> > result_queue; //result queue, holds [request identifier, pointer to buffer]

  pthread_mutex_t task_queue_mutex;        //serializes access to the task queue
  pthread_mutex_t result_queue_mutex;      //serializes access to the result queue
  pthread_mutex_t exit_mutex;              //synchronizes writes to the exit status for correct termination

  pthread_cond_t task_cond_var;            //condition variable for worker threads waiting for work
  pthread_cond_t result_cond_var;          //condition variable telling main thread if result is available
  bool exit_signal;                        //global flag indicating if threads should exit
  
  vector<pthread_t> pthreads;              //bookkeeping to track the threads

  pair<int, string> dequeue_task();        //dequeues a task - not atomic    
  void queue_result(pair<int, char *>);    //queues a task - atomic

  //worker function for each thread in the thread pool
  void * worker_thread();

  //helper function to launch worker threads
  static void * launch_worker(void * wtf)
  {
    return ((thread_pool *) wtf)->worker_thread();
  }

public:
  //thread pool constructor
  thread_pool(int);                        
  
  //atomically queues a task for processing
  void queue_task(pair<int, string>);      
  
  //dequeus a result - not atomic
  pair<int, char *> dequeue_result();      

  //destroys thread pool
  void destroy();

  //External facing lock acquire/release/wait functions

  void lock_task_mutex();
  void lock_result_mutex();
  void unlock_task_mutex();
  void unlock_result_mutex();
  void wait_for_task();
  void wait_for_result();
  bool has_task();
  bool has_result();
  void signal_task_queue();
  void signal_result_queue();

  char * read_file(char *);

};
