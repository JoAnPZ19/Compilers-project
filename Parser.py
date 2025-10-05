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
        self.lexer = Lexer.Lexer(self.errors, debug=self.debug)
        self.precedence = (
            ('left', 'OR'),
            ('left', 'AND'),
            ('left', 'EQUAL', 'LESS', 'GREATER', 'GREATEREQUAL', 'LESSEQUAL', 'LESSGREATER'),
            ('left', 'PLUS', 'MINUS'),
            ('left', 'MULTI', 'DIVIDE', 'MOD'),
            ('right', 'NOT', 'UMINUS'),
)

    def id_exists(self, symbol, p):
        if not self.lexer.symbol_table.exists(symbol):
            self.errors.append(f"Symbol '{symbol}' not declared", p.lexer.lineno, p.lexer.lexpos, 'semantic', self.data)
            print(self.errors[-1])

    def p_error(self, p):
        if not p:
            self.errors.append(f"Unexpected end of input", 0, 0, 'parser', self.data)
        else:
            self.errors.append(f"Syntax error on '{p.value}'", p.lineno, p.lexpos, 'parser', self.data)
        print(self.errors[-1])

    def parse_data(self, data):
        self.data = data
        self.lexer.data = data
        self.parser.parse(data, tracking=True)

    def build(self):
        self.tokens = tokens
        self.precedence = getattr(self, 'precedence', ())
        self.start = getattr(self, 'start', 'program')
        self.parser = yacc.yacc(module=self, debug=self.debug)

    def p_program(self, p):
        """program : PROGRAM ID body"""
        p[0] = Node("program", p[2], [p[3]])

    def p_body(self, p):
        """body : DECLARE declaration_list BEGIN statement_list END"""
        p[0] = Node("body", None, [Node("declarations", None, p[2]), Node("statements", None, p[4])])


    def p_declaration_list(self, p):
        """declaration_list : declaration SEMICOLON declaration_list
                            | empty"""
        if len(p) == 2:
            p[0] = []
        else:
            p[0] = [p[1]] + p[3]

    def p_declaration(self, p):
        """declaration : type identifier_list"""
        decl_nodes = [Node("identifier", name) for name in p[2]]
        p[0] = Node("declaration", p[1], decl_nodes)

    def p_identifier_list(self, p):
        """identifier_list : ID COMMA identifier_list
                           | ID"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

    def p_type(self, p):
        """type : INTEGER
                | DECIMAL"""
        p[0] = p[1]

    def p_statement_list(self, p):
        """statement_list : statement SEMICOLON p_statement_list_single"""
        p[0] = [p[1]] + (p[3] if p[3] else [])

    def p_statement_list_single(self, p):
        """p_statement_list_single : statement_list
                                | empty"""
        p[0] = p[1] if p[1] else []

    def p_statement(self, p):
        """statement :  if_statement
                | assign_statement
                | while_statement
                | do_while_statement
                | for_statement
                | read_statement
                | write_statement"""
        p[0] = p[1]

    def p_assign_statement(self, p):
        """assign_statement : ID ASSIGN expression"""
        self.id_exists(p[1], p)
        p[0] = Node("assign", p[1], [p[3]])

    def p_if_statement(self, p):
        """if_statement : IF condition THEN statement_list if_statement_aux"""
        if p[5] is None:
            p[0] = Node("if", None, [p[2], Node("then", None, p[4])])
        else:
            p[0] = Node("if", None, [p[2], Node("then", None, p[4]), p[5]])

    def p_if_statement_aux(self, p):
        """if_statement_aux : END
                            | ELSE statement_list END"""
        if len(p) == 2:
            p[0] = None
        else:
            p[0] = Node("else", None, p[2])

    def p_condition(self, p):
        """condition : expression"""
        p[0] = p[1]

    def p_do_while_statement(self, p):
        """do_while_statement : DO statement_list WHILE condition"""
        p[0] = Node("do-while", None, [Node("body", None, p[2]), p[4]])

    def p_for_statement(self, p):
        """for_statement : FOR assign_statement TO expression DO statement_list END"""
        p[0] = Node("for", None, [p[2], p[4], Node("body", None, p[6])])

    def p_while_statement(self, p):
        """while_statement : WHILE condition DO statement_list END"""
        p[0] = Node("while", None, [p[2], Node("body", None, p[4])])

    def p_read_statement(self, p):
        """read_statement : READ LPAREN ID RPAREN"""
        self.id_exists(p[3], p)
        p[0] = Node("read", p[3])

    def p_write_statement(self, p):
        """write_statement : WRITE LPAREN writable RPAREN"""
        p[0] = Node("write", None, [p[3]])

    def p_expression(self, p):
        """expression : simple_expression expression_aux"""
        if p[2] is None:
            p[0] = p[1]
        else:
            p[0] = Node("relop", p[2].value, [p[1], p[2].children[0]])

    def p_expression_aux(self, p):
        """expression_aux : relop simple_expression
                        | empty"""
        if len(p) == 3:
            p[0] = Node("relop", p[1], [p[2]])
        else:
            p[0] = None

    def p_dual_expression(self, p):
        """dual_expression : LPAREN expression RPAREN"""
        p[0] = p[2]

    def p_simple_expression(self, p):
        """simple_expression : tern
                            | dual_expression TERNAL simple_expression COLON simple_expression
                            | simple_expression addop tern"""
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 6:
            p[0] = Node("ternary", None, [p[1], p[3], p[5]])
        else:
            p[0] = Node("binop", p[2], [p[1], p[3]])

    def p_tern(self, p):
        """tern : factor_a
                | tern mulop factor_a"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Node("binop", p[2], [p[1], p[3]])

    def p_factor_a(self, p):
        """factor_a : factor 
                    | NOT factor 
                    | MINUS factor %prec UMINUS"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Node("unaryop", p[1], [p[2]])

    def p_factor(self, p):
        """factor : ID 
                | NUMBER 
                | dual_expression"""
        if p.slice[1].type == 'ID':
            self.id_exists(p[1], p)
            p[0] = Node("id", p[1])
        elif p.slice[1].type == 'NUMBER':
            p[0] = Node("number", p[1])
        else:
            p[0] = p[1]

    def p_unary(self, p):
        """unary : MINUS
                 | NOT"""

    def p_relop(self, p):
        """relop : EQUAL
                 | GREATER
                 | GREATEREQUAL
                 | LESS
                 | LESSEQUAL
                 | LESSGREATER"""

    def p_addop(self, p):
        """addop : PLUS
                 | MINUS
                 | OR"""

    def p_mulop(self, p):
        """mulop : MULTI
                 | DIVIDE
                 | MOD
                 | AND"""

    def p_constant(self, p):
        """constant : NUMBER"""

    def p_empty(self, p):
        """empty :"""

    def parse(self, source, debug=False, tracking=False):
        self.errors = []
        self.lexer.input(source)
        result = self.parser.parse(lexer=self.lexer, debug=debug, tracking=tracking)
        return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python Parser.py <archivo>")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, "r", encoding="utf-8") as f:
        src = f.read()

    p = Parser()
    ast = p.parse(src)
    print("\nAST:")
    print(ast)
    if p.errors:
        print("\nSemantic Errors:")
        for e in p.errors:
            print(e)

"""
Fast testing call

if __name__ == "__main__":
    source = 
    PROGRAM test
    DECLARE
        INTEGER x;
        DECIMAL y;
    BEGIN
        x := 5;
        IF x > 2 THEN
            WRITE(x);
        END
    END
  
    p = Parser(debug=False)
    p.build()
    ast = p.parse(source)
    print(ast)
"""

