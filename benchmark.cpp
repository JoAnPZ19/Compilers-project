#include <any>
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <tuple>
#include <cmath>
using namespace std;

// Helper function for str() conversion
template<typename T>
std::string str(T value) {
    return std::to_string(value);
}



int main(int argc, char *argv[]) {
    std::cout << "---------- Original list:" << std::endl;
    std::cout << numbers0 << std::endl;
    std::cout << numbers1 << std::endl;
    std::cout << numbers2 << std::endl;
    std::cout << numbers3 << std::endl;
    std::cout << numbers4 << std::endl;
    std::cout << numbers5 << std::endl;
    std::cout << numbers6 << std::endl;
    std::cout << numbers7 << std::endl;
    std::cout << numbers8 << std::endl;
    std::cout << numbers9 << std::endl;
    auto sorted_numbers0 = bubble_sort(numbers0);
    std::cout << "---------- Sorted list (Bubble Sort):" << std::endl;
    std::cout << bubble_sort(numbers0) << std::endl;
    std::cout << bubble_sort(numbers1) << std::endl;
    std::cout << bubble_sort(numbers2) << std::endl;
    std::cout << bubble_sort(numbers3) << std::endl;
    std::cout << bubble_sort(numbers4) << std::endl;
    std::cout << bubble_sort(numbers5) << std::endl;
    std::cout << bubble_sort(numbers6) << std::endl;
    std::cout << bubble_sort(numbers7) << std::endl;
    std::cout << bubble_sort(numbers8) << std::endl;
    std::cout << bubble_sort(numbers9) << std::endl;
    auto final_time = None();
    int elapsed_time = (std::any_cast<int>(final_time) - std::any_cast<int>(start_time));
    std::cout << "----- Elapsed time: " << elapsed_time << std::endl;
    return 0;
}
