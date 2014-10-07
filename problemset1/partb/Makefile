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
SRCS=main.cc server.cc thread_pool.cc
TEST_SRCS=thread_pool_test.cc
OBJS=$(subst .cc,.o,$(SRCS))
TEST_OBJS=$(subst .cc,.o,$(TEST_SRCS))
INCLUDES=
DEBUGGER=$(shell which valgrind)
TEST=1

all: $(EXECUTABLE)

run: $(EXECUTABLE)
	./$(EXECUTABLE) 127.0.0.1 9000

test: $(OBJS) $(TEST_OBJS)
	$(CC) $(CPPFLAGS) $(LDFLAGS) $(LDLIBS) -DTEST=$(TEST) -o $(EXECUTABLE) $(OBJS) $(TEST_OBJS)
	./$(EXECUTABLE)

$(EXECUTABLE): $(OBJS) $(TEST_OBJS)
	$(CC) $(CPPFLAGS) $(LDFLAGS) $(LDLIBS) -o $(EXECUTABLE) $(OBJS) $(TEST_OBJS)

debug: $(EXECUTABLE)
	$(DEBUGGER) $(EXECUTABLE)

%.o: %.cc
	$(CC) $(CPPFLAGS) -DTEST=$(TEST) -c $<

clean:
	rm -f $(EXECUTABLE) *~ \#* *.o