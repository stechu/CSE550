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
public:
  thread_pool(int);                   //thread pool constructor

  pthread_mutex_t task_queue_mutex;   //serializes access to the task queue
  pthread_mutex_t result_queue_mutex; //serializes access to the result queue
  pthread_mutex_t exit_mutex;         //synchronizes writes to the exit status for correct termination

  pthread_cond_t task_cond_var;       //condition variable for worker threads waiting for work
  pthread_cond_t result_cond_var;     //condition variable telling main thread if result is available
  bool exit_signal;                   //global flag indicating if threads should exit
  
  vector<pthread_t> pthreads;              //bookkeeping to track the threads

  queue< pair<int, string> > task_queue;   //task queue, holds [request identifier, filepath]
  queue< pair<int, char *> > result_queue; //result queue, holds [request identifier, pointer to buffer]
  
  void queue_task(pair<int, string>);
  pair<int, string> dequeue_task();
  
  void queue_result(pair<int, char *>);
  pair<int, char *> dequeue_result();

  void destroy_thread_pool();
  void * worker_thread();
  char * read_file(char *);

  void lock_task_mutex();
  void lock_result_mutex();
  void unlock_task_mutex();
  void unlock_result_mutex();
  void wait_for_task();
  void wait_for_result();

  static void * launch_worker(void * wtf)
  {
    return ((thread_pool *) wtf)->worker_thread();
  }
};
