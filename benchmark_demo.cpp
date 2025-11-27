#include <any>
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <tuple>
#include <cmath>
#include <chrono> 
using namespace std;

// Helper function for str() conversion
template<typename T>
std::string str(T value) {
    return std::to_string(value);
}

int fibonacci_recursive(std::any n) {
    if ((std::any_cast<int>(n) <= 0)) {
        return 0;
    }
    if ((std::any_cast<int>(n) == 1)) {
        return 1;
    }
    return (std::any_cast<int>(fibonacci_recursive((std::any_cast<int>(n) - 1))) + std::any_cast<int>(fibonacci_recursive((std::any_cast<int>(n) - 2))));
}

int fibonacci_iterative(std::any n) {
    if ((std::any_cast<int>(n) <= 0)) {
        return 0;
    }
    if ((std::any_cast<int>(n) == 1)) {
        return 1;
    }
    int a = 0;
    int b = 1;
    for (int i = 2; i < (std::any_cast<int>(n) + 1); i++) {
        int c = (a + b);
        a = b;
        b = c;
    }
    return b;
}


int main(int argc, char *argv[]) {
    auto start_time = chrono::high_resolution_clock::now();

    std::cout << "Recursive F(10):" << std::endl;
    std::cout << fibonacci_recursive(10) << std::endl;
    std::cout << "Iterative F(10):" << std::endl;
    std::cout << fibonacci_iterative(10) << std::endl;
    for (int i = 0; i < 41; i++) {
        std::cout << i << "- Recursive Fibonacci: " << fibonacci_recursive(i) << std::endl;
    }
    std::cout << "---------------------------------------------------------" << std::endl;
    int n = 0;
    while ((n < 41)) {
        std::cout << n << "- Iterative Fibonacci: " << fibonacci_iterative(n) << std::endl;
        n = (n + 1);
    }
    std::vector<int> numbers0 = std::vector<int>{1345, 928, 545, 737, 1908, 953, 179, 493, 1572, 1034, 107, 1373, 1690, 260, 1806, 368, 1958, 1235, 690, 915, 757, 1060, 1141, 631, 1233, 1391, 1138, 918, 86, 664, 975, 847, 957, 1898, 1962, 1446, 1415, 1374, 1226, 1158, 704, 202, 157, 1784, 121};
    std::vector<int> numbers1 = std::vector<int>{2, 4, 6, 12, 909, 43, 1, 7, 7, 888, 11, 33, 24, 1, 5, 9, 41, 37, 15, 78, 100};
    std::vector<int> numbers2 = std::vector<int>{1825, 391, 227, 557, 1753, 344, 1672, 532, 1986, 1153, 1991, 750, 71, 1653, 669, 927, 1461, 226, 249, 1009, 203, 1446, 920, 301, 1797, 1905, 391, 1734, 917, 1036, 1120, 1359, 1398, 1144, 1910, 1962, 227, 145, 606, 1067, 682, 1826, 1818, 1263, 1755};
    std::vector<int> numbers3 = std::vector<int>{1911, 819, 545, 1583, 1569};
    std::vector<int> numbers4 = std::vector<int>{989, 1616, 34, 836, 251, 211, 1645, 1425, 1360, 1289, 892, 651, 1972, 589, 643, 1219, 109, 639, 1547, 1196, 406, 195, 2};
    std::vector<int> numbers5 = std::vector<int>{189, 1227, 364, 1609, 1769, 577, 1754, 914, 1925, 367, 1243, 1658, 59, 1996, 1522, 501, 1879, 1570, 1017, 673, 1574, 121, 1164, 648, 1726, 1250, 1624, 726, 944, 1499, 1429, 1296, 360, 1005, 1338, 1073, 61, 195, 1446, 395, 1453, 1458};
    std::vector<int> numbers6 = std::vector<int>{752, 1887, 1863, 1630, 1980, 1217, 157, 1232, 29, 217, 1268, 603, 419, 1268, 1420, 694, 812, 1672, 1540, 321, 728, 330, 396, 594, 1184, 1914, 984, 697, 947, 1424, 1907, 1043, 1740, 248, 1455, 1007, 1201, 591, 819, 1819, 1752, 1084, 342, 744, 102, 1784, 1317};
    std::vector<int> numbers7 = std::vector<int>{1045, 681, 1100, 1705, 417, 584, 1212, 1404, 297, 951, 838, 83, 730, 16, 1211, 1915, 897, 1557, 1422, 208, 981, 1430, 47, 1766, 371, 1102};
    std::vector<int> numbers8 = std::vector<int>{1955, 798, 304, 1262, 1363};
    std::vector<int> numbers9 = std::vector<int>{1958, 1031, 668, 505, 1378, 42, 737, 1350, 1215, 709, 99, 322, 738, 257, 139, 1522, 1654, 509, 1193, 1633, 786, 653, 727, 1751, 1023, 1440, 1845, 990, 1239, 490, 975, 263, 899, 773, 1925, 1415, 629, 489, 1997, 1080, 450};
    return 0;

    auto end_time = chrono::high_resolution_clock::now();

    // Calculate the difference and convert to floating-point seconds
    chrono::duration<double> elapsed_time = end_time - start_time;

    cout << "\n---------------------------------------------------------" << endl;
    cout << "✅ Execution finished!" << endl;
    cout << "**Total Elapsed Time:** **" << elapsed_time.count() << " seconds**" << endl;
}
