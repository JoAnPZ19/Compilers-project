# Project: Parser for Fangless Python

## Description
This project implements a parser for a custom programming language inspired by Python, but simplified (referred to here as Fangless Python).
It is built using PLY (Python Lex-Yacc) and extends the default parser functionality with indentation-sensitive parsing, similar to Python’s INDENT and DEDENT token.

## What's included? 

The parser recognizes and handles the following language structures:

Function definitions (def ... :)

Class definitions (class ... :)

Conditional statements (if, elif, else)

Loops (for, while, do ... end)

Return statements (return)

Assignments and expressions

Arithmetic and logical operations

Comments and newlines are ignored by syntax rules.

### AST Node Design

The Node class is a lightweight representation of the parse tree, used to store:

type → rule or token type ("IF", "DEF", "EXPR", etc.)
value → literal or identifier value (e.g., variable name)
children → list of sub-nodes forming the tree structure


### Error handling

The parser reports syntax and structural errors with line numbers, similar to the lexer:

SyntaxError: unexpected or misplaced tokens.

IndentationError: mismatched INDENT / DEDENT tokens (passed from the lexer).

Unexpected EOF: unclosed blocks or parentheses.

All errors are stored in an errors list and displayed at the end of execution, allowing the process to continue collecting multiple issues in one pass.


## Design 

The parser aims for:

Clarity: Pythonic grammar representation.

Modularity: clean separation between lexer, parser, and AST handling.

Extensibility: easy addition of new constructs (e.g., try/except, match, or custom decorators).

Together with the lexer, this parser forms a solid foundation for building interpreters, compilers, or static analyzers for Fangless Python.

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

    python Parser.py <input file>

or 

    py Parser.py <input file> 

Where input file is the name of the python file you want to tokenize. You can use Prueba.txt or Prueba2.txt or any other file written using a python language. 



### Students
* Queene Zavala Morales. A77201
* Jose Andrey Pereira. C05869
