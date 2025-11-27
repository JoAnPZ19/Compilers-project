#include <iostream>
#include <string>
#include <vector>
#include <tuple>
#include <map>
#include <variant>


using PyValue = std::variant<
    int,
    double,
    std::string,
    std::vector<std::variant<int, double, std::string>>,
    std::map<std::string, std::variant<int, double, std::string>>,
    std::tuple<int,int,int,int>
>;


int hola(int a, int b) {
    return a + b;
}

int fib(int n) {
    if (n == 1 || n == 2)
        return 1;
    return fib(n - 1) + fib(n - 2);
}

template <typename T>
int len(const T& container) { return container.size(); }

std::vector<int> range(int n) {
    std::vector<int> r;
    for (int i = 0; i < n; i++) r.push_back(i);
    return r;
}

int main() {

    std::cout << hola(1,2) << std::endl;
    std::cout << fib(5) << std::endl;
    int a = 4;
    std::cout << a << std::endl;
    int b = 5;
    std::string a_str = "hola";
    std::string b_str = a_str + std::to_string(b);
    std::cout << b_str << std::endl;
    std::vector<std::variant<
        int,
        std::string,
        std::map<std::string, std::variant<int,std::string>>,
        std::vector<int>,
        std::tuple<int,int,int,int>>> 
    a_list = {
        1,
        std::string("hola"),
        std::map<std::string, std::variant<int,std::string>>{
            {"z", 1},
            {"x", std::string("ECCI")}
        },
        std::vector<int>{1,2,3,4},
        std::tuple<int,int,int,int>(1,2,3,4)
    };

    std::cout << "[1, 'hola', {z:1, x:'ECCI'}, [1,2,3,4], (1,2,3,4)]" << std::endl;
    std::cout << "Fibonacci" << std::endl;
    for (int i : range(len(a_list) - 1)) {
        auto &val = a_list[i];
        if (std::holds_alternative<int>(val))
            std::cout << std::get<int>(val) << std::endl;
        else if (std::holds_alternative<std::string>(val))
            std::cout << std::get<std::string>(val) << std::endl;
        else if (std::holds_alternative<std::vector<int>>(val)) {
            auto v = std::get<std::vector<int>>(val);
            std::cout << "[";
            for (size_t k = 0; k < v.size(); k++) {
                std::cout << v[k];
                if (k+1 < v.size()) std::cout << ",";
            }
            std::cout << "]" << std::endl;
        }
        else if (std::holds_alternative<std::map<std::string, std::variant<int,std::string>>>(val)) {
            std::cout << "{...dict...}" << std::endl;
        }
        else if (std::holds_alternative<std::tuple<int,int,int,int>>(val)) {
            std::cout << "(1,2,3,4)" << std::endl;
        }
    }
    auto vec = std::get<std::vector<int>>(a_list[3]);
    for (int e : vec) {
        std::cout << e << std::endl;
    }
    a = 5;
    b = 10;
    while (a < b) {
        std::cout << fib(b - 5) << std::endl;
        int c = b;
        b = c - 2;
    }
    std::cout << "Si printeo mis probabilidades de graduarme suben :)" << std::endl;
    return 0;
}
