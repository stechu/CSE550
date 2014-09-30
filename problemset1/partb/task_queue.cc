//###########################################################################################
// task_queue.cc
//
// Work queue for the tasks that need to be serviced.
// All incoming work is serialized and queued here.
//###########################################################################################

#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include <queue>
#include <pthread.h>
#include "task_queue.hpp"

using namespace std;

task_queue::task_queue()
{
  //initialize the synchrnization access mutex
  pthread_mutex_init(&queue_access_mutex, NULL);
}

//adds a task to the task queue
void task_queue::add_task(string path)
{
  pthread_mutex_lock(&queue_access_mutex);
  request_queue.push(path);
  pthread_mutex_unlock(&queue_access_mutex);
}

//removes and returns the head task from the request queue
string task_queue::pop_task()
{
  pthread_mutex_lock(&queue_access_mutex);
  string task_path = request_queue.front();
  request_queue.pop();
  pthread_mutex_unlock(&queue_access_mutex);
  return task_path;
}
