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

static pthread_mutex_t task_queue_mutex;   //serializes access to the task queue
static pthread_mutex_t result_queue_mutex; //serializes access to the result queue
static pthread_mutex_t exit_mutex;         //synchronizes writes to the exit status for correct termination

static pthread_cond_t work_cond_var;       //condition variable for worker threads waiting for work
static bool exit_signal;                   //global flag indicating if threads should exit

void initialize_thread_pool(int num_threads);

void queue_task(pair<int, string> s);
pair<int, string> dequeue_task();

void queue_result(pair<int, char *> s);
pair<int, char *> dequeue_result();

void destroy_thread_pool();
void * worker_thread(void * ptr);
