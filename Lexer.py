# Based on https://github.com/ThaisBarrosAlvim/mini-compiler-python/blob/master/src/lexer.py
import ply.lex as lex
import sys

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

tokens = [*reserved.values()] + [
    # Literals (identifier, integer constant, float constant, string constant, char const)
    'ID', 'NUMBER', 'SCONST',

    # Operators (+,-,*,/,%,<,>,<=,>=,==,!=,&&,||,!,=)
    'PLUS', 'MINUS', 'MULTI', 'DIVIDE', 'LPAREN', 'RPAREN', 'COMMA', 'SEMICOLON', 
    'COLON', 'EQUAL', 'NOTEQUAL', 'LESS', 'LESSEQUAL', 'GREATER', 'GREATEREQUAL', 
    'ASSIGN', 'DOT', 'DOUBLEGREATER', 'DOUBLELESS', 'TRIPLELESS', 'DECIMAL',
    'TRIPLEGREATER', 'LESSGREATER', 'TERNAL', 'LITERAL', 'LBRACKET', 'RBRACKET',
    'LKEY', 'RKEY', 'WHITESPACE', 'NEWLINE', 'FDIVIDE', 'MODULE', 'POW', 
    'EQUALEQUAL', 'PLUSEQUAL', 'MINUSEQUAL', 'MULTIEQUAL', 'DIVEQUAL', 'MODEQUAL', 
    'FDIVEQUAL', 'POWEREQUAL', 'INDENT', 'DEDENT', 'ENDMARKER', 'QUOTATIONMARK'        
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
t_POW = r'\*\*'
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

def t_WHITESPACE(t):
    r'[ \t]+'
    return t

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

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

def t_error(t):
    errors.append(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    print("Skip error: ", errors[-1])
    t.lexer.skip(1)

# INDENT states
NO_INDENT = 0
MIGHT_INDENT = 1
MUST_INDENT = 2

def _new_token_manual(type, lineno=None, lexer=None):
    tok = lex.LexToken()
    tok.lexpos = 0
    tok.value = None
    tok.type = type
    tok.lineno = lineno if lineno is not None else (lexer.lineno if lexer else 0)
    return tok

def DEDENT(lineno):
    return _new_token_manual("DEDENT", lineno)

def INDENT(lineno):
    return _new_token_manual("INDENT", lineno)

def track_indent(lexer, tokens):
    lexer.at_line_start = True
    indent_state = NO_INDENT
    
    for token in tokens:
        token.at_line_start = lexer.at_line_start
        
        if token.type == "COLON":
            indent_state = MIGHT_INDENT
            token.must_indent = False
        elif token.type == "NEWLINE":
            lexer.at_line_start = True
            if indent_state == MIGHT_INDENT:
                indent_state = MUST_INDENT
            token.must_indent = False
        elif token.type == "WHITESPACE":
            # White space is the beggining of each line
            token.must_indent = False
            
        else:
            if indent_state == MUST_INDENT:
                token.must_indent = True
            else:
                token.must_indent = False
            lexer.at_line_start = False
            indent_state = NO_INDENT
        
        yield token

def filter_indent(tokens):
    global indent_stack
    depth = 0
    pending_whitespace = None
    
    for token in tokens:
        if token.type == "DEF":
            indent_stack = [0]
            pending_whitespace = None
            continue

        if token.type == "WHITESPACE" and token.at_line_start:
            depth = len(token.value)
            pending_whitespace = token
            continue
        
        if token.type == "NEWLINE":
            depth = 0
            pending_whitespace = None
            yield token
            continue
        
        if pending_whitespace is not None:
            try:
                if token.must_indent:
                    if depth <= indent_stack[-1]:
                        raise IndentationError("Error 01!! Block must be indented")
                    indent_stack.append(depth)
                    yield INDENT(token.lineno)
                elif token.at_line_start:
                    if depth > indent_stack[-1]:
                        raise IndentationError("Error 02!! Indentation found, but no new block found")
                    elif depth < indent_stack[-1]:
                        # Look for line number
                        while depth < indent_stack[-1]:
                            yield DEDENT(token.lineno)
                            indent_stack.pop()
                        if depth != indent_stack[-1]:
                            raise IndentationError("Error 03!! Inconsistent indentation")
            except IndentationError as e:
                # Capture errors, but continue execution
                errors.append(f"Indentation Error at line {token.lineno}: {str(e)}")
                print(f"Indentation Error: {str(e)} at line {token.lineno}")
            
            pending_whitespace = None
        
        yield token
    
    # End with DEDENTS
    while len(indent_stack) > 1:
        yield DEDENT(token.lineno if token else 1)
        indent_stack.pop()

def final_indent(lexer, add_endmarker=True):
    tokens = iter(lexer.token, None)
    tokens = track_indent(lexer, tokens)
    
    for token in filter_indent(tokens):
        yield token
    
    if add_endmarker:
        yield _new_token_manual("ENDMARKER", lexer.lineno)

class IndentLexer(object):
    def __init__(self, debug=0, reflags=0):
        self.lexer = lex.lex(debug=debug, reflags=reflags)
        self.token_stream = None

    def input(self, s, add_endmarker=True):
        global indent_stack
        indent_stack = [0]  # Reset stack for each input
        self.lexer.input(s)
        self.token_stream = final_indent(self.lexer, add_endmarker)

    def token(self):
        try:
            return next(self.token_stream)
        except StopIteration:
            return None

lexer = IndentLexer()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: \n \t py lexer.py <filename>")
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
    
    # All errors found
    if errors:
        print("\n===== Resume: ALL ERRORS FOUND =====")
        for error in errors:
            print(error)