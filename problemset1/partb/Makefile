#####################################################################3
# CSE 550 Autumn 2014
#
# Problem Set 1 Part B
# Author: Vincent Lee
#####################################################################3

EXECUTABLE=550server
CC=$(shell which g++)
CPPFLAGS=-Wall -Wextra -g
LDFLAGS=-lm -lpthread
LDLIBS=
SRCS=main.cc server.cc task_queue.cc thread_pool.cc
OBJS=$(subst .cc,.o,$(SRCS))
INCLUDES=
DEBUGGER=$(shell which valgrind)

all: $(EXECUTABLE)

$(EXECUTABLE): $(OBJS)
	$(CC) $(CPPFLAGS) $(LDFLAGS) $(LDLIBS) -o $(EXECUTABLE) $(OBJS)

debug: $(EXECUTABLE)
	$(DEBUGGER) $(EXECUTABLE)

%.o: %.cc
	$(CC) $(CPPFLAGS) -c $<

clean:
	rm -f $(EXECUTABLE) *~ \#* *.o