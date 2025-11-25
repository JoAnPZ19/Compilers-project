import sys
import argparse
import os
import ast
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
    def __init__(self, symtab=None):
        # lines for function bodies and top-level function definitions
        self.lines = []
        # symbol table from analyzer (used to get inferred types)
        self.symtab = symtab
        self.indent_level = 0
        # collect top-level nodes to put inside main
        self.top_level_statements = []
        # are we currently generating inside a function?
        self.inside_function = False
        # track declared variables in main (to avoid redeclaring)
        self.declared_main = set()
        # stack to track declared variables per function
        self.func_declared_stack = []

    # utilidades para emitir dentro de funciones (self.lines)
    def emit(self, text=""):
        self.lines.append("    " * self.indent_level + text)

    def push(self):
        self.indent_level += 1

    def pop(self):
        self.indent_level = max(0, self.indent_level - 1)

    def cpp_type_name(self, t):
        # t puede ser None, una instancia Analyzer.Type o un string
        if t is None:
            return "std::any"
        if isinstance(t, str):
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
            return f"std::vector<{self.cpp_type_name(t.params[0])}>"
        if t.name == 'dict' and len(t.params) >= 2:
            return f"std::map<{self.cpp_type_name(t.params[0])},{self.cpp_type_name(t.params[1])}>"
        if t.name == 'func':
            return "auto"
        return "std::any"

    # === DEBUG: Print AST with inferred types ===
    def dump_ast(self, node, indent=0):
        pad = "  " * indent
        inferred = getattr(node, "inferred_type", None)
        print(f"{pad}{node.type}  value={getattr(node,'value',None)}  type={inferred}")
        for child in getattr(node, "children", []) or []:
            if is_node(child):
                self.dump_ast(child, indent + 1)

    # main nodes
    def visit_module(self, node):
        for child in node.children:
            # ignore plain newline strings
            if isinstance(child, str):
                if child.strip() == "":
                    continue

            if is_node(child) and child.type == "function_def":
                # visit functions now (they append to self.lines via emit)
                self.visit(child)
            else:
                # keep for main generation
                self.top_level_statements.append(child)

        return self.generate_full_output()

    def generate_full_output(self):
        includes = (
            "#include <any>\n"
            "#include <iostream>\n"
            "#include <string>\n"
            "#include <vector>\n"
            "#include <map>\n"
            "#include <set>\n"
            "using namespace std;\n\n"
        )

        # funciones y demás emitidas en self.lines
        functions_cpp = "\n".join(self.lines)

        # generar main con las lineas que las visitas retornen
        main = "int main() {\n"
        for stmt in self.top_level_statements:
            line = self.visit(stmt)
            if line and line.strip():
                # si la línea ya contiene ; (p.ej. print code), no agregar;
                if line.strip().endswith(";"):
                    main += f"    {line}\n"
                else:
                    main += f"    {line};\n"
        main += "    return 0;\n}\n"

        return includes + functions_cpp + "\n\n" + main

    # --- Functions ---
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
            # if function has fewer param types than params, fallback to any
            for idx, pname in enumerate(params):
                ptype = param_types[idx] if idx < len(param_types) else None
                cpp_params.append(f"{self.cpp_type_name(ptype)} {pname}")
            if len(func_type.params) >= 1:
                ret_type_str = self.cpp_type_name(func_type.params[-1])
        else:
            cpp_params = [f"std::any {p}" for p in params]

        # begin function: set inside flag and new declared set for this function
        self.inside_function = True
        self.func_declared_stack.append(set())

        self.emit(f"{ret_type_str} {name}({', '.join(cpp_params)}) {{")
        self.push()

        if suite_node:
            self.visit(suite_node)

        self.pop()
        self.emit("}\n")

        # leave function
        self.func_declared_stack.pop()
        self.inside_function = False

    def visit_suite(self, node):
        for child in node.children:
            if isinstance(child, str):
                continue
            self.visit(child)

    # control structures unchanged (they call visit on bodies and will use emit inside)
    def visit_if(self, node):
        condition = self.visit(node.children[0])
        self.emit(f"if ({condition}) {{")
        self.push()
        self.visit(node.children[1])
        self.pop()
        self.emit("}")
        if len(node.children) > 2:
            rest = node.children[2]
            if is_node(rest):
                if rest.type == "elif":
                    self.visit_elif(rest)
                elif rest.type in ("else", "suite"):
                    self.emit("else {")
                    self.push()
                    self.visit(rest.children[0] if rest.children else rest)
                    self.pop()
                    self.emit("}")

    def visit_elif(self, node):
        condition = self.visit(node.children[0])
        self.emit(f"else if ({condition}) {{")
        self.push()
        self.visit(node.children[1])
        self.pop()
        self.emit("}")
        if len(node.children) > 2:
            rest = node.children[2]
            if is_node(rest):
                if rest.type == "elif":
                    self.visit_elif(rest)
                elif rest.type in ("else", "suite"):
                    self.emit("else {")
                    self.push()
                    self.visit(rest.children[0] if rest.children else rest)
                    self.pop()
                    self.emit("}")

    def visit_else(self, node):
        self.emit("else {")
        self.push()
        if node.children:
            self.visit(node.children[0])
        self.pop()
        self.emit("}")

    def visit_while(self, node):
        condition = self.visit(node.children[0])
        self.emit(f"while ({condition}) {{")
        self.push()
        self.visit(node.children[1])
        self.pop()
        self.emit("}")

    def visit_for(self, node):
        target = node.children[0]
        iterable = node.children[1]
        suite = node.children[2] if len(node.children) > 2 else None

        target_name = self.visit(target)
        iterable_expr = self.visit(iterable)
        # emit a simple range loop if iterable is a vector or expression
        self.emit(f"for (auto {target_name} : {iterable_expr}) {{")
        self.push()
        if suite:
            self.visit(suite)
        self.pop()
        self.emit("}")

    # Sentences: assignment must return string for top-level (so generate_full_output can place it)
    def visit_assignment(self, node):
        name = node.value
        expr_node = node.children[0] if node.children else None
        expr = self.visit(expr_node) if expr_node else "/*missing_expr*/"

        # get inferred type: prefer node.inferred_type, fallback to symtab lookup
        t = getattr(node, "inferred_type", None)
        if t is None and self.symtab is not None:
            tt = self.symtab.lookup(name)
            t = tt if tt is not None else None

        cpp_t = self.cpp_type_name(t)

        if self.inside_function:
            # in function scope: use function-declared set to know if declared already
            cur_declared = self.func_declared_stack[-1]
            if name in cur_declared:
                self.emit(f"{name} = {expr};")
            else:
                # declare with type if available, else std::any
                decl_type = cpp_t if cpp_t else "std::any"
                self.emit(f"{decl_type} {name} = {expr};")
                cur_declared.add(name)
            return ""  # function emissions already done
        else:
            # top-level: return a string; generate_full_output will append semicolon
            if name in self.declared_main:
                return f"{name} = {expr}"
            else:
                decl_type = cpp_t if cpp_t else "std::any"
                self.declared_main.add(name)
                return f"{decl_type} {name} = {expr}"

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
            if expr_cpp and expr_cpp.strip():
                # if expression already emitted (e.g., visit_assignment emitted), do nothing
                # but if it's a simple expression, emit as statement
                self.emit(f"{expr_cpp};")
            return ""
        else:
            # top-level: return expression to be placed in main
            return expr_cpp

    # Expressions: returns string as C++
    def visit_binary_op(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value

        # If either child is a string literal or inferred string (node.inferred_type),
        # we want concatenation without numeric any_cast
        # But this is approximate: prefer using node children inferred types if present
        left_t = getattr(node.children[0], "inferred_type", None)
        right_t = getattr(node.children[1], "inferred_type", None)

        is_string = (left_t and getattr(left_t, "name", None) == "string") or \
                    (right_t and getattr(right_t, "name", None) == "string")

        if op == "+" and is_string:
            return f"({left} + {right})"

        # default numeric fallback (user uses any_cast double)
        return f"std::any_cast<double>({left}) {op} std::any_cast<double>({right})"

    def visit_unary_op(self, node):
        operand = self.visit(node.children[0])
        op = node.value
        if op == 'not':
            return f"!({operand})"
        return f"{op}{operand}"

    def visit_comparison(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        # comparisons in C++ use &&/|| equivalents? keep original Python operator tokens
        # but ensure operands are raw values (no any_cast if they are numbers/strings)
        return f"({left} {op} {right})"

    def visit_boolean_op(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        return f"({left} {op} {right})"

    def visit_augmented_assignment(self, node):
        target = self.visit(node.children[0])
        expr = self.visit(node.children[1])
        op = node.value
        if self.inside_function:
            self.emit(f"{target} {op} {expr};")
            return ""
        return f"{target} {op} {expr}"

    def visit_call(self, node):
        func_name = node.value
        args = node.children or []
        arg_exprs = [self.visit(a) for a in args]

        if func_name == "print":
            join_expr = " << ".join(arg_exprs) if arg_exprs else '""'
            if self.inside_function:
                self.emit(f"std::cout << {join_expr} << std::endl;")
                return ""
            # top-level: return the expression without trailing semicolon
            return f"std::cout << {join_expr} << std::endl"

        return f"{func_name}({', '.join(arg_exprs)})"

    def visit_subscript(self, node):
        obj = self.visit(node.children[0])
        idx = self.visit(node.children[1])
        return f"{obj}[{idx}]"

    def visit_identifier(self, node):
        return node.value

    def visit_number(self, node):
        return str(node.value)

    def visit_string(self, node):
        raw = node.value
        try:
            text = ast.literal_eval(raw)
        except:
            text = raw[1:-1] if isinstance(raw, str) and len(raw) >= 2 else raw
        # escape for C++
        escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        return f"\"{escaped}\""

    def visit_boolean(self, node):
        v = str(node.value)
        if v.lower() in ("true", "1"):
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
        return node.value

    def visit_pass(self, node):
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
    ast_tree = p.parse(src)

    # If errors, print, but try to generate something
    if p.errors:
        print("\n===PARSE ERRORS ===")
        for e in p.errors:
            print(e)

    AnalyzerClass = Analyzer.Analyzer
    analyzer = AnalyzerClass()
    analyzer.analyze(ast_tree)

    # pass analyzer.symtab so visitor can use inferred types
    visitor = CppVisitor(analyzer.symtab)
    cpp_code = visitor.visit(ast_tree)

    # For debug purposes
    print_symbol_table(analyzer.symtab)

    base = os.path.splitext(fname)[0]
    out_name = f"{base}.cpp"
    with open(out_name, "w", encoding="utf-8") as out:
        out.write(cpp_code)

if __name__ == "__main__":
    main()
