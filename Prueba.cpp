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

int hola(std::any a, std::any b) {
    return (std::any_cast<int>(a) + std::any_cast<int>(b));
}

int fib(std::any n) {
    if (((std::any_cast<int>(n) == 1) || (std::any_cast<int>(n) == 2))) {
        return 1;
    }
    else {
        return (std::any_cast<int>(fib((std::any_cast<int>(n) - 1))) + std::any_cast<int>(fib((std::any_cast<int>(n) - 2))));
    }
}


int main(int argc, char *argv[]) {
    std::cout << hola(1, 2) << std::endl;
    std::cout << fib(5) << std::endl;
    int a = 4;
    std::cout << a << std::endl;
    int b = 5;
    a = "hola";
    b = (a + str(b));
    std::cout << b << std::endl;
    a = std::vector<std::any>{1, "hola", std::map<std::string, std::any>{{"z", 1}, {"x", "ECCI"}}, std::vector<int>{1, 2, 3, 4}, std::tuple<int, int, int, int>(1, 2, 3, 4)};
    std::cout << a << std::endl;
    std::cout << "Fibonacci" << std::endl;
    for (int i : /* range((a.size() - 1)) */) {
        std::cout << a[i] << std::endl;
    }
    for (auto e : a[3]) {
        std::cout << e << std::endl;
    }
    a = 5;
    b = 10;
    while ((a < b)) {
        std::cout << fib((b - 5)) << std::endl;
        int c = b;
        b = "hola";
        b = (c - 2);
    }
    std::cout << "Si printeo hasta aquí mis probabilidades de pasar el curso y graduarme suben :)" << std::endl;
    return 0;
}
