#ifndef BIMAP_HPP
#define BIMAP_HPP

#include <map>

class Bimap{
    public:
        Bimap();
        int add(int, int); //returns -1 if add is not succesful
        int get_right(int);
        int get_left(int);
        int remove_from_left(int);
        int remove_from_right(int);
        size_t size();
    private:
        std::map<int, int> left;
        std::map<int, int> right;
};

#endif // BIMAP_HPP
