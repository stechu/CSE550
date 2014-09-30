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

class thread_pool {
  //sychronization mechanisms for thread pool queues
  pthread_mutex_t thread_queue_mutex;
  pthread_mutex_t task_queue_mutex;
  pthread_mutex_t result_queue_mutex;
  
  pthread_cond_t work_cond_var;

  //queues associated with thread pool
  queue<pthread_t> thread_queue;
  queue<string> task_queue;
  queue< pair<string, char *> > result_queue;

public:
  thread_pool(int);

  void queue_task(string);
  string dequeue_task();

  void queue_result(pair<string, char*>);
  pair<string, char *> dequeue_result();

  void destroy();
  void * worker_thread();

  static void *worker_helper(void * context)
  {
    return ((thread_pool*) context)->worker_thread();
  }
};

