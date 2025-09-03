import ply.lex as lex

from src.utils import Error
from src.symbol_table import SymbolTable

class Lexer:
    def __init__(self, errors: list[Error], debug=False):
        self.lex = None
        self.data = None
        self.debug = debug
        self.symbol_table = SymbolTable()
        self.reserved_map = {}
        self.errors = errors  # to use the same list of errors that the parser uses
        for r in self.reserved:
            self.reserved_map[r.lower()] = r

    reserved = {
        'false': 'FALSE',
        'None': 'NONE',
        'true': 'TRUE',
        'and': 'AND',
        'as': 'AS',
        'assert': 'ASSERT',
        'async': 'ASYNC',
        'await': 'AWAIT',
        'break': 'BREAK',
        'class': 'CLASS',
        'continue': 'CONTINUE',
        'def': 'DEF',
        'do': 'DO',
        'elif': 'ELIF',
        'else': 'ELSE',
        'except': 'EXCEPT',
        'finally': 'FINALLY',
        'for': 'FOR',
        'from': 'FROM',
        'begin': 'BEGIN',
        'if': 'IF',
        'end': 'END',
        'in': 'IN',
        'is': 'IS',
        'read': 'READ',
        'to': 'TO',
        'not': 'NOT',
        'or': 'OR',
        'pass': 'PASS',
        'then': 'THEN',
        'return': 'RETURN',
        'try': 'TRY',
        'while': 'WHILE',
        'write': 'WRITE',
        'yield': 'YIELD',
    }

    tokens = reserved + (
        # Literals (identifier, integer constant, float constant, string constant, char const)'ID',
        'ID', 'NUMBER', 'SCONST',

        # Operators (+,-,*,/,%,<,>,<=,>=,==,!=,&&,||,!,=)
        'PLUS', 'MINUS', 'MULTI', 'DIVIDE', 'LPAREN', 'RPAREN', 'COMMA', 'SEMICOLON', 'COLON', 'EQUAL','NOTEQUAL', 'LESS',
        'LESSEQUAL', 'GREATER', 'GREATEREQUAL', 'ASSIGN', 'DOT', 'DOUBLEGREATER', 'DOUBLELESS', 'TRIPLELESS',
        'TRIPLEGREATER', 'LESSGREATER', 'TERNAL', 'LITERAL','LBRACKET','RBRACKET','LKEY','RKEY','INDENT','DEDENT','WHITESPACE','NEWLINE'
    )
    # Regular expression rules for simple tokens

    # Operators
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_MULTI = r'\*'
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
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

    # String literal
    t_SCONST = r'\"([^\\\n]|(\\.))*?\"'

    t_ignore = ' \t'


    def __init__(self):
        #Detecting DEDENT by INDENT stack
        self.indent_stack = [0]

    def t_ID(self, t):
        r"""[a-zA-Z_][a-zA-Z0-9_]*"""
        if self.debug:
            print(f'DEBUG(LEXER): {t.value.upper()} on line {t.lineno}, position {t.lexpos}')
        t.type = self.reserved_map.get(t.value, 'ID')
        return t

    def t_NUMBER(self, t):
        r"""\d+"""
        t.value = int(t.value)
        return t

    def t_DECIMAL(self, t):
        r"""\d+\.\d+"""
        t.value = float(t.value)
        return t

    def t_LITERAL(self, t):
        r"""\"[^"]*\\"""
        return t

    def t_NEWLINE(self, t):
        r"""\n+"""
        t.lexer.lineno += len(t.value)

    def t_COMMENT(self, t):
        r"""\%.*"""
        pass
    def t_WHITESPACE(t):
        r'[ ]+'
        if t.lexer.at_line_start and t.lexer.paren_count == 0:
            return t
    def t_error(self, t):
        self.errors.append(Error("Illegal character '%s'" % t.value[0], t.lineno, t.lexpos, 'lexer', self.data))
        print(self.errors[-1])
        t.lexer.skip(1)

    def build(self, ):
        self.lex = lex.lex(module=self)
    
