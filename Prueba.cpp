#include <any>
#include <iostream>
#include <vector>
#include <map>
#include <set>
#include <tuple>
using namespace std;

std::any random_operation(std::any a, std::any b) {
    std::any c = std::any_cast<double>(a) + std::any_cast<double>(b);
    return std::any_cast<double>(std::any_cast<double>(c) + std::any_cast<double>(std::any_cast<double>(a) * std::any_cast<double>(b))) + std::any_cast<double>(2.6548);
}
