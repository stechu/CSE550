/*
** client.cc -- a simple stream socket client 
*/

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <netdb.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>

#include <cstring>
#include <string>
#include <vector>
#include <cassert>

#include "constants.hpp"
#include "utilities.hpp"

void connect(const char * host, const char * port, const std::string url) {
    // boilerplates
    int sockfd, numbytes;
    char buf[MAX_DATA_SIZE];
    struct addrinfo hints, *servinfo, *p;
    int rv = -1;
    char s[INET6_ADDRSTRLEN];

    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if ((rv = getaddrinfo(host, port, &hints, &servinfo)) != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
        exit(EXIT_FAILURE);
    }

    // loop through all the results and connect to the first we can
    for (p = servinfo; p != NULL; p = p->ai_next) {
        if ((sockfd = socket(p->ai_family, p->ai_socktype,
                p->ai_protocol)) == -1) {
            perror("client: socket");
            continue;
        }

        if (connect(sockfd, p->ai_addr, p->ai_addrlen) == -1) {
            close(sockfd);
            perror("client: connect");
            continue;
        }

        break;
    }

    if (p == NULL) {
        fprintf(stderr, "client: failed to connect\n");
        exit(EXIT_FAILURE);
    }

    inet_ntop(p->ai_family, get_in_addr((struct sockaddr *)p->ai_addr),
            s, sizeof s);
    printf("client: connecting to %s\n", s);

    freeaddrinfo(servinfo);     // all done with this structure

    // send request
    size_t raw_size = url.size()+1;
    assert(raw_size <= MAX_DATA_SIZE);
    char raw_req_msg[MAX_DATA_SIZE];
    strcpy(raw_req_msg, url.c_str());
    printf("[INFO] client: sending %s \n", raw_req_msg);
    if ((numbytes = send(sockfd, raw_req_msg, raw_size, 0)) == -1){
        perror("[ERROR] error on sending req from client");
        exit(EXIT_FAILURE);
    }

    // receive content
    if ((numbytes = recv(sockfd, buf, MAX_DATA_SIZE-1, 0)) == -1) {
        perror("[ERROR] error on receiving from client");
        exit(EXIT_FAILURE);
    }
    buf[numbytes] = '\0';
    printf("[INFO] client: received '%s'\n", buf);

    close(sockfd);  // close socket
}

// client main
int main() {

    // hardcoded request
    static std::vector<std::string> urls;
    urls.push_back("main.cc\n");
    urls.push_back("server.cc\n");
    urls.push_back("client.cc\n");

    // connect to server
    for (int i = 0; i < REQUEST_TIMES; i++) {
        connect(SERVER_IP, SERVER_PORT, urls[i%urls.size()]);
    }

    return 0;
}
