# Project: Lexer for Fangless Python

## Description
This project implements a lexer for a custom programming language inspired by Python, but simplified (referred to here as Fangless Python).
It is built using PLY (Python Lex-Yacc) and extends the default lexer functionality with indentation-sensitive parsing, similar to Python’s INDENT and DEDENT token.

## What's included? 

The lexer recognizes reserved words such as:
if, else, elif, while, for, def, return, class, try, except, async, await, begin, end, True, False, None, and, or, not, yield, pass, break, continue, from, as, is, assert, finally, do, then, to, read, write.

They are mapped to token types like IF, ELSE, DEF, CLASS, RETURN, etc.

### Keywords

Identifiers follow the pattern:

[a-zA-Z_][a-zA-Z0-9_]*


They are used for variable names, function names, and class names.
If the identifier matches a reserved word, it is converted to the appropriate keyword token.

### Identifiers

Identifiers follow the pattern:

[a-zA-Z_][a-zA-Z0-9_]*


They are used for variable names, function names, and class names.
If the identifier matches a reserved word, it is converted to the appropriate keyword token.


### Literals (numbers and strings)

NUMBER → integers (42)

DECIMAL → floating-point numbers (3.14)

SCONST → string constants enclosed in double quotes ("Hello World")

### Operands

Arithmetic and logical operators supported:
+, -, *, /, %, //, **,
Comparison operators: <, <=, >, >=, ==, !=, <>
Assignment operators: =, +=, -=, *=, /=, %=, //=, **=
Other operators: := (assign), ? (ternary-like), ! (negation via NOT keyword)

### Simbols and delimiters

Parentheses: ( )

Brackets: [ ]

Braces: { }

Punctuation: , ; : .

### Comments

Single-line comments start with # and continue until the end of the line.
Comments are ignored by the lexer and not returned as tokens.


### Indentation

Blocks are defined by indentation, instead of braces.

At the beginning of a line, the lexer counts spaces (WHITESPACE).

If the indentation increases, an INDENT token is emitted.

If the indentation decreases, one or more DEDENT tokens are emitted.

At the end of input, remaining DEDENT tokens are generated automatically.

This mimics Python’s block structure and ensures consistent nesting rules.

Errors such as inconsistent indentation or unexpected indent are reported with the corresponding line number.

### Error handling

The lexer handles two kinds of errors:

Illegal characters → reported with the offending character and its line number.
Example:

Illegal character '$' at line 3


Indentation errors → reported when the indentation depth is inconsistent or unexpected.
Example:

Indentation Error at line 5: Inconsistent indentation


All errors are collected in a list (errors) and also printed during execution.


## Design 

The design follows a two-stage filtering process:

Tokenization → raw tokens are generated using PLY rules (t_PLUS, t_NUMBER, etc.).

Indentation filtering → a custom post-processor (track_indent + filter_indent) transforms whitespace and newlines into proper INDENT and DEDENT tokens.

This design separates lexical analysis from block structure detection, making the lexer modular and easier to maintain.

The main lexer is wrapped in the IndentLexer class, which integrates both stages and provides a simple API:

input(source_code) → feed input to the lexer

token() → retrieve the next token

## Requirements

Python 3.8+

PLY (Python Lex-Yacc) → install via pip:

pip install ply

Optional:

Works on any OS (Windows, Linux, macOS)

Recommended editor: VSCode or PyCharm for syntax highlighting and debugging

## Usage

To execute the code, you should be placed in the folder containing all the repo files. 
Then, you can execute: 

python Lexer.py <input file>

or 

py Lexer.py <input file> 

Where input file is the name of the python file you want to tokenize. You can use Prueba.txt or Prueba2.txt or any other file written using a python language. 


##  Output examples





### Students
* Queene Zavala Morales. A77201
* Jose Andrey Pereira. C05869
