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

using namespace std;

//constructor for thread pool
thread_pool::thread_pool(int num_threads)
{
  threads = (pthread_t *) malloc(sizeof(pthread_t) * num_threads);

  pthread_mutex_init(&thread_queue_mutex, NULL);

  for (int i = 0; i < num_threads; i++)
    {

      pthread_mutex_lock(&thread_queue_mutex);
      pthread_t new_thread;
      pthread_create(&new_thread, NULL, NULL, NULL);
      pthread_mutex_unlock(&thread_queue_mutex);

    }
}

// queues a thread into the thread pool
void thread_pool::queue_thread(pthread_t t)
{
  pthread_mutex_lock(&thread_queue_mutex);
  thread_queue.push(t);
  pthread_mutex_unlock(&thread_queue_mutex);
}
   
// dequeues a thread from the thread pool
// TODO: deal with blocking until thread pool has resources available - or use a semaphore
pthread_t thread_pool::dispatch_thread()
{
  pthread_mutex_lock(&thread_queue_mutex);
  pthread_t free_thread = thread_queue.front();
  thread_queue.pop();
  pthread_mutex_unlock(&thread_queue_mutex);

  return free_thread;
}

void thread_pool::destroy()
{
  //TODO: wait for threads to join or kill them if they timeout

  pthread_mutex_destroy(&thread_queue_mutex);

  //TODO: free any allocated memory
}
