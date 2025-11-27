# Project: C++ Transpiler for Fangless Python

## Description
Fangless Python is a simplified Python-like language designed for experimentation with lexing, parsing, static analysis, AST processing, and code generation.

This project implements a complete toolchain to transpile Python-like source code into optimized, modern C++ code.

***

## 📦 What's Included? 

This project includes the following core components:

* **`Lexer.py`**: An indentation-sensitive lexer (Python-style `INDENT`/`DEDENT`) that converts physical indentation into tokens, allowing for clear, Pythonic grammar rules.
* **`Parser.py`**: A PLY (Python Lex-Yacc) parser that builds a clean **Abstract Syntax Tree (AST)** from the tokens.
* **`Analyzer.py`**: A **static type inference analyzer** that traverses the AST to determine variable and expression types, supporting complex structures like lists, dictionaries, and functions.
* **`Visitor.py`**: The C++ code generator (`CppVisitor`), capable of transpiling Fangless Python to modern C++ (`.cpp` files). It includes logic to handle dynamic Python features (like type reassignment) by issuing **transpilation warnings** and falling back to `std::any` where necessary.
* **`benchmark.py`**: Python file containing the **Iterative Fibonacci** and **Bubble Sort** implementations, used to measure Python's native execution time.
* **`benchmark.cpp`**: The C++ file generated from `benchmark.py`, used to measure the execution time of the transpiled code.

### Supported Constructs

The parser and transpiler support:
* `def ...:` function definitions
* Indented suites / blocks
* Assignments and type reassignments (with warnings)
* Arithmetic, comparison, and boolean expressions
* Conditionals (`if` / `elif` / `else`)
* Loop constructs (`for`, `while`, `range` iteration)
* `return`, `break`, and `continue` statements
* Lists (`std::vector`), tuples (`std::tuple`), dictionaries (`std::map`), and sets (`std::set`).
* Subscripts, indexing, and map key access.
* Function calls and built-ins (`print`, `len`, `str`, `int`, `float`).

***

## 🛠️ Requirements

* Python 3.8+
* PLY (Python Lex-Yacc) → install via pip:
    ```bash
    pip install ply
    ```
* **C++ Compiler**: To compile the generated `.cpp` file (e.g., GCC, Clang).

***

## 🚀 Usage

To execute the transpilation process, run the main `Visitor.py` file with your Python input file:

```bash
python Visitor.py <input_file.py> -o <output_file.cpp>
```

## Comparison

| Iteraciones | Python | Pure C++ | C++ transpiled |
| :---------: | :----: | :----------: | :------------: |
|      1      | 34.37574 | 1.34719 | 100 |
|      2      | 34.44429 | 1.32408 | 100 |
|      3      | 35.39543 | 1.31808 | 100 |
|      4      | 34.565603 | 1.3051 | 100 |
|      5      | 34.150238 | 1.34496 | 100 |
|      6      | 34.3899204 | 1.35729 | 100 |
|      7      | 33.9984008 | 1.3466 | 100 |
|      8      | 34.4992194 | 1.33068 | 100 |
|      9      | 34.126796 | 1.32732 | 100 |
|     10      | 34.502017 | 1.35939 | 100 |
| **Average** | **34.44332618** | **1.336069** | **100** |

### Students
* Queene Zavala Morales. A77201
* Jose Andrey Pereira. C05869
