# Based on https://github.com/ThaisBarrosAlvim/mini-compiler-python/blob/master/src/lexer.py
import ply.yacc as yacc
import Lexer

tokens = Lexer.tokens

class Node:
    def __init__(self, type_, value=None, children=None):
        self.type = type_
        self.value = value
        self.children = children or []

    def __repr__(self, level=0):
        indent = "  " * level
        s = f"{indent}{self.type}: {self.value if self.value is not None else ''}\n"
        for child in self.children:
            if isinstance(child, Node):
                s += child.__repr__(level + 1)
            else:
                s += "  " * (level + 1) + repr(child) + "\n"
        return s

class Parser:
    def __init__(self, debug=False):
        self.errors = []
        self.data = None
        self.debug = debug
        self.tokens = tokens
        self.lexer = Lexer.IndentLexer(debug=self.debug)
        self.precedence = (
            ('left', 'OR'),
            ('left', 'AND'),
            ('left', 'NOT'),
            ('left', 'EQUAL', 'NOTEQUAL', 'LESS', 'GREATER', 'GREATEREQUAL', 'LESSEQUAL', 'IN', 'IS'),
            ('left', 'PLUS', 'MINUS'),
            ('left', 'MULTI', 'DIVIDE', 'MODULE', 'FDIVIDE'),
            ('left', 'POW'),
            ('right', 'UMINUS'),
        )

    def p_error(self, p):
        if not p:
            error_msg = f"Unexpected end of input"
            self.errors.append(error_msg)
        else:
            error_msg = f"Syntax error on '{p.value}' at line {p.lineno}"
            self.errors.append(error_msg)
        print(f"Parser Error: {error_msg}")

    def parse_data(self, data):
        self.data = data
        self.lexer.input(data)
        result = self.parser.parse(lexer=self.lexer)
        return result

    def build(self):
        self.parser = yacc.yacc(module=self, debug=self.debug)

    # Main module
    def p_module(self, p):
        """module : statements"""
        p[0] = Node("module", None, p[1])

    # Statements
    def p_statements(self, p):
        """statements : statement
                      | statements statement"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    # Individual statement
    def p_statement(self, p):
        """statement : simple_statement NEWLINE
                     | compound_statement
                     | NEWLINE"""
        if len(p) == 3:
            p[0] = p[1]
        elif len(p) == 2 and p[1] is not None:
            p[0] = p[1]
        else:
            p[0] = Node("pass")

    # Simple statements
    def p_simple_statement(self, p):
        """simple_statement : expression_statement
                           | assignment_statement
                           | return_statement
                           | pass_statement"""
        p[0] = p[1]

    # Compound statements
    def p_compound_statement(self, p):
        """compound_statement : function_def
                             | if_statement
                             | while_statement
                             | for_statement"""
        p[0] = p[1]

    # Def function
    def p_function_def(self, p):
        """function_def : DEF ID LPAREN parameters RPAREN COLON suite"""
        p[0] = Node("function_def", p[2], [Node("parameters", None, p[4]), p[7]])

    def p_parameters(self, p):
        """parameters : parameter_list
                      | empty"""
        if p[1] is None:
            p[0] = []
        else:
            p[0] = p[1]

    def p_parameter_list(self, p):
        """parameter_list : ID
                         | parameter_list COMMA ID"""
        if len(p) == 2:
            p[0] = [Node("parameter", p[1])]
        else:
            p[0] = p[1] + [Node("parameter", p[3])]

    # Suite
    def p_suite(self, p):
        """suite : NEWLINE INDENT statements DEDENT
                 | simple_statement NEWLINE"""
        if len(p) == 5:
            p[0] = Node("suite", None, p[3])
        else:
            p[0] = Node("suite", None, [p[1]])

    # Statement if
    def p_if_statement(self, p):
        """if_statement : IF expression COLON suite
                       | IF expression COLON suite elif_clauses
                       | IF expression COLON suite elif_clauses ELSE COLON suite"""
        if len(p) == 5:
            p[0] = Node("if", None, [p[2], p[4]])
        elif len(p) == 6:
            p[0] = Node("if", None, [p[2], p[4], p[5]])
        else:
            p[0] = Node("if", None, [p[2], p[4], p[5], p[8]])

    def p_elif_clauses(self, p):
        """elif_clauses : elif_clause
                       | elif_clauses elif_clause"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_elif_clause(self, p):
        """elif_clause : ELIF expression COLON suite"""
        p[0] = Node("elif", None, [p[2], p[4]])

    # Statement while
    def p_while_statement(self, p):
        """while_statement : WHILE expression COLON suite"""
        p[0] = Node("while", None, [p[2], p[4]])

    # Statement for
    def p_for_statement(self, p):
        """for_statement : FOR ID IN expression COLON suite"""
        p[0] = Node("for", None, [Node("target", p[2]), p[4], p[6]])

    # Return statement
    def p_return_statement(self, p):
        """return_statement : RETURN
                           | RETURN expression"""
        if len(p) == 2:
            p[0] = Node("return")
        else:
            p[0] = Node("return", None, [p[2]])

    # Pass statement
    def p_pass_statement(self, p):
        """pass_statement : PASS"""
        p[0] = Node("pass")

    # Assignment
    def p_assignment_statement(self, p):
        """assignment_statement : ID EQUAL expression"""
        p[0] = Node("assignment", p[1], [p[3]])

    # Expression statement
    def p_expression_statement(self, p):
        """expression_statement : expression"""
        p[0] = Node("expression_stmt", None, [p[1]])

    # Expresiones
    def p_expression(self, p):
        """expression : binary_expression
                     | unary_expression
                     | comparison_expression
                     | boolean_expression
                     | primary"""
        p[0] = p[1]

    def p_binary_expression(self, p):
        """binary_expression : expression PLUS expression
                           | expression MINUS expression
                           | expression MULTI expression
                           | expression DIVIDE expression
                           | expression FDIVIDE expression
                           | expression MODULE expression
                           | expression POW expression"""
        p[0] = Node("binary_op", p[2], [p[1], p[3]])

    def p_unary_expression(self, p):
        """unary_expression : MINUS expression %prec UMINUS
                           | NOT expression"""
        p[0] = Node("unary_op", p[1], [p[2]])

    def p_comparison_expression(self, p):
        """comparison_expression : expression EQUAL expression
                               | expression NOTEQUAL expression
                               | expression LESS expression
                               | expression GREATER expression
                               | expression LESSEQUAL expression
                               | expression GREATEREQUAL expression"""
        p[0] = Node("comparison", p[2], [p[1], p[3]])

    def p_boolean_expression(self, p):
        """boolean_expression : expression AND expression
                            | expression OR expression"""
        p[0] = Node("boolean_op", p[2], [p[1], p[3]])

    # Primary expressions
    def p_primary(self, p):
        """primary : atom
                  | primary LPAREN arguments RPAREN
                  | primary LBRACKET expression RBRACKET"""
        if len(p) == 2:
            p[0] = p[1]
        elif p[2] == '(':
            p[0] = Node("call", p[1].value if hasattr(p[1], 'value') else None, p[3])
        else:
            p[0] = Node("subscript", None, [p[1], p[3]])

    def p_arguments(self, p):
        """arguments : expression_list
                    | empty"""
        if p[1] is None:
            p[0] = []
        else:
            p[0] = p[1]

    def p_expression_list(self, p):
        """expression_list : expression
                          | expression_list COMMA expression"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    # Atoms
    def p_atom(self, p):
        """atom : ID
               | NUMBER
               | DECIMAL
               | SSTRING
               | DSTRING
               | TRUE
               | FALSE
               | NONE
               | LPAREN expression RPAREN"""
        if len(p) == 2:
            if p.slice[1].type == 'ID':
                p[0] = Node("identifier", p[1])
            elif p.slice[1].type in ('NUMBER', 'DECIMAL'):
                p[0] = Node("number", p[1])
            elif p.slice[1].type in ('SSTRING', 'DSTRING'):
                p[0] = Node("string", p[1])
            elif p.slice[1].type in ('TRUE', 'FALSE'):
                p[0] = Node("boolean", p[1])
            elif p.slice[1].type == 'NONE':
                p[0] = Node("none")
        else:
            p[0] = p[2]

    def p_empty(self, p):
        """empty :"""
        p[0] = None

    def parse(self, source, debug=False):
        self.errors = []
        self.lexer.input(source)
        result = self.parser.parse(lexer=self.lexer, debug=debug)
        return result

# Test fx
def test_parser():
    test_code = """
def random_operation(a, b):
    return a * b + 2.6548

def fibonacci(n):
    if n == 1 or n == 2:
        return 1
    elif n == 0:
        return n / 0
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)
"""

    parser = Parser(debug=False)
    parser.build()
    ast = parser.parse(test_code)
    
    print("=== AST ===")
    print(ast)
    
    if parser.errors:
        print("\n=== ERRORES ===")
        for error in parser.errors:
            print(error)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        with open(filename, "r", encoding="utf-8") as f:
            src = f.read()
        
        parser = Parser(debug=False)
        parser.build()
        ast = parser.parse(src)
        print("\n=== AST ===")
        print(ast)
        
        if parser.errors:
            print("\n=== ERRORES ===")
            for error in parser.errors:
                print(error)
    else:
        test_parser()

