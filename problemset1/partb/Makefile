#####################################################################3
# CSE 550 Autumn 2014
#
# Problem Set 1 Part B
# Author: Vincent Lee
#####################################################################3

SERVER_EXECUTABLE=550server
CLIENT_EXECUTABLE=550client
CC=$(shell which g++)
CPPFLAGS=-Wall -Wextra -g -w
CFLAGS=
LDFLAGS=-lm -lpthread
LDLIBS=
SERVER_SRCS=main.cc server.cc thread_pool.cc utilities.cc bimap.cc
CLIENT_SRCS=client.cc server.cc thread_pool.cc utilities.cc bimap.cc
TEST_SRCS=thread_pool_test.cc server_test.cc
SERVER_OBJS=$(subst .cc,.o,$(SERVER_SRCS))
CLIENT_OBJS=$(subst .cc,.o,$(CLIENT_SRCS))
TEST_OBJS=$(subst .cc,.o,$(TEST_SRCS))
INCLUDES=
DEBUGGER=$(shell which valgrind)
TEST=0

all: $(SERVER_EXECUTABLE) $(CLIENT_EXECUTABLE)

run: $(SERVER_EXECUTABLE)
	./$(SERVER_EXECUTABLE) 127.0.0.1 9000

test: $(SERVER_OBJS) $(TEST_OBJS)
	$(CC) $(CPPFLAGS) $(LDFLAGS) $(LDLIBS) -DTEST=$(TEST) -o $(SERVER_EXECUTABLE) $(SERVER_OBJS) $(TEST_OBJS)
	./$(SERVER_EXECUTABLE)

$(SERVER_EXECUTABLE): $(SERVER_OBJS) $(TEST_OBJS)
	$(CC) $(CPPFLAGS) $(LDFLAGS) $(LDLIBS) -o $(SERVER_EXECUTABLE) $(SERVER_OBJS) $(TEST_OBJS)

$(CLIENT_EXECUTABLE): $(CLIENT_OBJS) $(TEST_OBJS)
	$(CC) $(CPPFLAGS) $(LDFLAGS) $(LDLIBS) -o $(CLIENT_EXECUTABLE) $(CLIENT_OBJS) $(TEST_OBJS)

debug: $(SERVER_EXECUTABLE)
	$(DEBUGGER) $(SERVER_EXECUTABLE)

%.o: %.cc
	$(CC) $(CPPFLAGS) -DTEST=$(TEST) -c $<

clean:
	rm -f $(SERVER_EXECUTABLE) $(CLIENT_EXECUTABLE) *~ \#* *.o *.txt