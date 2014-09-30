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
  pthread_mutex_t thread_queue_mutex;
  queue<pthread_t> thread_queue;
  pthread_t * threads;

public:
  thread_pool(int);
  void queue_thread(pthread_t);
  pthread_t dispatch_thread();
  void destroy();

};
