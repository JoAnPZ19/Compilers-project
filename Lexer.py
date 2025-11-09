# Based on https://github.com/ThaisBarrosAlvim/mini-compiler-python/blob/master/src/lexer.py
# and https://github.com/dabeaz/ply/blob/master/example/GardenSnake/GardenSnake.py 
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

tokens = [*reserved.values()] + [
    # Literals (identifier, integer constant, float constant, string constant, char const)
    'ID', 'NUMBER', 'SSTRING', 'DSTRING',

    # Operators (+,-,*,/,%,<,>,<=,>=,==,!=,&&,||,!,=)
    'PLUS', 'MINUS', 'MULTI', 'DIVIDE', 'LPAREN', 'RPAREN', 'COMMA', 'SEMICOLON', 
    'COLON', 'EQUAL', 'NOTEQUAL', 'LESS', 'LESSEQUAL', 'GREATER', 'GREATEREQUAL', 
    'ASSIGN', 'DOT', 'DOUBLEGREATER', 'DOUBLELESS', 'TRIPLELESS', 'DECIMAL',
    'TRIPLEGREATER', 'LESSGREATER', 'TERNAL', 'LITERAL', 'LBRACKET', 'RBRACKET',
    'LKEY', 'RKEY', 'WHITESPACE', 'NEWLINE', 'FDIVIDE', 'MODULE', 'POW', 
    'EQUALEQUAL', 'PLUSEQUAL', 'MINUSEQUAL', 'MULTIEQUAL', 'DIVEQUAL', 'MODEQUAL', 
    'FDIVEQUAL', 'POWEREQUAL', 'INDENT', 'DEDENT', 'ENDMARKER', 'QUOTATIONMARK',
    'DQUOTATIONMARK', 'UMINUS', 'COMMENT'       
]

# Regular expression rules for simple tokens

# Operators
t_DOUBLEGREATER = r'>>'
t_DOUBLELESS = r'<<'
t_TRIPLELESS = r'<<<'
t_TRIPLEGREATER = r'>>>'
t_LESSGREATER = r'<>'
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
t_TERNAL = r'\?'
t_FDIVIDE = r'//'
t_MODULE = r'\%'
t_POW = r'\*\*'
t_QUOTATIONMARK = r'\''
t_DQUOTATIONMARK = r'\"'

# String literal
t_DSTRING = r'\"([^\\\n]|(\\.))*?\"'
t_SSTRING = r"'([^\\\n]|(\\.))*?'"

def t_WHITESPACE(t):
    r'[ \t]+'
    if hasattr(t.lexer, 'at_line_start') and t.lexer.at_line_start:
        return t

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    setattr(t.lexer, "at_line_start", True)
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
    t_lower = t.value.lower()
    t.type = reserved.get(t_lower, 'ID')
    return t


def t_COMMENT(t):
    r'\#.*'
    return t

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
    # poner value = type para que p.value no sea None (mejor diagnóstico)
    tok.value = type
    tok.type = type
    tok.lineno = lineno if lineno is not None else (lexer.lineno if lexer else 0)
    return tok

def DEDENT(lineno):
    return _new_token_manual("DEDENT", lineno)

def INDENT(lineno):
    return _new_token_manual("INDENT", lineno)

def track_indent(lexer, tokens):
    """
    Tracks indentation state transitions and marks tokens that must be indented.
    """
    lexer.at_line_start = True
    indent_state = NO_INDENT

    for token in tokens:
        token.at_line_start = getattr(lexer, "at_line_start", False)
        token.must_indent = False

        if token.type == "COLON" or token.type == "LKEY":
            indent_state = MIGHT_INDENT
            lexer.at_line_start = False

        elif token.type == "NEWLINE":
            lexer.at_line_start = True
            if indent_state == MIGHT_INDENT:
                indent_state = MUST_INDENT
            elif indent_state == MUST_INDENT:
                indent_state = MUST_INDENT
            else:
                indent_state = NO_INDENT

        elif token.type == "WHITESPACE":
            pass

        else:
            if indent_state == MUST_INDENT:
                token.must_indent = True
            indent_state = NO_INDENT
            lexer.at_line_start = False

        yield token


def filter_indent(tokens, lexer):
    """
    Process tokens to handle Python-style indentation and dedentation.
    Emits INDENT/DEDENT tokens appropriately.
    """
    global indent_stack
    indent_stack = [0]
    pending_whitespace = None
    depth = 0
    last_token_type = None

    for token in tokens:
        if token is None:
            continue

        # Handle start-of-line whitespace
        if token.type == "WHITESPACE" and token.at_line_start:
            depth = len(token.value)
            pending_whitespace = token
            continue

        # Handle newline resets
        if token.type == "NEWLINE":
            depth = 0
            pending_whitespace = None
            yield token
            continue

        # If the previous token was a DEDENT, reset line start flags
        if last_token_type == "DEDENT":
            lexer.at_line_start = True
            depth = 0

        # Handle blank lines (whitespace + newline only)
        if token.type == "NEWLINE" and last_token_type == "NEWLINE":
            continue

        if token.at_line_start and pending_whitespace is None:
            # depth is already 0 (because of NEWLINE handling), but ensure it:
            depth = 0
            if depth < indent_stack[-1]:
                # Emit DEDENTs until stack matches current depth
                while depth < indent_stack[-1]:
                    yield DEDENT(token.lineno)
                    indent_stack.pop()
                # If after popping we don't match depth, it's an inconsistency:
                if depth != indent_stack[-1]:
                    msg = f"Inconsistent indentation at line {token.lineno}"
                    errors.append(msg)
                    print(msg)

        # Handle indentation logic before yielding next real token
        if pending_whitespace is not None:
            try:
                if token.must_indent:
                    if depth <= indent_stack[-1]:
                        raise IndentationError("Block must be indented")
                    indent_stack.append(depth)
                    yield INDENT(token.lineno)
                elif token.at_line_start:
                    # Same or dedented line
                    if depth > indent_stack[-1]:
                        raise IndentationError("Unexpected indentation increase")
                    while depth < indent_stack[-1]:
                        yield DEDENT(token.lineno)
                        indent_stack.pop()
                    if depth != indent_stack[-1]:
                        raise IndentationError("Inconsistent indentation")
            except IndentationError as e:
                msg = f"Indentation Error at line {token.lineno}: {str(e)}"
                errors.append(msg)
                print(msg)
            finally:
                pending_whitespace = None

        # Yield the actual token
        if token.type == "COMMENT":
            continue
        
        yield token
        last_token_type = token.type

    # At EOF: emit DEDENTs for any remaining indentation
    while len(indent_stack) > 1:
        yield DEDENT(token.lineno if token else 0)
        indent_stack.pop()



def final_indent(lexer, add_endmarker=True):
    tokens = iter(lexer.token, None)
    tokens = track_indent(lexer, tokens)
    
    for token in filter_indent(tokens, lexer):
        yield token
    
    if add_endmarker:
        end_token = _new_token_manual("ENDMARKER", lexer.lineno)
        end_token.value = ""
        yield end_token

class IndentLexer(object):
    def __init__(self, debug=0, reflags=0):
        self._inner = lex.lex(debug=debug, reflags=reflags)
        self.token_stream = None
        self._endmarker_emitted = False
        self.add_endmarker = True

    def input(self, s, add_endmarker=True):
        global indent_stack
        indent_stack = [0]  
        if s is None:
            s = ""
        if not s.endswith("\n"):
            s = s + "\n"
        self.add_endmarker = add_endmarker
        self._endmarker_emitted = False
        self._inner.input(s)
        self._inner.at_line_start = True

        self._inner.lineno = 1 
        self.token_stream = final_indent(self._inner, add_endmarker=False)

    def token(self):
        try:
            tok = next(self.token_stream)
            return tok
        except StopIteration:
            if not self._endmarker_emitted and self.add_endmarker:
                self._endmarker_emitted = True
                end_tok = _new_token_manual("ENDMARKER", getattr(self._inner, "lineno", 0), lexer=self._inner)
                return end_tok
            return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lexer for Python-like language")
    parser.add_argument("-f", "--file", type=str, help="Input file to tokenize")
    parser.add_argument("-t", "--text", type=str, help="Input text to tokenize")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = f.read()
    elif args.text:
        data = args.text
    else:
        print("Usage:\n\tpy lexer.py -f <filename>\n\tpy lexer.py -t <text>")
        sys.exit(1)

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
