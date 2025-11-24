#include <any>
#include <iostream>
#include <string>
using namespace std;

std::any random_operation(std::any a, std::any b) {
    std::any c = std::any_cast<double>(a) + std::any_cast<double>(b);
    return std::any_cast<double>(std::any_cast<double>(c) + std::any_cast<double>(std::any_cast<double>(a) * std::any_cast<double>(b))) + std::any_cast<double>(2.6548);
}

std::any hola(std::any a, std::any b) {
    return std::any_cast<double>(a) + std::any_cast<double>(b);
}

std::any fib(std::any n) {
    if (((n == 1) or (n == 2))) {
        return 1;
    }
    else {
        return std::any_cast<double>(fib(std::any_cast<double>(n) - std::any_cast<double>(1))) + std::any_cast<double>(fib(std::any_cast<double>(n) - std::any_cast<double>(2)));
    }
    std::cout << "Hola, dentro de fib()" << std::endl;
}

int main() {
    std::cout << hola(1, 2) << std::endl;
    std::cout << fib(5) << std::endl;
    std::cout << a << std::endl;
    std::cout << b << std::endl;
    std::cout << a << std::endl;
    std::cout << "Fibonacci" << std::endl;
    std::cout << "Si printeo mis probabilidades de graduarme suben :)" << std::endl;
    return 0;
}
