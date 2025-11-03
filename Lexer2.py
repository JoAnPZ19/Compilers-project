# Lexer.py - Lexer autocontenido por línea (no depende de PLY para indentación)
# Esta versión produce tokens con atributos: type, value, lineno, lexpos
# Diseñado para ser compatible con tu Parser.py (usa los mismos nombres de tokens/reserved).

import re

errors = []
indent_stack = [0]

reserved = {
    'and': 'AND',
    'as': 'AS',
    'assert': 'ASSERT',
    'async': 'ASYNC',
    'await': 'AWAIT',
    'begin': 'BEGIN',
    'break': 'BREAK',
    'class': 'CLASS',
    'continue': 'CONTINUE',
    'def': 'DEF',
    'do': 'DO',
    'elif': 'ELIF',
    'else': 'ELSE',
    'end': 'END',
    'except': 'EXCEPT',
    'false': 'FALSE',
    'finally': 'FINALLY',
    'for': 'FOR',
    'from': 'FROM',
    'if': 'IF',
    'in': 'IN',
    'is': 'IS',
    'none': 'NONE',
    'not': 'NOT',
    'or': 'OR',
    'pass': 'PASS',
    'read': 'READ',
    'return': 'RETURN',
    'then': 'THEN',
    'to': 'TO',
    'true': 'TRUE',
    'try': 'TRY',
    'while': 'WHILE',
    'write': 'WRITE',
    'yield': 'YIELD',
}

# tokens list (must match Parser.tokens)
tokens = [*reserved.values()] + [
    'ID', 'NUMBER', 'DECIMAL', 'SSTRING', 'DSTRING',
    'PLUS', 'MINUS', 'MULTI', 'DIVIDE', 'LPAREN', 'RPAREN', 'COMMA', 'SEMICOLON',
    'COLON', 'EQUAL', 'NOTEQUAL', 'LESS', 'LESSEQUAL', 'GREATER', 'GREATEREQUAL',
    'ASSIGN', 'DOT', 'DOUBLEGREATER', 'DOUBLELESS', 'TRIPLELESS',
    'TRIPLEGREATER', 'LESSGREATER', 'TERNAL', 'LITERAL', 'LBRACKET', 'RBRACKET',
    'LKEY', 'RKEY', 'WHITESPACE', 'NEWLINE', 'FDIVIDE', 'MODULE', 'POW',
    'EQUALEQUAL', 'PLUSEQUAL', 'MINUSEQUAL', 'MULTIEQUAL', 'DIVEQUAL', 'MODEQUAL',
    'FDIVEQUAL', 'POWEREQUAL', 'INDENT', 'DEDENT', 'ENDMARKER', 'QUOTATIONMARK',
    'DQUOTATIONMARK', 'UMINUS'
]

# regex pieces (order matters: multi-char operators first)
_regex_parts = [
    (r'==', 'EQUALEQUAL'),
    (r'!=', 'NOTEQUAL'),
    (r'<=', 'LESSEQUAL'),
    (r'>=', 'GREATEREQUAL'),
    (r'\+=', 'PLUSEQUAL'),
    (r'-=', 'MINUSEQUAL'),
    (r'\*=', 'MULTIEQUAL'),
    (r'/=', 'DIVEQUAL'),
    (r'%=', 'MODEQUAL'),
    (r'//=', 'FDIVEQUAL'),
    (r'\*\*=', 'POWEREQUAL'),
    (r'//', 'FDIVIDE'),
    (r'\*\*', 'POW'),
    (r'>>>' , 'TRIPLEGREATER'),
    (r'<<<' , 'TRIPLELESS'),
    (r'>>' , 'DOUBLEGREATER'),
    (r'<<' , 'DOUBLELESS'),
    (r'<>' , 'LESSGREATER'),
    (r':=', 'ASSIGN'),
    (r'\(', 'LPAREN'),
    (r'\)', 'RPAREN'),
    (r'\[', 'LBRACKET'),
    (r'\]', 'RBRACKET'),
    (r'\{', 'LKEY'),
    (r'\}', 'RKEY'),
    (r',', 'COMMA'),
    (r';', 'SEMICOLON'),
    (r':', 'COLON'),
    (r'\.', 'DOT'),
    (r'\+', 'PLUS'),
    (r'-', 'MINUS'),
    (r'\*', 'MULTI'),
    (r'/', 'DIVIDE'),
    (r'%', 'MODULE'),
    (r'\?', 'TERNAL'),
    (r'==', 'EQUALEQUAL'),
    (r'<=', 'LESSEQUAL'),
    (r'>=', 'GREATEREQUAL'),
]

# number, identifier, string
_number_re = re.compile(r'\d+(\.\d+)?')
_id_re = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
_sstring_re = re.compile(r"'([^\\\n]|(\\.))*?'")
_dstring_re = re.compile(r"\"([^\\\n]|(\\.))*?\"")

# compile operator patterns into a single regex for speed (longest-first)
_ops_pattern
