#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <tuple>
#include <variant>
#include <cmath>
#include <any>
using namespace std;

// Type alias for values that can be multiple types
using Value = variant<int, double, string, 
                       vector<any>, 
                       map<string, any>, 
                       tuple<int, int, int, int>>;

// Helper function for str() conversion
template<typename T>
string str(T value) {
    return to_string(value);
}

// Overload for string (already a string)
string str(const string& value) {
    return value;
}

// Helper to print any type
void print_any(const any& val) {
    try {
        cout << any_cast<int>(val);
    } catch(...) {
        try {
            cout << any_cast<double>(val);
        } catch(...) {
            try {
                cout << any_cast<string>(val);
            } catch(...) {
                try {
                    auto vec = any_cast<vector<int>>(val);
                    cout << "[";
                    for (size_t i = 0; i < vec.size(); i++) {
                        cout << vec[i];
                        if (i < vec.size() - 1) cout << ", ";
                    }
                    cout << "]";
                } catch(...) {
                    try {
                        auto tup = any_cast<tuple<int,int,int,int>>(val);
                        cout << "(" << get<0>(tup) << ", " << get<1>(tup) 
                             << ", " << get<2>(tup) << ", " << get<3>(tup) << ")";
                    } catch(...) {
                        try {
                            auto m = any_cast<map<string, any>>(val);
                            cout << "{";
                            size_t count = 0;
                            for (const auto& [k, v] : m) {
                                cout << "'" << k << "': ";
                                print_any(v);
                                if (++count < m.size()) cout << ", ";
                            }
                            cout << "}";
                        } catch(...) {
                            cout << "[complex type]";
                        }
                    }
                }
            }
        }
    }
}

// Energy function
double energy(double mass, double velocity) {
    // It calculates kinetic energy
    cout << "Calculating energy..." << endl;
    return mass * pow(velocity, 2);
}

// Random operation function
double random_operation(double a, double b) {
    cout << "Performing random operation with a and b..." << endl;
    double c = a + b;
    // Hi I'm a comment!
    return c + a * b + 2.6571896;
}

// Hola function
string hola(int a, int b) {
    return "Hola" + str(a) + str(b);
}

// Fibonacci function
int Fibonacci(int n) {
    if (n <= 0) {
        return 0;
    }
    if (n == 1 || n == 2) {
        return 1;
    }
    else {
        return Fibonacci(n - 1) + Fibonacci(n - 2);
    }
}

int main(int argc, char *argv[]) {
    // Calculate energy
    int mass = 70;
    double v = 4.5;
    cout << "La energía calculada es: " << energy(mass, v) << endl;
    
    // Test hola function
    cout << hola(1, 2) << endl;
    
    // Fibonacci for list of numbers
    vector<int> numeros = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    for (int num : numeros) {
        cout << "Fibonacci de " << str(num) << " es " << str(Fibonacci(num)) << endl;
    }
    
    // Variable reassignment with different types
    int a_int = 4;
    cout << a_int << endl;
    
    int b_int = 5;
    string a_str = "hola";
    string b_str = a_str + str(b_int);
    cout << b_str << endl;
    
    // Mixed type vector
    vector<any> a_mixed = {
        1,
        string("hola"),
        map<string, any>{{"z", 1}, {"x", string("ECCI")}},
        vector<int>{1, 2, 3, 4},
        make_tuple(1, 2, 3, 4)
    };
    
    // Print mixed vector
    cout << "[";
    for (size_t i = 0; i < a_mixed.size(); i++) {
        print_any(a_mixed[i]);
        if (i < a_mixed.size() - 1) cout << ", ";
    }
    cout << "]" << endl;
    
    cout << "Fibonacci" << endl;
    
    // Loop through mixed vector (except last element)
    for (size_t i = 0; i < a_mixed.size() - 1; i++) {
        print_any(a_mixed[i]);
        cout << endl;
    }
    
    // Loop through the 4th element (vector of ints)
    auto vec_elem = any_cast<vector<int>>(a_mixed[3]);
    for (int e : vec_elem) {
        cout << e << endl;
    }
    
    // While loop with Fibonacci
    int a = 5;
    int b = 10;
    
    while (a < b) {
        cout << Fibonacci(b - 5) << endl;
        b = b - 1;
    }
    
    // Additional variable declarations
    bool queene = true;
    double jose = 789.298781;
    string andrey = "ECCI";
    
    cout << "Finalizado" << endl;
    
    return 0;
}