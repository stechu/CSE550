Name: Vincent Lee
SID: 1323346
Email: vlee2@uw.edu

Name: Shumo Chu
SID: 1323363
Email: chushumo@uw.edu

Part A
Our shell should work for all basic commands

Part B
Our server thread pool works correctly.
Our server works should be able to handle asynchronous send, receive, processing, and socket connects for at least sequential connections.
We did not have time to do stress tests with multiple concurrent clients operating at full line rate
We do not handle graceful shutdown, we change the SIGPIPE action to ignore it but do not clean up properly
We also kill zombie child processes

## Instructions to run
1. run `make`
2. In command line, run `./550server`
3. In command line, run `./550client`
