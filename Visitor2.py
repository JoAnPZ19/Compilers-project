
import sys
import argparse
import os
import Parser
import Analyzer

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
        self.main_lines = [] 
        self.indent_level = 0
        self.top_level_statements = []
        self.inside_function = False
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
    
    # === DEBUG: Print AST with inferred types ===
    def dump_ast(self, node, indent=0):
        pad = "  " * indent
        inferred = getattr(node, "inferred_type", None)
        print(f"{pad}{node.type}  value={node.value}  type={inferred}")
        for child in getattr(node, "children", []) or []:
            self.dump_ast(child, indent + 1)

    def cpp_type_name(self, t):
        # Recibe un Analyzer.Type o None
        if t is None:
            return "std::any"
        if isinstance(t, str):
            # improbable, pero manejar
            name = t
            if name == 'int':
                return "int"
            if name == 'float':
                return "double"
            if name == 'string':
                return "std::string"
            if name == 'bool':
                return "bool"
            if name == 'none':
                return "void"
            return "std::any"

        # Analyzer.Type objects
        if t.name == 'int':
            return "int"
        if t.name == 'float':
            return "double"
        if t.name == 'string':
            return "std::string"
        if t.name == 'bool':
            return "bool"
        if t.name == 'none':
            return "void"
        if t.name == 'list' and t.params:
            # list<T> -> std::vector<T>
            return f"std::vector<{self.cpp_type_name(t.params[0])}>"
        if t.name == 'dict' and len(t.params) >= 2:
            return f"std::map<{self.cpp_type_name(t.params[0])},{self.cpp_type_name(t.params[1])}>"
        if t.name == 'func':
            # functions handled elsewhere; return auto
            return "auto"
        # fallback
        return "std::any"


    # main nodes
    def visit_module(self, node):

        for child in node.children:

            if isinstance(child, str):
                if child.strip() == "":
                    continue

            if is_node(child) and child.type == "function_def":
                self.visit(child)

            else:
                self.top_level_statements.append(child)

        return self.generate_full_output()


    def generate_full_output(self):
        includes = (
            "#include <any>\n"
            "#include <iostream>\n"
            "#include <string>\n"
            "using namespace std;\n\n"
        )

        # funciones
        body = "\n".join(self.lines)

        # generar main
        main = "int main() {\n"

        for stmt in self.top_level_statements:
            line = self.visit(stmt)
            if line and line.strip():
                main += f"    {line};\n"

        main += "    return 0;\n}\n"

        return includes + body + "\n" + main

    def visit_function_def(self, node):
        name = node.value
        params_node = node.children[0] if len(node.children) > 0 else None
        suite_node = node.children[1] if len(node.children) > 1 else None

        params = []
        if params_node and is_node(params_node):
            for p in params_node.children:
                if is_node(p):
                    params.append(p.value)

        func_type = getattr(node, "inferred_type", None)
        ret_type_str = "auto"
        cpp_params = []

        if func_type and func_type.name == 'func':
            param_types = func_type.params[:-1]
            ret_type = func_type.params[-1]
            ret_type_str = self.cpp_type_name(ret_type)

            for pname, ptype in zip(params, param_types):
                cpp_params.append(f"{self.cpp_type_name(ptype)} {pname}")
        else:
            cpp_params = [f"std::any {p}" for p in params]

        self.inside_function = True

        self.emit(f"{ret_type_str} {name}({', '.join(cpp_params)}) {{")
        self.push()

        if suite_node:
            self.visit(suite_node)

        self.pop()
        self.emit("}\n")

        self.inside_function = False

  
    def visit_suite(self, node):
        for child in node.children:
            if isinstance(child, str):
                continue
            self.visit(child)

    def visit_if(self, node):
        # node estructure
        # children[0]: condition expression
        # children[1]: suit for if
        # children[2]: elif or else (optional)
        condition = self.visit(node.children[0])
        self.emit(f"if ({condition}) {{")
        self.push()
        self.visit(node.children[1])  # if-body
        self.pop()
        self.emit("}")
        
        # Handle elif/else
        if len(node.children) > 2:
            rest = node.children[2]
            if is_node(rest):
                if rest.type == "elif":
                    # Handle elif chain
                    self.visit_elif(rest)
                elif rest.type == "else":
                    # Handle else
                    self.emit("else {")
                    self.push()
                    self.visit(rest.children[0] if rest.children else rest)
                    self.pop()
                    self.emit("}")
                elif rest.type == "suite":
                    # Direct else suite
                    self.emit("else {")
                    self.push()
                    self.visit(rest)
                    self.pop()
                    self.emit("}")
    
    def visit_elif(self, node):
        #elif node, like else if in C++
        condition = self.visit(node.children[0])
        self.emit(f"else if ({condition}) {{")
        self.push()
        self.visit(node.children[1])  # elif-body
        self.pop()
        self.emit("}")
        
        # Check for more elif or else
        if len(node.children) > 2:
            rest = node.children[2]
            if is_node(rest):
                if rest.type == "elif":
                    self.visit_elif(rest)
                elif rest.type == "else" or rest.type == "suite":
                    self.emit("else {")
                    self.push()
                    self.visit(rest.children[0] if hasattr(rest, 'children') and rest.children else rest)
                    self.pop()
                    self.emit("}")
    
    def visit_else(self, node):
        # else clause
        self.emit("else {")
        self.push()
        if node.children:
            self.visit(node.children[0])
        self.pop()
        self.emit("}")

    def visit_while(self, node):
        # node structure:
        # children[0]: condition expression
        # children[1]: suite (while-body)
        
        condition = self.visit(node.children[0])
        self.emit(f"while ({condition}) {{")
        self.push()
        self.visit(node.children[1])  # while-body
        self.pop()
        self.emit("}")

    def visit_for(self, node):
    # node structure:
    # children[0]: target variable (identifier)
    # children[1]: iterable expression
    # children[2]: suite (for-body)
    
        target = self.visit(node.children[0])
        iterable = self.visit(node.children[1])
        
        # Simple range-based for loop
        self.emit(f"for (auto {target} : {iterable}) {{")
        self.push()
        self.visit(node.children[2])  # for-body
        self.pop()
        self.emit("}")

    # Sentences
    def visit_assignment(self, node):
        name = node.value
        expr_node = node.children[0] if node.children else None
        expr = self.visit(expr_node)
        # check inferred type on node or variable in symtab
        t = getattr(node, "inferred_type", None)
        if t is None:
            # try child identifier's inferred type
            if expr_node is not None:
                t = getattr(expr_node, "inferred_type", None)
        # choose C++ type
        if t:
            cpp_t = self.cpp_type_name(t)
            # if the expression was already emitted as statement (e.g., prints), it may be ""
            self.emit(f"{cpp_t} {name} = {expr};")
        else:
            # fallback
            self.emit(f"std::any {name} = {expr};")


    def visit_return(self, node):
        if node.children:
            expr = self.visit(node.children[0])
            self.emit(f"return {expr};")
        else:
            self.emit("return {};") 
    
    def visit_break(self, node):
        self.emit("break;")

    def visit_continue(self, node):
        self.emit("continue;")
            
    def visit_expression_stmt(self, node):
        expr_node = node.children[0] if node.children else None
        if not expr_node:
            return ""

        expr_cpp = self.visit(expr_node)

        if self.inside_function:
            if expr_cpp.strip():
                self.emit(f"{expr_cpp};")
            return ""

        else:
            return expr_cpp


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

    def visit_augmented_assignment(self, node):
    # node.value: operator (+=, -=, *=, etc.)
    # children[0]: target (identifier)
    # children[1]: expression
        target = self.visit(node.children[0])
        expr = self.visit(node.children[1])
        op = node.value
        self.emit(f"{target} {op} {expr};")

    def visit_call(self, node):
        func_name = node.value
        args = node.children or []
        arg_exprs = [self.visit(a) for a in args]

        if func_name == "print":
            join_expr = " << ".join(arg_exprs) if arg_exprs else '""'

            # Si estamos dentro de una función, emitimos
            if self.inside_function:
                self.emit(f"std::cout << {join_expr} << std::endl;")
                return ""

            # Si está en top-level devolvemos el código (será puesto dentro del main)
            return f"std::cout << {join_expr} << std::endl"

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
        raw = node.value 

        try:
            # Interpret Python literal (handles escapes, unicode, etc.)
            text = ast.literal_eval(raw)
        except:
            # Fallback: remove only outer quotes
            text = raw[1:-1]

        # Escape for C++
        escaped = (
            text.replace('\\', '\\\\')
                .replace('"', '\\"')
                .replace('\n', '\\n')
                .replace('\t', '\\t')
        )

        return f"\"{escaped}\""

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

def print_symbol_table(symtab):
    print("=== SYMBOL TABLE ===")
    for i, scope in enumerate(symtab.scopes):
        print(f"--- Scope {i} ---")
        for name, symbol in scope.items():
            print(f"{name} : {symbol.type}")
    print("====================")

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

    # Build parser and parse with it
    p = Parser.Parser(debug=False)
    p.build()
    ast = p.parse(src)

    # If erorrs, print, but try to generate something
    if p.errors:
        print("\n===PARSE ERRORS ===")
        for e in p.errors:
            print(e)
        # no return: try to figure with partial AST 

    from Analyzer import Analyzer as AnalyzerClass
    analyzer = AnalyzerClass()
    analyzer.analyze(ast)

    visitor = CppVisitor()
    cpp_code = visitor.visit(ast)

   # For debug purposes
    print_symbol_table(analyzer.symtab)
    
    base = os.path.splitext(fname)[0]
    out_name = f"{base}.cpp"
    with open(out_name, "w", encoding="utf-8") as out:
        out.write(cpp_code)

if __name__ == "__main__":
    main()
