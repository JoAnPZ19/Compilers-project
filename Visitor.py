
import sys
import argparse
import os
import Parser

# Helper: Node-like detector
def is_node(x):
    return hasattr(x, "type") and hasattr(x, "children")

# Visitor 
class Visitor:
    def visit(self, node):
        if node is None:
            return ""
        if isinstance(node, str):
            return ""
        if not is_node(node):
            return ""
        method_name = f"visit_{node.type}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        out = ""
        for child in getattr(node, "children", []) or []:
            out_child = self.visit(child)
            out += out_child if out_child is not None else ""
        return out

# Visitor -> C++  std::any

class CppVisitor(Visitor):
    def __init__(self):
        self.lines = []
        self.indent_level = 0

    # utilidades
    def emit(self, text=""):
        self.lines.append("    " * self.indent_level + text)

    def push(self):
        self.indent_level += 1

    def pop(self):
        self.indent_level = max(0, self.indent_level - 1)

    def get_code(self):
        header = [
            "#include <any>",
            "#include <iostream>",
            "#include <vector>",
            "#include <map>",
            "#include <set>",
            "#include <tuple>",
            "using namespace std;",
            ""
        ]
        return "\n".join(header + self.lines)

    # main nodes
    def visit_module(self, node):
         # read functions and declarations
        for child in node.children:
            self.visit(child)
        return self.get_code()

    def visit_function_def(self, node):
        # node.value: name; node.children: [parameters_node, suite_node]
        name = node.value
        params_node = node.children[0] if len(node.children) > 0 else None
        suite_node = node.children[1] if len(node.children) > 1 else None

        params = []
        if params_node and is_node(params_node):
            for p in params_node.children:
                if is_node(p):
                    params.append(p.value)

        cpp_params = ", ".join([f"std::any {p}" for p in params])
        self.emit(f"std::any {name}({cpp_params}) {{")
        self.push()
        # Body
        if suite_node:
            self.visit(suite_node)
        self.pop()
        self.emit("}\n")

    def visit_suite(self, node):
        for child in node.children:
            if isinstance(child, str):
                continue
            self.visit(child)

    # Sentences
    def visit_assignment(self, node):
        name = node.value
        expr = self.visit(node.children[0])
        self.emit(f"std::any {name} = {expr};")

    def visit_return(self, node):
        if node.children:
            expr = self.visit(node.children[0])
            self.emit(f"return {expr};")
        else:
            self.emit("return {};") 

    def visit_expression_stmt(self, node):
        expr_node = node.children[0] if node.children else None
        if expr_node:
            if is_node(expr_node) and expr_node.type == "call":
                s = self.visit(expr_node)
                if s.strip():
                    if "std::cout" in s or s.endswith(";"):
                        if not any(line.strip().endswith(";") for line in [s.strip()]):
                            self.emit(s)
                        else:
                            self.emit(s if s.endswith(";") else s + ";")
                    else:
                        self.emit(f"{s};")
            else:
                expr = self.visit(expr_node)
                if expr:
                    self.emit(f"{expr};")

    # Expressions: returns string as C++
    def visit_binary_op(self, node):
        # children[0], children[1] expressions
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        return f"std::any_cast<double>({left}) {op} std::any_cast<double>({right})"

    def visit_unary_op(self, node):
        # node.value es '-' o 'not'
        operand = self.visit(node.children[0])
        op = node.value
        if op == 'not':
            return f"!({operand})"
        return f"{op}{operand}"

    def visit_comparison(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        return f"({left} {op} {right})"

    def visit_boolean_op(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        return f"({left} {op} {right})"

    def visit_call(self, node):
        # node.value: 
        func_name = node.value
        args = node.children or []
        arg_exprs = [self.visit(a) for a in args]

        if func_name == "print":
            # join con " << " y convert args a streamables
            parts = []
            for ae in arg_exprs:
                parts.append(f"{ae}")
                parts.append(' << " " << ')
            # remove last added spacer
            if parts:
                # compose: std::cout << arg1 << " " << arg2 << std::endl;
                join_expr = " << ".join([p for p in arg_exprs])
                self.emit(f"std::cout << {join_expr} << std::endl;")
                return ""  # ya emitimos la sentencia
            else:
                self.emit('std::cout << std::endl;')
                return ""

        # Normal Calls: return expression
        return f"{func_name}({', '.join(arg_exprs)})"

    def visit_subscript(self, node):
        # [obj, index]
        obj = self.visit(node.children[0])
        idx = self.visit(node.children[1])
        return f"{obj}[{idx}]"

    def visit_identifier(self, node):
        return node.value

    def visit_number(self, node):
        # numbers in parser  int or float (node.value)
        return str(node.value)

    def visit_string(self, node):
        # node.value proviene de lexer con comillas incluidas "hola" o 'hola'
        # asegurarnos que esté con comillas dobles para C++
        v = node.value
        if isinstance(v, str):
            if v.startswith('"') and v.endswith('"'):
                return v
            if v.startswith("'") and v.endswith("'"):
                inner = v[1:-1]
                return f"\"{inner}\""
            return f"\"{v}\""
        return str(v)

    def visit_boolean(self, node):
        val = str(node.value)
        if val.lower() in ("true", "1"):
            return "true"
        return "false"

    def visit_pair(self, node):
        k = self.visit(node.children[0])
        v = self.visit(node.children[1])
        return f"make_pair({k}, {v})"

    def visit_list(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        return f"vector<any>{{{items}}}"

    def visit_tuple(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        return f"make_tuple({items})"

    def visit_dict(self, node):
        # return expression constructing a std::map<any, any>
        items = []
        for c in node.children:
            if is_node(c) and c.type == "pair":
                items.append(f"{{{self.visit(c.children[0])}, {self.visit(c.children[1])}}}")
        inner = ", ".join(items)
        return f"map<any, any>{{{inner}}}"

    def visit_set(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        return f"set<any>{{{items}}}"

    def visit_parameter(self, node):
        # parameter node.value is name; used when building function signature
        return node.value

    def visit_pass(self, node):
        # no-op
        return ""

def main():
    parser_cli = argparse.ArgumentParser(description="Visitor that generates C++ from AST produced by your Parser")
    parser_cli.add_argument("input", help="Python source file (parsed by your Parser)")
    parser_cli.add_argument("-o", "--output", help="Optional output .cpp file", default=None)
    args = parser_cli.parse_args()

    fname = args.input
    if not os.path.exists(fname):
        print("File not found:", fname)
        sys.exit(1)

    src = open(fname, "r", encoding="utf-8").read()

    # construir parser y parsear (usar tu Parser class)
    p = Parser.Parser(debug=False)
    p.build()
    ast = p.parse(src)

    # si hubo errores, imprimirlos y salir (pero aún así intentamos generar)
    if p.errors:
        print("\n===PARSE ERRORS ===")
        for e in p.errors:
            print(e)
        # no return: try to figure with partial AST 

    visitor = CppVisitor()
    cpp_code = visitor.visit(ast)

    base = os.path.splitext(fname)[0]
    out_name = f"{base}.cpp"
    with open(out_name, "w", encoding="utf-8") as out:
        out.write(cpp_code)

if __name__ == "__main__":
    main()
