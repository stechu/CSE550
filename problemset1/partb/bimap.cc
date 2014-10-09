#include "bimap.hpp"
#include <map>
#include <cstdio>
#include <cassert>

Bimap::Bimap()
{

}

int Bimap::add(int a, int b){
    fprintf(stderr, "add %d and %d \n", a, b);
    if(left.find(a) != left.end()){
        fprintf(stderr, "[WARN] add %d and %d failed. \n", a, b);
        return -1;
    } 
    if(right.find(b) != right.end()){
        fprintf(stderr, "[WARN] add %d and %d failed. \n", a, b);
        return -1;
    }
    left[a] = b;
    right[b] = a;
    fprintf(stderr, "add:left: %lu + right: %lu", left.size(), right.size());
    return 0;
}

int Bimap::get_right(int a){
    return left[a];
}

int Bimap::get_left(int b){
    return right[b];
}

int Bimap::remove_from_left(int a){
    fprintf(stderr, "removing %d from left", a);
    debug_print();
    int b = left[a];
    left.erase(left.find(a));
    right.erase(right.find(b));
    debug_print();
    return 0;
}

int Bimap::remove_from_right(int b){
    printf("removing %d from right", b);
    debug_print();
    int a = left[b];
    left.erase(left.find(a));
    right.erase(right.find(b));
    debug_print();
    return 0;
}

void Bimap::debug_print(){
    std::map<int, int>::iterator it;
    printf("left map:\n");
    for(it=left.begin(); it!=left.end(); ++it){
        printf("%d : %d\n", it->first, it->second);
    }
    printf("right map:\n");
    for(right.begin(); it!=right.end(); ++it){
        printf("%d : %d\n", it->first, it->second);
    }
}

size_t Bimap::size(){
    fprintf(stderr, "left: %lu + right: %lu", left.size(), right.size());
    assert(left.size() ==  right.size());
    return left.size();
}
