# Project: C++ Transpiler for Fangless Python

## Description
Fangless Python is a simplified Python-like language designed for experimentation with lexing, parsing, static analysis, AST processing, and code generation.

## What's included? 

-This project includes:
-An indentation-sensitive lexer (Python-style INDENT/DEDENT)
-A PLY (Python Lex-Yacc) parser
-A clean AST node system
-A static type inference analyzer
-A C++ code generator, capable of transpiling Fangless Python to modern C++

### Indentation-based Lexer

The custom lexer converts physical indentation into INDENT and DEDENT tokens, closely matching Python’s own behavior.
This allows block structures without braces and enables clear, Pythonic grammar rules in the parser.


### Full Parser for Core Language Constructs

The parser supports:
- def ...: function definitions
- Indented suites / blocks
- Assignments
- Arithmetic and boolean expressions
- Conditionals (if / elif / else)
- Loop constructs (for, while)
- return statements
- Lists, tuples, dictionaries
- Subscripts and indexing
- Function calls
- Built-ins: print, len, range, etc.
- Comments and blank lines are ignored.

AST Design

A single lightweight Node class represents all parts of the program:
- type — node type ("if", "assignment", "call", …)
- value — identifier or literal
- children — ordered subnodes

This minimal design makes the AST easy to debug, print, transform, and transpile.

## Static Type Analyzer (Type Inference)

Analyzer.py implements a full static type inference pass over the AST.
It infers:

- int, double, string, bool, none
- list[T], dict[K,V], tuple[...]
- Function parameter and return types
- The type of expressions and variables (Work in progress)
- Types across control flow
- A multi-scope symbol table with shadowing (Work in progress)
- Type System Philosophy
- This project follows a minimal-string rule: 
- Only literal "..." strings count as type string 
- Everything else defaults to numeric (double)
- str(x) does not convert the function into a “string context”
- If a function contains no string literals, the whole function becomes numerically typed

This rule allows the C++ generator to produce clean, strongly-typed code without falling back to std::any.

## C++ Code Generator (Transpiler)

Visitor.py walks the AST and emits valid C++ code.

Supported code generation:

* Function signatures based on inferred types
* Automatic selection between double, int, bool, std::string
* Generation of:
* std::vector<T>
* std::map<K,V>
* std::tuple<...>
* Literal translation ("hello", lists, dicts, tuples)
* Intelligent casting for unknown types
* static_cast<double> for safe numeric coercion
* No std::any_cast except as a rare fallback

## Known Issues & Limitations 

### Type inference is incomplete and sometimes contradictory
- Variables may unexpectedly collapse to ANY during analysis.
- Type promotion rules conflict in different parts of the analyzer.
- Numeric coercion sometimes overrides legitimate types.
- Some expressions infer as string because of earlier nodes, even when they shouldn’t.
- Function return type unification is imperfect (e.g., mixing int/double/string).

### String typing is fragile
- Marks identifiers as string incorrectly
- Propagates string types through certain operations
- Misinterprets calls like str(b) as string contexts

### Complex expressions break inference

These often degrade to ANY, forcing the C++ output into fallback casting.

- Nested calls
- Function recursion
- Tuple unpacking
- Dictionary updates
- Mixed-type arithmetic

## Requirements

* Python 3.8+

* PLY (Python Lex-Yacc) → install via pip:


          pip install ply


* **Optional:**

Works on any OS (Windows, Linux, macOS)

Recommended editor: VSCode or PyCharm for syntax highlighting and debugging

## Usage

To execute the code, you should be placed in the folder containing all the repo files. 
Then, you can execute: 

    python Visitor.py <input file>

or 

    py Visitor.py <input file> 

Where input file is the name of the python file you want to tokenize. You can use Prueba.txt or Prueba2.txt or any other file written using a python language. 



### Students
* Queene Zavala Morales. A77201
* Jose Andrey Pereira. C05869
