//###########################################################################################
// task_queue.hpp
//
// Header file for the task queue
//###########################################################################################

#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include <queue>
#include <pthread.h>

using namespace std;

class task_queue {
  pthread_mutex_t queue_access_mutex;
  queue<string> request_queue;

public:
  task_queue();
  void add_task(string path);
  string pop_task();
};
