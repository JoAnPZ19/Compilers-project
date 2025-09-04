# Based on https://github.com/ThaisBarrosAlvim/mini-compiler-python/blob/master/src/lexer.py
import ply.lex as lex
import sys

class Error:
    def __init__(self, message, lineno, lexpos, source="lexer", data=None):
        self.message = message
        self.lineno = lineno
        self.lexpos = lexpos
        self.source = source
        self.data = data

    def __str__(self):
        return f"[{self.source.upper()} ERROR] {self.message} (line {self.lineno}, position {self.lexpos})"
    

class Lexer:

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
        'LESSEQUAL', 'GREATER', 'GREATEREQUAL', 'ASSIGN', 'DOT', 'DOUBLEGREATER', 'DOUBLELESS', 'TRIPLELESS',
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

    def __init__(self, debug=False):
        self.debug = debug
        self.errors = []
        self.reserved_map = {k.lower(): v for k, v in self.reserved.items()}
        self.lexer = None
        self.paren_count = 0
        self.at_line_start = True

    # Identifiers and reserved words
    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        t.type = self.reserved_map.get(t.value.lower(), 'ID')
        return t

    # Numbers
    def t_DECIMAL(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    # Comments
    def t_COMMENT(self, t):
        r'\#.*'
        pass

    # Newlines
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        self.at_line_start = True
        return t

    # Error handling
    def t_error(self, t):
        self.errors.append(Error(f"Illegal character '{t.value[0]}'", t.lineno, t.lexpos))
        print(self.errors[-1])
        t.lexer.skip(1)

    # Build lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        self.lexer.paren_count = 0
        self.lexer.at_line_start = True

    def input(self, data):
        self.lexer.input(data)

    def token(self):
        return self.lexer.token()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python lexer_complete.py <filename>")
        sys.exit(1)

    file = sys.argv[1]
    with open(file, "r", encoding="utf-8") as f:
        data = f.read()

    lexer_instance = Lexer()
    lexer_instance.build()
    lexer_instance.input(data)

    while True:
        tok = lexer_instance.token()
        if not tok:
            break
        print(tok)