#####################################################################3
# CSE 550 Autumn 2014
#
# Problem Set 1 Part A
# Author: Vincent Lee
#####################################################################3

EXECUTABLE=550shell
CC=$(shell which g++)
CPPFLAGS=-Wall -Wextra -g
LDFLAGS=-lm -lreadline
LDLIBS=
SRCS=main.cc parser.cc
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

run: $(EXECUTABLE)
	./$(EXECUTABLE) "ls | wc"

clean:
	rm -f $(EXECUTABLE) *~ \#* *.o