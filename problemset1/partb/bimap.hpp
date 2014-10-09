#ifndef BIMAP_HPP
#define BIMAP_HPP

#include <map>

class Bimap{
    public:
        Bimap();
        int add(int a, int b); //returns -1 if add is not succesful
        int get_right(int a);
        int get_left(int b);
        int remove_from_left(int a);
        int remove_from_right(int b);
        size_t size();
    private:
        std::map<int, int> left;
        std::map<int, int> right;
};

#endif // BIMAP_HPP
