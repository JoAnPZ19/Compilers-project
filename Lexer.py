# Based on https://github.com/ThaisBarrosAlvim/mini-compiler-python/blob/master/src/lexer.py
import ply.lex as lex
import sys

errors = []

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
    'False': 'FALSE',
    'finally': 'FINALLY',
    'for': 'FOR',
    'from': 'FROM',
    'if': 'IF',
    'in': 'IN',
    'is': 'IS',
    'None': 'NONE',
    'not': 'NOT',
    'or': 'OR',
    'pass': 'PASS',
    'read': 'READ',
    'return': 'RETURN',
    'then': 'THEN',
    'to': 'TO',
    'True': 'TRUE',
    'try': 'TRY',
    'while': 'WHILE',
    'write': 'WRITE',
    'yield': 'YIELD',
}

tokens = [*reserved.values()] +[
        # Literals (identifier, integer constant, float constant, string constant, char const)'ID',
    'ID', 'NUMBER', 'SCONST',

        # Operators (+,-,*,/,%,<,>,<=,>=,==,!=,&&,||,!,=)
    'PLUS', 'MINUS', 'MULTI', 'DIVIDE', 'LPAREN', 'RPAREN', 'COMMA', 'SEMICOLON', 'COLON', 'EQUAL','NOTEQUAL', 'LESS',
    'LESSEQUAL', 'GREATER', 'GREATEREQUAL', 'ASSIGN', 'DOT', 'DOUBLEGREATER', 'DOUBLELESS', 'TRIPLELESS', 'DECIMAL',
    'TRIPLEGREATER', 'LESSGREATER', 'TERNAL', 'LITERAL','LBRACKET','RBRACKET','LKEY','RKEY','INDENT','DEDENT','WHITESPACE','NEWLINE',
    'FDIVIDE', 'MODULE', 'POW', 'EQUALEQUAL', 'PLUSEQUAL', 'MINUSEQUAL', 'MULTIEQUAL', 'DIVEQUAL', 'MODEQUAL', 'FDIVEQUAL', 'POWEREQUAL',        
]
    # Regular expression rules for simple tokens

    # Operators
t_PLUS = r'\+'
t_MINUS = r'-'
t_MULTI = r'\*'
t_DIVIDE = r'/'
t_COMMA = r','
t_SEMICOLON = r';'
t_COLON = r':'
t_EQUAL = r'='
t_NOTEQUAL = r'!='
t_LESS = r'<'
t_GREATER = r'>'
t_ASSIGN = r':='
t_DOT = r'\.'
t_LKEY = r'\{'
t_RKEY = r'\}'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_DOUBLEGREATER = r'>>'
t_DOUBLELESS = r'<<'
t_TRIPLELESS = r'<<<'
t_TRIPLEGREATER = r'>>>'
t_LESSGREATER = r'<>'
t_TERNAL = r'\?'
t_FDIVIDE = r'//'
t_MODULE = r'\%'
t_POW = r'\*'
t_EQUALEQUAL = r'=='
t_LESSEQUAL = r'<='
t_GREATEREQUAL = r'>='
t_PLUSEQUAL = r'\+='
t_MINUSEQUAL = r'-='
t_MULTIEQUAL = r'\*='
t_DIVEQUAL = r'/='
t_MODEQUAL = r'\%='
t_FDIVEQUAL = r'//='
t_POWEREQUAL = r'\*\*='

    # String literal
t_SCONST = r'\"([^\\\n]|(\\.))*?\"'

t_ignore = ' \t'


    # Numbers
def t_DECIMAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_COMMENT(t):
    r'\#.*'
    pass

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

def t_error(t):
    errors.append(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    print(errors[-1])
    t.lexer.skip(1)

lexer = lex.lex()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lexer.py <filename>")
        sys.exit(1)

    file = sys.argv[1]
    with open(file, "r", encoding="utf-8") as f:
        data = f.read()

    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)