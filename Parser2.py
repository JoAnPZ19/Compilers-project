# Based on https://github.com/ThaisBarrosAlvim/mini-compiler-python/blob/master/src/lexer.py
import ply.yacc as yacc
import Lexer
import os

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
            ("left", "OR"),
            ("left", "AND"),
            ("left", "NOT"),
            ("left", "EQUALEQUAL", "NOTEQUAL", "LESS", "GREATER", "GREATEREQUAL", "LESSEQUAL", "IN", "IS"),
            ("left", "PLUS", "MINUS"),
            ("left", "MULTI", "DIVIDE", "MODULE", "FDIVIDE"),
            ("left", "POW"),
            ("right", "UMINUS"),
        )

      
    def p_error(self, p):
        if not p:
            error_msg = f"Unexpected end of input"
        else:
            # El error "Syntax error on 'None'" es por DEDENT sin manejar.
            error_msg = f"Syntax error on '{p.value}' (type {p.type}) at line {p.lineno}"
        
        self.errors.append(error_msg)
        print(f"Parser Error: {error_msg}")
        
        # Modo de recuperación simple: saltar el token y continuar
        if p and p.type != 'ENDMARKER':
            self.parser.errok()
            # No se hace p.lexer.skip(1) porque el lexer es una clase wrapper
        else:
             raise Exception("End of input reached")

    def build(self):
        for f in ("parsetab.py", "parser.out"):
            if os.path.exists(f):
                os.remove(f)
        self.parser = yacc.yacc(module=self, debug=self.debug, start='module', write_tables=True)
        

    def parse_data(self, data):
        self.data = data
        self.lexer.input(data)
        result = self.parser.parse(lexer=self.lexer.lexer)
        print(f"Result of parse_data: {result}")
        return result

    def parse(self, source, debug=False):
        self.errors = []
        self.lexer.input(source)
        result = self.parser.parse(lexer=self.lexer, debug=debug)
        print(result)
        return result

    # === MODULE ===
    def p_module(self, p):
        """module : statements optional_end"""
        p[0] = Node("module", None, p[1])
        if self.debug:
            print("Module parsed successfully")

    def p_optional_end(self, p):
        """optional_end : end_token optional_end
                        | empty"""
        p[0] = None


    def p_end_token(self, p):
        """end_token : NEWLINE
                     | DEDENT
                     | ENDMARKER"""
        p[0] = None



    # === STATEMENTS ===
    def p_statements(self, p):
        """statements : statement
                      | statements statement"""
        if len(p) == 2:
            # Inicializa la lista solo si el statement no es de control de flujo (pass)
            p[0] = [p[1]] if p[1].type != "pass" else []
        else:
            # Agrega solo si el statement no es de control de flujo
            if p[2].type == "pass":
                p[0] = p[1]
            else:
                p[0] = p[1] + [p[2]]

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

    # === SIMPLE STATEMENTS ===
    def p_simple_statement(self, p):
        """simple_statement : expression_statement
                           | assignment_statement
                           | return_statement
                           | pass_statement"""
        p[0] = p[1]

    # === COMPOUND STATEMENTS ===
    def p_compound_statement(self, p):
        """compound_statement : function_def
                             | if_statement
                             | while_statement
                             | for_statement"""
        p[0] = p[1]

    # === FUNCTION DEF ===
    def p_function_def(self, p):
        """function_def : DEF ID LPAREN parameters RPAREN COLON suite"""
        p[0] = Node("function_def", p[2], [Node("parameters", None, p[4]), p[7]])

    def p_parameters(self, p):
        """parameters : parameter_list
                      | empty"""
        p[0] = [] if p[1] is None else p[1]

    def p_parameter_list(self, p):
        """parameter_list : ID
                         | parameter_list COMMA ID"""
        if len(p) == 2:
            p[0] = [Node("parameter", p[1])]
        else:
            p[0] = p[1] + [Node("parameter", p[3])]

    # === SUITE ===
    def p_suite(self, p):
        """suite : NEWLINE INDENT statements DEDENT
                 | simple_statement NEWLINE"""
        if len(p) == 5:
            p[0] = Node("suite", None, p[3])
        else:
            p[0] = Node("suite", None, [p[1]])

    # === IF / ELIF / ELSE ===
    def p_if_statement(self, p):
        """if_statement : IF expression COLON suite elif_clauses else_clause"""
        children = [p[2], p[4]]
        if p[5] is not None:
            children.extend(p[5])
        if p[6] is not None:
            children.append(p[6])
        p[0] = Node("if", None, children)

    def p_elif_clauses(self, p):
        """elif_clauses : elif_clause_list
                        | empty"""
        p[0] = p[1]

    def p_elif_clause_list(self, p):
        """elif_clause_list : elif_clause
                            | elif_clause_list elif_clause"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_elif_clause(self, p):
        """elif_clause : ELIF expression COLON suite"""
        p[0] = Node("elif", None, [p[2], p[4]])

    def p_else_clause(self, p):
        """else_clause : ELSE COLON suite
                       | empty"""
        if len(p) == 4:
            p[0] = Node("else", None, [p[3]])
        else:
            p[0] = None

    # === WHILE ===
    def p_while_statement(self, p):
        """while_statement : WHILE expression COLON suite"""
        p[0] = Node("while", None, [p[2], p[4]])

    # === FOR ===
    def p_for_statement(self, p):
        """for_statement : FOR ID IN expression COLON suite"""
        p[0] = Node("for", None, [Node("target", p[2]), p[4], p[6]])

    # === RETURN ===
    def p_return_statement(self, p):
        """return_statement : RETURN
                           | RETURN expression"""
        if len(p) == 2:
            p[0] = Node("return")
        else:
            p[0] = Node("return", None, [p[2]])

    # === PASS ===
    def p_pass_statement(self, p):
        """pass_statement : PASS"""
        p[0] = Node("pass")

    # === ASSIGNMENT ===
    def p_assignment_statement(self, p):
        """assignment_statement : ID EQUAL expression"""
        p[0] = Node("assignment", p[1], [p[3]])

    # === EXPRESSION STATEMENT ===
    def p_expression_statement(self, p):
        """expression_statement : expression"""
        p[0] = Node("expression_stmt", None, [p[1]])

    # === EXPRESSIONS ===
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
        """comparison_expression : expression EQUALEQUAL expression
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

    # === PRIMARY EXPRESSIONS ===
    def p_primary(self, p):
        """primary : atom
                  | primary LPAREN arguments RPAREN
                  | primary LBRACKET expression RBRACKET"""
        if len(p) == 2:
            p[0] = p[1]
        elif p[2] == "(":
            p[0] = Node("call", getattr(p[1], "value", None), p[3])
        else:
            p[0] = Node("subscript", None, [p[1], p[3]])

    def p_arguments(self, p):
        """arguments : expression_list
                    | empty"""
        p[0] = [] if p[1] is None else p[1]

    def p_expression_list(self, p):
        """expression_list : expression
                          | expression_list COMMA expression"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    # === ATOMS ===
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
            t = p.slice[1].type
            if t == "ID":
                p[0] = Node("identifier", p[1])
            elif t in ("NUMBER", "DECIMAL"):
                p[0] = Node("number", p[1])
            elif t in ("SSTRING", "DSTRING"):
                p[0] = Node("string", p[1])
            elif t in ("TRUE", "FALSE"):
                p[0] = Node("boolean", p[1])
            elif t == "NONE":
                p[0] = Node("none")
        else:
            p[0] = p[2]

    def p_empty(self, p):
        """empty :"""
        p[0] = None


# === TEST DRIVER ===
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
        for e in parser.errors:
            print(e)

'''
if __name__ == "__main__":
    import sys
    tokens_parser = []
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        with open(filename, "r", encoding="utf-8") as f:
            src = f.read()

        parser = Parser(debug=False)
        parser.build()

        parser.lexer.input(src)
        tok = parser.lexer.token()
        while tok:
            tokens_parser.append(tok)
            print(tok)
            tok = parser.lexer.token()

        print(f"real tokens: {tokens_parser}")

        parser.lexer.input(src)
        ast = parser.parse(src)
        print("\n=== AST ===")
        print(ast)

        if parser.errors:
            print("\n=== ERRORES ===")
            for e in parser.errors:
                print(e)
    else:
        test_parser()
'''

if __name__ == "__main__":
    # ... (código de prueba del driver) ...
    import sys
    tokens_parser = []
    
    if len(sys.argv) > 1:
        # Modo de archivo: lee el archivo y lo parsea
        filename = sys.argv[1]
        try:
            with open(filename, "r", encoding="utf-8") as f:
                src = f.read()

            parser = Parser(debug=False)
            parser.build()

            # Primera pasada: imprimir tokens (para debugging)
            parser.lexer.input(src)
            tok = parser.lexer.token()
            while tok:
                tokens_parser.append(tok)
                print(tok)
                tok = parser.lexer.token()

            #print(f"real tokens: {tokens_parser}")

            # Segunda pasada: parsear
            parser.lexer.input(src)
            ast = parser.parser.parse(lexer=parser.lexer.lexer)
            
            print("\n=== AST ===")
            print(ast)

            if parser.errors:
                print("\n=== ERRORES ===")
                for e in parser.errors:
                    print(e)
            
        except FileNotFoundError:
             print(f"Error: File not found {filename}")
        except Exception as e:
             print(f"An unexpected error occurred: {e}")

    else:
        test_parser()