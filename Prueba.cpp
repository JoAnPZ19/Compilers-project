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

std::any hola(std::any a, std::any b) {
    return std::any_cast<double>(a) + std::any_cast<double>(b);
}

std::cout << hola(1, 2) << std::endl;
std::any fib(std::any n) {
    if (((n == 1) or (n == 2))) {
        return 1;
    }
    else {
        return std::any_cast<double>(fib(std::any_cast<double>(n) - std::any_cast<double>(1))) + std::any_cast<double>(fib(std::any_cast<double>(n) - std::any_cast<double>(2)));
    }
    std::cout << "Hola, dentro de fib()" << std::endl;
}

std::cout << fib(5) << std::endl;
int a = 4;
std::cout << a << std::endl;
int b = 5;
std::string a = "hola";
std::string b = std::any_cast<double>(a) + std::any_cast<double>(str(b));
std::cout << b << std::endl;
std::vector<std::any> a = vector<any>{1, "hola", map<any, any>{{"z", 1}, {"x", "ECCI"}}, vector<any>{1, 2, 3, 4}, make_tuple(1, 2, 3, 4)};
std::cout << a << std::endl;
std::cout << "Fibonacci" << std::endl;
for (auto i : range(std::any_cast<double>(len(a)) - std::any_cast<double>(1))) {
    std::cout << a[i] << std::endl;
}
for (auto e : a[3]) {
    std::cout << e << std::endl;
}
int a = 5;
int b = 10;
while ((a < b)) {
    std::cout << fib(std::any_cast<double>(b) - std::any_cast<double>(5)) << std::endl;
    int c = b;
    std::string b = "hola";
    int b = std::any_cast<double>(c) - std::any_cast<double>(2);
}
std::cout << "Si printeo mis probabilidades de graduarme suben :)" << std::endl;
bool queene = true;
std::any jose = 789.298781;
std::string andrey = "ECCI";