# Based on https://github.com/ThaisBarrosAlvim/mini-compiler-python/blob/master/src/lexer.py
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
        'None': 'NONE',
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

    tokens = reserved + (
        # Literals (identifier, integer constant, float constant, string constant, char const)'ID',
        'ID', 'NUMBER', 'SCONST',

        # Operators (+,-,*,/,%,<,>,<=,>=,==,!=,&&,||,!,=)
        'PLUS', 'MINUS', 'MULTI', 'DIVIDE', 'LPAREN', 'RPAREN', 'COMMA', 'SEMICOLON', 'COLON', 'EQUAL','NOTEQUAL', 'LESS',
        'LESSEQUAL', 'GREATER', 'GREATEREQUAL', 'ASSIGN', 'DOT', 'DOUBLEGREATER', 'DOUBLELESS', 'TRIPLELESS',
        'TRIPLEGREATER', 'LESSGREATER', 'TERNAL', 'LITERAL','LBRACKET','RBRACKET','LKEY','RKEY','INDENT','DEDENT','WHITESPACE','NEWLINE',
        'FDIVIDE', 'MODULE', 'POW', 'EQUALEQUAL', 'PLUSEQUAL', 'MINUSEQUAL', 'MULTIEQUAL', 'DIVEQUAL', 'MODULEEEQUAL', 'FDIVEQUAL', 'POWEQUAL',        
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
    t_MODULEEEQUAL = r'\%='
    t_FDIVEQUAL = r'//='
    t_POWEQUAL = r'\*\*='

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
        t.type = "NEWLINE"
        if t.lexer.paren_count == 0:
            return t

    def t_COMMENT(self, t): # Try with %
        r"""\b#.*"""
        pass

    def t_WHITESPACE(t):
        r'[ ]+'
        if t.lexer.at_line_start and t.lexer.paren_count == 0:
            return t
        
    def t_LPAREN(t):
        r'\('
        t.lexer.paren_count += 1
        return t
    
    def t_RPAREN(t):
        r'\)'
        t.lexer.paren_count += 1
        return t
    
    def t_error(self, t):
        self.errors.append(Error("Illegal character '%s'" % t.value[0], t.lineno, t.lexpos, 'lexer', self.data))
        print(self.errors[-1])
        t.lexer.skip(1)

    def build(self, ):
        self.lex = lex.lex(module=self)
    
