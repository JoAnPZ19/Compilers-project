#include <iostream>
#include <vector>
#include <chrono> // Used for measuring execution time
#include <algorithm> // Needed for std::swap (used in Bubble Sort)

// Use 'long long' for Fibonacci numbers as they grow too large for a standard 'int'.
using namespace std;

// =========================================================================
// 1. RECURSIVE FIBONACCI FUNCTION (O(2^n))
// =========================================================================
/**
 * Calculates the nth Fibonacci number using a recursive approach.
 *
 * This method is conceptually simple but inefficient due to
 * repeated calculations (high time complexity).
 *
 * @param n The position (integer) in the Fibonacci sequence (n >= 0).
 * @return The nth Fibonacci number (long long).
 */
long long fibonacci_recursive(int n) {
    // Base cases: F(0) = 0, F(1) = 1
    if (n <= 0) {
        return 0;
    }
    if (n == 1) {
        return 1;
    }

    // Recursive step: F(n) = F(n-1) + F(n-2)
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2);
}

// -------------------------------------------------------------------------

// =========================================================================
// 2. ITERATIVE FIBONACCI FUNCTION (O(n))
// =========================================================================
/**
 * Calculates the nth Fibonacci number using an iterative approach (a loop).
 *
 * This method is highly efficient (low time complexity) and
 * avoids redundant calculations by building the sequence bottom-up.
 *
 * @param n The position (integer) in the Fibonacci sequence (n >= 0).
 * @return The nth Fibonacci number (long long).
 */
long long fibonacci_iterative(int n) {
    if (n <= 0) {
        return 0;
    }
    if (n == 1) {
        return 1;
    }

    // Initialize the first two numbers
    long long a = 0; // F(i-2)
    long long b = 1; // F(i-1)
    long long c = 0; // F(i)

    // The loop starts at i=2 and goes up to n
    for (int i = 2; i <= n; ++i) {
        // Calculate the next number (F(i))
        c = a + b;

        // Update the sequence for the next iteration
        a = b; // F(i-1) moves to the F(i-2) position
        b = c; // F(i) is stored as F(i-1)
    }

    // 'b' holds the value of F(n)
    return b;
}

// -------------------------------------------------------------------------

// =========================================================================
// 3. BUBBLE SORT FUNCTION (O(n^2))
// =========================================================================
/**
 * Sorts a vector of numbers using the Bubble Sort algorithm.
 *
 * @param arr The vector of numbers (integers) to be sorted. Passed by reference.
 */
void bubble_sort(vector<int>& arr) {
    int n = arr.size();

    // Outer loop: Traverse through all vector elements
    for (int i = 0; i < n - 1; ++i) {
        // Inner loop: Last 'i' elements are already in place.
        for (int j = 0; j < n - i - 1; ++j) {
            // Compare adjacent elements
            if (arr[j] > arr[j + 1]) {
                // Swap elements using the standard C++ utility
                swap(arr[j], arr[j + 1]);
            }
        }
    }
}

// -------------------------------------------------------------------------

// Helper function to print the vector content
void print_vector(const vector<int>& arr) {
    cout << "[";
    for (size_t i = 0; i < arr.size(); ++i) {
        cout << arr[i];
        if (i < arr.size() - 1) {
            cout << ", ";
        }
    }
    cout << "]" << endl;
}

// =========================================================================
// MAIN FUNCTION
// =========================================================================
int main() {
    // -------------------------------------------------
    // START TIME MEASUREMENT
    // Use std::chrono for high-resolution time measurement in C++
    // -------------------------------------------------
    auto start_time = chrono::high_resolution_clock::now();

    // -------------------------------------------------
    // VECTOR DECLARATION (equivalent to Python lists)
    // -------------------------------------------------
    vector<int> numbers0 = {1345, 928, 545, 737, 1908, 953, 179, 493, 1572, 1034, 107, 1373, 1690, 260, 1806, 368, 1958, 1235, 690, 915, 757, 1060, 1141, 631, 1233, 1391, 1138, 918, 86, 664, 975, 847, 957, 1898, 1962, 1446, 1415, 1374, 1226, 1158, 704, 202, 157, 1784, 121};
    vector<int> numbers1 = {2, 4, 6 ,12, 909, 43, 1, 7, 7, 888, 11, 33, 24, 1, 5, 9, 41, 37, 15, 78, 100};
    vector<int> numbers2 = {1825, 391, 227, 557, 1753, 344, 1672, 532, 1986, 1153, 1991, 750, 71, 1653, 669, 927, 1461, 226, 249, 1009, 203, 1446, 920, 301, 1797, 1905, 391, 1734, 917, 1036, 1120, 1359, 1398, 1144, 1910, 1962, 227, 145, 606, 1067, 682, 1826, 1818, 1263, 1755};
    vector<int> numbers3 = {1911, 819, 545, 1583, 1569};
    vector<int> numbers4 = {989, 1616, 34, 836, 251, 211, 1645, 1425, 1360, 1289, 892, 651, 1972, 589, 643, 1219, 109, 639, 1547, 1196, 406, 195, 2};
    vector<int> numbers5 = {189, 1227, 364, 1609, 1769, 577, 1754, 914, 1925, 367, 1243, 1658, 59, 1996, 1522, 501, 1879, 1570, 1017, 673, 1574, 121, 1164, 648, 1726, 1250, 1624, 726, 944, 1499, 1429, 1296, 360, 1005, 1338, 1073, 61, 195, 1446, 395, 1453, 1458};
    vector<int> numbers6 = {752, 1887, 1863, 1630, 1980, 1217, 157, 1232, 29, 217, 1268, 603, 419, 1268, 1420, 694, 812, 1672, 1540, 321, 728, 330, 396, 594, 1184, 1914, 984, 697, 947, 1424, 1907, 1043, 1740, 248, 1455, 1007, 1201, 591, 819, 1819, 1752, 1084, 342, 744, 102, 1784, 1317};
    vector<int> numbers7 = {1045, 681, 1100, 1705, 417, 584, 1212, 1404, 297, 951, 838, 83, 730, 16, 1211, 1915, 897, 1557, 1422, 208, 981, 1430, 47, 1766, 371, 1102};
    vector<int> numbers8 = {1955, 798, 304, 1262, 1363};
    vector<int> numbers9 = {1958, 1031, 668, 505, 1378, 42, 737, 1350, 1215, 709, 99, 322, 738, 257, 139, 1522, 1654, 509, 1193, 1633, 786, 653, 727, 1751, 1023, 1440, 1845, 990, 1239, 490, 975, 263, 899, 773, 1925, 1415, 629, 489, 1997, 1080, 450};


    // -------------------------------------------------
    // FIBONACCI TESTS
    // -------------------------------------------------
    cout << "Recursive F(10): " << fibonacci_recursive(10) << endl;
    cout << "Iterative F(10): " << fibonacci_iterative(10) << endl;
    cout << endl;

    cout << "---------------------------------------------------------" << endl;

    // Recursive Fibonacci execution (up to 40, as it becomes very slow after that)
    for (int i = 0; i < 41; ++i) {
        cout << i << " - Recursive Fibonacci: " << fibonacci_recursive(i) << endl;
    }

    cout << "---------------------------------------------------------" << endl;

    // Iterative Fibonacci execution
    int n = 0;
    while (n < 41) {
        cout << n << " - Iterative Fibonacci: " << fibonacci_iterative(n) << endl;
        n = n + 1;
    }

    // -------------------------------------------------
    // BUBBLE SORT TESTS
    // -------------------------------------------------
    cout << "\n---------- Original Lists:" << endl;
    print_vector(numbers0);
    print_vector(numbers1);
    
    cout << "\n---------- Sorted Lists (Bubble Sort):" << endl;

    // Call the Bubble Sort function for each vector
    // NOTE: Bubble Sort modifies the original vector (pass by reference)
    bubble_sort(numbers0);
    print_vector(numbers0);
    bubble_sort(numbers1);
    print_vector(numbers1);
    bubble_sort(numbers2);
    print_vector(numbers2);
    bubble_sort(numbers3);
    print_vector(numbers3);
    bubble_sort(numbers4);
    print_vector(numbers4);
    bubble_sort(numbers5);
    print_vector(numbers5);
    bubble_sort(numbers6);
    print_vector(numbers6);
    bubble_sort(numbers7);
    print_vector(numbers7);
    bubble_sort(numbers8);
    print_vector(numbers8);
    bubble_sort(numbers9);
    print_vector(numbers9);

    // -------------------------------------------------
    // END TIME MEASUREMENT AND DISPLAY
    // -------------------------------------------------
    auto end_time = chrono::high_resolution_clock::now();

    // Calculate the difference and convert to floating-point seconds
    chrono::duration<double> elapsed_time = end_time - start_time;

    cout << "\n---------------------------------------------------------" << endl;
    cout << "✅ Execution finished!" << endl;
    cout << "**Total Elapsed Time:** **" << elapsed_time.count() << " seconds**" << endl;

    return 0; // Successful exit code
}