# Parser.py (reemplaza completamente tu Parser.py con este contenido)
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

        # precedence (some operators grouped)
        self.precedence = (
            ('left', 'OR'),
            ('left', 'AND'),
            ('left', 'NOT'),
            ('left', 'EQUALEQUAL', 'NOTEQUAL', 'LESS', 'GREATER', 'GREATEREQUAL', 'LESSEQUAL', 'IN', 'IS'),
            ('left', 'PLUS', 'MINUS'),
            ('left', 'MULTI', 'DIVIDE', 'MODULE', 'FDIVIDE'),
            ('left', 'POW'),
            ('right', 'UMINUS'),
        )

    def p_error(self, p):
        if not p:
            msg = "Unexpected end of input"
            self.errors.append(msg)
            print(f"Parser Error: {msg}")
            return
        tok_type = getattr(p, "type", None)
        tok_val  = getattr(p, "value", None)
        lineno   = getattr(p, "lineno", getattr(p, "lineno", "?"))
        msg = f"Syntax error on token type='{tok_type}' value={repr(tok_val)} at line {lineno}"
        self.errors.append(msg)
        print(f"Parser Error: {msg}")

    def build(self):
        for f in ("parsetab.py", "parser.out"):
            if os.path.exists(f):
                os.remove(f)
        self.parser = yacc.yacc(module=self, debug=self.debug, start='module', write_tables=True)

    def parse(self, source, debug=False):
        self.errors = []
        self.lexer.input(source)
        result = self.parser.parse(lexer=self.lexer, debug=debug)
        return result

    # ---- Grammar ----

    def p_module(self, p):
        """module : statements optional_dedents
                  | optional_dedents
                  | statements optional_dedents ENDMARKER"""
        if len(p) == 2:
            # only optional dedents or empty
            p[0] = Node("module", None, [])
        else:
            p[0] = Node("module", None, p[1])

    def p_optional_dedents(self, p):
        """optional_dedents :
                         | DEDENT optional_dedents"""
        p[0] = None

    def p_optional_newlines(self, p):
        """optional_newlines :
                            | NEWLINE optional_newlines"""
        p[0] = None

    def p_optional_indents(self, p):
        """optional_indents :
                            | INDENT optional_indents"""
        p[0] = None

    # statements: one or more statements
    def p_statements(self, p):
        """statements : statement
                      | statements statement"""
        if len(p) == 2:
            p[0] = [p[1]]
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

    def p_simple_statement(self, p):
        """simple_statement : expression_statement
                            | assignment_statement
                            | return_statement
                            | pass_statement"""
        p[0] = p[1]

    def p_compound_statement(self, p):
        """compound_statement : function_def
                              | if_statement
                              | while_statement
                              | for_statement"""
        p[0] = p[1]

    
    # suite: either simple_statement NEWLINE or indented block
    def p_suite(self, p):
        """suite : simple_statement NEWLINE
                | NEWLINE INDENT statements optional_dedents
                | INDENT statements optional_dedents
                | NEWLINE INDENT DEDENT"""
        if len(p) == 3 and isinstance(p[1], Node):
            p[0] = Node("suite", None, [p[1]])
        elif len(p) in (5, 4):
            stmts = p[2] if len(p) == 4 else p[3]
            p[0] = Node("suite", None, stmts if isinstance(stmts, list) else [stmts])
        else:
            p[0] = Node("suite", None, [])


    # function definition
    def p_function_def(self, p):
        """function_def : DEF ID LPAREN parameters RPAREN COLON suite"""
        p[0] = Node("function_def", p[2], [Node("parameters", None, p[4]), p[7]])

    def p_parameters(self, p):
        """parameters :
                      | parameter_list"""
        if len(p) == 1:
            p[0] = []
        else:
            p[0] = p[1]

    def p_parameter_list(self, p):
        """parameter_list : parameter
                          | parameter_list COMMA parameter"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_parameter(self, p):
        """parameter : ID
                     | ID EQUAL expression"""
        if len(p) == 2:
            p[0] = Node("parameter", p[1])
        else:
            p[0] = Node("parameter", p[1], [p[3]])



    # if / elif / else
    def p_if_statement(self, p):
        """if_statement : IF expression COLON suite
                        | IF expression COLON suite elif_clauses
                        | IF expression COLON suite ELSE COLON suite
                        | IF expression COLON suite elif_clauses ELSE COLON suite"""
        if len(p) == 5:
            p[0] = Node("if", None, [p[2], p[4]])
        elif len(p) == 7:
            # with elif_clauses
            p[0] = Node("if", None, [p[2], p[4], p[5]])
        elif len(p) == 8 and p.slice[5].type == 'ELSE':
            p[0] = Node("if", None, [p[2], p[4], p[7]])
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

    def p_while_statement(self, p):
        """while_statement : WHILE expression COLON suite"""
        p[0] = Node("while", None, [p[2], p[4]])

    # for: target can be any expression (more flexible)
    def p_for_statement(self, p):
        """for_statement : FOR expression IN expression COLON suite"""
        p[0] = Node("for", None, [p[2], p[4], p[6]])

    # return / pass
    def p_return_statement(self, p):
        """return_statement : RETURN
                            | RETURN expression"""
        if len(p) == 2:
            p[0] = Node("return")
        else:
            p[0] = Node("return", None, [p[2]])

    def p_pass_statement(self, p):
        """pass_statement : PASS"""
        p[0] = Node("pass")

    # assignment
    def p_assignment_statement(self, p):
        """assignment_statement : ID EQUAL expression"""
        p[0] = Node("assignment", p[1], [p[3]])

    # expression statement
    def p_expression_statement(self, p):
        """expression_statement : expression"""
        p[0] = Node("expression_stmt", None, [p[1]])

    # --- expressions ---
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
                                | expression GREATEREQUAL expression
                                | expression IN expression
                                | expression IS expression"""
        p[0] = Node("comparison", p[2], [p[1], p[3]])

    def p_boolean_expression(self, p):
        """boolean_expression : expression AND expression
                              | expression OR expression"""
        p[0] = Node("boolean_op", p[2], [p[1], p[3]])

    # primary: atoms, calls, indexing, attributes
    def p_primary(self, p):
        """primary : atom
                | primary LPAREN arguments RPAREN
                | primary LBRACKET subscript_item RBRACKET
                | primary DOT ID"""
        if len(p) == 2:
            p[0] = p[1]
        elif p.slice[2].type == 'LPAREN':
            func_node = p[1]
            args = p[3] if p[3] is not None else []
            name = func_node.value if isinstance(func_node, Node) and func_node.type == "identifier" else None
            p[0] = Node("call", name, args)
        elif p.slice[2].type == 'LBRACKET':
            p[0] = Node("subscript", None, [p[1], p[3]])
        else:
            p[0] = Node("attribute", p[3], [p[1]])


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

    # subscript item (index or slice)
    def p_subscript_item(self, p):
        """subscript_item : expression
                          | slice"""
        p[0] = p[1]

    def p_slice(self, p):
        """slice : expression COLON expression
                 | COLON expression
                 | expression COLON
                 | COLON"""
        if len(p) == 4:
            p[0] = Node("slice", None, [p[1], p[3]])
        elif len(p) == 3:
            if p.slice[1].type == 'COLON':
                p[0] = Node("slice", None, [None, p[2]])
            else:
                p[0] = Node("slice", None, [p[1], None])
        else:
            p[0] = Node("slice", None, [None, None])

    # atoms and literals
    def p_atom(self, p):
        """atom : ID
               | NUMBER
               | DECIMAL
               | SSTRING
               | DSTRING
               | TRUE
               | FALSE
               | NONE
               | LPAREN paren_contents RPAREN"""
        if len(p) == 2:
            ttype = p.slice[1].type
            if ttype == 'ID':
                p[0] = Node("identifier", p[1])
            elif ttype in ('NUMBER', 'DECIMAL'):
                p[0] = Node("number", p[1])
            elif ttype in ('SSTRING', 'DSTRING'):
                p[0] = Node("string", p[1])
            elif ttype in ('TRUE', 'FALSE'):
                p[0] = Node("boolean", p[1])
            elif ttype == 'NONE':
                p[0] = Node("none")
        else:
            p[0] = p[2]

    def p_paren_contents(self, p):
        """paren_contents : expression
                          | expression_list
                          | expression_list COMMA"""

        if len(p) == 2:
            if isinstance(p[1], list):
                if len(p[1]) == 1:
                    p[0] = p[1][0]
                else:
                    p[0] = Node("tuple", None, p[1])
            else:
                p[0] = p[1]
        else:
            lst = p[1] if isinstance(p[1], list) else [p[1]]
            p[0] = Node("tuple", None, lst)

# ---- Literales con soporte para forma multilínea con INDENT/DEDENT ----

    def p_dict_literal(self, p):
        """atom : LKEY dict_pairs RKEY
                | LKEY NEWLINE INDENT dict_pairs NEWLINE DEDENT RKEY"""
        # Inline: { a: b, ... }
        if len(p) == 4:
            p[0] = Node("dict", None, p[2])
        else:
            # Multilínea: { \n INDENT dict_pairs NEWLINE DEDENT }
            p[0] = Node("dict", None, p[5])

    def p_dict_pairs(self, p):
        """dict_pairs : empty
                    | dict_pair
                    | dict_pairs COMMA dict_pair
                    | dict_pairs NEWLINE dict_pair
                    | dict_pairs COMMA NEWLINE dict_pair
                    | dict_pairs COMMA"""
        if p[1] is None:
            p[0] = []
        elif len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 3:
            # trailing comma
            p[0] = p[1]
        elif len(p) == 4:
            # dict_pairs COMMA dict_pair  OR dict_pairs NEWLINE dict_pair
            p[0] = p[1] + [p[3]]
        else:
            # dict_pairs COMMA NEWLINE dict_pair
            p[0] = p[1] + [p[4]]

    def p_dict_pair(self, p):
        """dict_pair : expression COLON expression"""
        p[0] = Node("pair", None, [p[1], p[3]])


    def p_list_literal(self, p):
        """atom : LBRACKET list_items RBRACKET
                | LBRACKET NEWLINE INDENT list_items NEWLINE DEDENT RBRACKET"""
        if len(p) == 4:
            p[0] = Node("list", None, p[2])
        else:
            p[0] = Node("list", None, p[5])

    def p_list_items(self, p):
        """list_items : empty
                    | expression
                    | list_items COMMA expression
                    | list_items NEWLINE expression
                    | list_items COMMA NEWLINE expression
                    | list_items COMMA"""
        if p[1] is None:
            p[0] = []
        elif len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 3:
            p[0] = p[1]   # trailing comma
        elif len(p) == 4:
            p[0] = p[1] + [p[3]]
        else:
            p[0] = p[1] + [p[4]]


    def p_set_literal(self, p):
        """atom : LKEY set_items RKEY
                | LKEY NEWLINE INDENT set_items NEWLINE DEDENT RKEY"""
        if len(p) == 4:
            p[0] = Node("set", None, p[2])
        else:
            p[0] = Node("set", None, p[5])

    def p_set_items(self, p):
        """set_items : empty
                    | expression
                    | set_items COMMA expression
                    | set_items NEWLINE expression
                    | set_items COMMA NEWLINE expression
                    | set_items COMMA"""
        if p[1] is None:
            p[0] = []
        elif len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 3:
            p[0] = p[1]
        elif len(p) == 4:
            p[0] = p[1] + [p[3]]
        else:
            p[0] = p[1] + [p[4]]



    def p_empty(self, p):
        """empty :"""
        p[0] = None


# ---- Test helper ----
def test_parser():
    code = """
def random_operation(a, b):
    c = a + b
    # Hi I'm a comment!
    return c + a * b + 2.6548
"""
    parser = Parser(debug=False)
    parser.build()
    ast = parser.parse(code)
    print("=== AST ===")
    print(ast)
    if parser.errors:
        print("\n=== ERRORES ===")
        for e in parser.errors:
            print(e)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        with open(fname, "r", encoding="utf-8") as f:
            src = f.read()
        parser = Parser(debug=False)
        parser.build()

        # print tokens for debugging
        parser.lexer.input(src)
        tok = parser.lexer.token()
        while tok:
            print(f"{tok.lineno:3} {tok.type:12} {repr(tok.value)}")
            tok = parser.lexer.token()

        # parse
        parser.lexer.input(src)
        ast = parser.parser.parse(lexer=parser.lexer)
        print("\n=== AST ===")
        print(ast)
        if parser.errors:
            print("\n=== ERRORES ===")
            for e in parser.errors:
                print(e)
    else:
        test_parser()
