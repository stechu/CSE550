#include "bimap.hpp"
#include <map>

Bimap::Bimap()
{

}

int Bimap::add(int a, int b){
    if(left.find(a) == left.end()){
        return -1;
    } 
    if(right.find(b) == right.end()){
        return -1;
    }
    left[a] = b;
    right[b] = a;
    return 0;
}

int Bimap::get_right(int a){
    return left[a];
}

int Bimap::get_left(int b){
    return right[b];
}

int Bimap::remove_from_left(int a){
    int b = left[a];
    left.erase(left.find(a));
    right.erase(right.find(b));
    return 0;
}

int Bimap::remove_from_right(int b){
    int a = left[b];
    left.erase(left.find(a));
    right.erase(right.find(b));
    return 0;
}
