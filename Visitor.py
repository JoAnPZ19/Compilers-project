import sys
import argparse
import os
import ast
import Parser
import Analyzer

def is_node(x):
    return hasattr(x, "type") and hasattr(x, "children")

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

class CppVisitor(Visitor):
    def __init__(self, symtab=None):
        self.function_lines = []  # Lines for function definitions
        self.main_lines = []      # Lines for main function
        self.symtab = symtab
        self.indent_level = 0
        self.inside_function = False
        self.declared_main = set()
        self.func_declared_stack = []
        self.current_output = None  # Will point to either function_lines or main_lines

    def emit(self, text=""):
        line = "    " * self.indent_level + text
        if self.current_output is not None:
            self.current_output.append(line)

    def push(self):
        self.indent_level += 1

    def pop(self):
        self.indent_level = max(0, self.indent_level - 1)

    def cpp_type_name(self, t):
        if t is None:
            return "std::any"
        if isinstance(t, str):
            name = t
            if name == 'int':
                return "int"
            if name in ('float', 'double'):
                return "double"
            if name == 'string':
                return "std::string"
            if name == 'bool':
                return "bool"
            if name == 'none':
                return "void"
            return "std::any"

        if t.name == 'int':
            return "int"
        if t.name in ('float', 'double'):
            return "double"
        if t.name == 'string':
            return "std::string"
        if t.name == 'bool':
            return "bool"
        if t.name == 'none':
            return "void"
        if t.name == 'list' and t.params:
            elem_type = self.cpp_type_name(t.params[0])
            return f"std::vector<{elem_type}>"
        if t.name == 'dict' and len(t.params) >= 2:
            k_type = self.cpp_type_name(t.params[0])
            v_type = self.cpp_type_name(t.params[1])
            return f"std::map<{k_type}, {v_type}>"
        if t.name == 'tuple' and t.params:
            types = ", ".join(self.cpp_type_name(p) for p in t.params)
            return f"std::tuple<{types}>"
        if t.name == 'func':
            return "auto"
        return "std::any"

    def get_expr_type(self, node):
        """Get the inferred type of an expression node"""
        return getattr(node, "inferred_type", None)

    def visit_module(self, node):
        for child in node.children:
            if isinstance(child, str):
                if child.strip() == "":
                    continue

            if is_node(child) and child.type == "function_def":
                # Function definitions go to function_lines
                self.current_output = self.function_lines
                self.inside_function = True
                self.visit(child)
                self.inside_function = False
            else:
                # Top-level statements go to main_lines
                self.current_output = self.main_lines
                self.inside_function = False
                self.func_declared_stack = [self.declared_main]
                self.indent_level = 1
                self.visit(child)
                self.indent_level = 0
                self.func_declared_stack = []

        return self.generate_full_output()

    def generate_full_output(self):
        includes = (
            "#include <any>\n"
            "#include <iostream>\n"
            "#include <string>\n"
            "#include <vector>\n"
            "#include <map>\n"
            "#include <set>\n"
            "#include <tuple>\n"
            "#include <cmath>\n"
            "using namespace std;\n\n"
        )

        # Add str() helper function
        str_helper = (
            "// Helper function for str() conversion\n"
            "template<typename T>\n"
            "std::string str(T value) {\n"
            "    return std::to_string(value);\n"
            "}\n\n"
        )

        functions_cpp = "\n".join(self.function_lines)
        
        main_cpp = "int main(int argc, char *argv[]) {\n"
        main_cpp += "\n".join(self.main_lines)
        main_cpp += "\n    return 0;\n}\n"

        return includes + str_helper + functions_cpp + "\n\n" + main_cpp

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
        ret_type_str = "std::any"
        cpp_params = []

        if func_type and func_type.name == 'func':
            param_types = func_type.params[:-1]
            for idx, pname in enumerate(params):
                ptype = param_types[idx] if idx < len(param_types) else None
                cpp_params.append(f"{self.cpp_type_name(ptype)} {pname}")
            if len(func_type.params) >= 1:
                ret_type_str = self.cpp_type_name(func_type.params[-1])
        else:
            cpp_params = [f"std::any {p}" for p in params]

        self.func_declared_stack.append(set())

        self.emit(f"{ret_type_str} {name}({', '.join(cpp_params)}) {{")
        self.push()

        if suite_node:
            self.visit(suite_node)

        self.pop()
        self.emit("}\n")

        self.func_declared_stack.pop()

    def visit_suite(self, node):
        for child in node.children:
            if isinstance(child, str):
                continue
            self.visit(child)

    def visit_if(self, node):
        condition = self.visit(node.children[0])
        self.emit(f"if ({condition}) {{")
        self.push()
        self.visit(node.children[1])
        self.pop()
        self.emit("}")
        
        if len(node.children) > 2:
            rest = node.children[2:]
            for item in rest:
                if is_node(item):
                    if item.type == "elif":
                        self.visit_elif(item)
                    elif item.type == "else":
                        self.emit("else {")
                        self.push()
                        if item.children:
                            self.visit(item.children[0])
                        self.pop()
                        self.emit("}")
                    elif item.type == "suite":
                        # This is an else suite
                        self.emit("else {")
                        self.push()
                        self.visit(item)
                        self.pop()
                        self.emit("}")

    def visit_elif(self, node):
        condition = self.visit(node.children[0])
        self.emit(f"else if ({condition}) {{")
        self.push()
        self.visit(node.children[1])
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
        
        # Get the type of the loop variable
        iter_type = self.get_expr_type(iterable)
        if iter_type and iter_type.name == 'list' and iter_type.params:
            elem_type = self.cpp_type_name(iter_type.params[0])
            self.emit(f"for ({elem_type} {target_name} : {iterable_expr}) {{")
        else:
            self.emit(f"for (auto {target_name} : {iterable_expr}) {{")
        
        self.push()
        if suite:
            self.visit(suite)
        self.pop()
        self.emit("}")

    def visit_assignment(self, node):
        name = node.value
        expr_node = node.children[0] if node.children else None
        expr = self.visit(expr_node) if expr_node else "/*missing_expr*/"

        t = getattr(node, "inferred_type", None)
        if t is None and self.symtab is not None:
            tt = self.symtab.lookup(name)
            t = tt if tt is not None else None

        cpp_t = self.cpp_type_name(t)

        # Check if variable is already declared in current scope
        cur_declared = self.func_declared_stack[-1] if self.func_declared_stack else self.declared_main
        
        if name in cur_declared:
            self.emit(f"{name} = {expr};")
        else:
            decl_type = cpp_t if cpp_t != "std::any" else "auto"
            self.emit(f"{decl_type} {name} = {expr};")
            cur_declared.add(name)

    def visit_return(self, node):
        if node.children:
            expr = self.visit(node.children[0])
            self.emit(f"return {expr};")
        else:
            self.emit("return;")

    def visit_break(self, node):
        self.emit("break;")

    def visit_continue(self, node):
        self.emit("continue;")

    def visit_expression_stmt(self, node):
        expr_node = node.children[0] if node.children else None
        if not expr_node:
            return ""

        # Check if it's an assignment or other statement that handles itself
        if is_node(expr_node) and expr_node.type == "assignment":
            self.visit(expr_node)
            return ""

        expr_cpp = self.visit(expr_node)
        
        if expr_cpp and expr_cpp.strip():
            # Don't double-emit for print statements
            if not (is_node(expr_node) and expr_node.type == "call" and expr_node.value == "print"):
                self.emit(f"{expr_cpp};")
        
        return ""

    def visit_binary_op(self, node):
        left_node = node.children[0]
        right_node = node.children[1]
        op = node.value

        left = self.visit(left_node)
        right = self.visit(right_node)

        # Get types
        left_type = self.get_expr_type(left_node)
        right_type = self.get_expr_type(right_node)
        result_type = self.get_expr_type(node)

        # Handle power operator
        if op == '**':
            return f"pow({left}, {right})"

        # String concatenation
        if result_type and result_type.name == 'string':
            return f"({left} + {right})"

        # Both operands are concrete types
        if left_type and right_type:
            if left_type.is_numeric() and right_type.is_numeric():
                return f"({left} {op} {right})"
            elif left_type.name == 'string' or right_type.name == 'string':
                return f"({left} + {right})"

        # Default
        return f"({left} {op} {right})"

    def visit_unary_op(self, node):
        operand = self.visit(node.children[0])
        op = node.value
        if op == 'not':
            return f"!({operand})"
        return f"{op}({operand})"

    def visit_comparison(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        
        # Map Python operators to C++
        op_map = {
            '==': '==',
            '!=': '!=',
            '<': '<',
            '>': '>',
            '<=': '<=',
            '>=': '>=',
            'is': '==',
            'in': 'in'  # Special handling needed
        }
        cpp_op = op_map.get(op, op)
        return f"({left} {cpp_op} {right})"

    def visit_boolean_op(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        
        # Map Python boolean operators to C++
        if op == 'and':
            op = '&&'
        elif op == 'or':
            op = '||'
            
        return f"({left} {op} {right})"

    def visit_call(self, node):
        func_name = node.value
        args = node.children or []
        arg_exprs = [self.visit(a) for a in args]

        if func_name == "print":
            join_expr = " << ".join(arg_exprs) if arg_exprs else '""'
            self.emit(f"std::cout << {join_expr} << std::endl;")
            return ""

        # Type conversion functions
        if func_name in ("str", "int", "float", "bool"):
            if arg_exprs:
                return f"{func_name}({arg_exprs[0]})"
            return f"{func_name}()"

        if func_name == "len":
            if arg_exprs:
                return f"{arg_exprs[0]}.size()"
            return "0"

        if func_name == "range":
            # Generate vector initialization
            if len(arg_exprs) == 1:
                # range(n) - 0 to n-1
                return f"/* range(0, {arg_exprs[0]}) */"
            return f"/* range({', '.join(arg_exprs)}) */"

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
        escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        return f'"{escaped}"'

    def visit_boolean(self, node):
        v = str(node.value)
        if v.lower() in ("true", "1"):
            return "true"
        return "false"

    def visit_pair(self, node):
        k = self.visit(node.children[0])
        v = self.visit(node.children[1])
        return f"{{{k}, {v}}}"

    def visit_list(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        
        # Get element type
        list_type = self.get_expr_type(node)
        if list_type and list_type.name == 'list' and list_type.params:
            elem_cpp_type = self.cpp_type_name(list_type.params[0])
            return f"std::vector<{elem_cpp_type}>{{{items}}}"
        
        return f"std::vector<std::any>{{{items}}}"

    def visit_tuple(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        
        # Get tuple types
        tuple_type = self.get_expr_type(node)
        if tuple_type and tuple_type.name == 'tuple' and tuple_type.params:
            types = ", ".join(self.cpp_type_name(p) for p in tuple_type.params)
            return f"std::tuple<{types}>({items})"
        
        return f"std::make_tuple({items})"

    def visit_dict(self, node):
        items = []
        for c in node.children:
            if is_node(c) and c.type == "pair":
                items.append(self.visit(c))
        inner = ", ".join(items)
        
        # Get dict types
        dict_type = self.get_expr_type(node)
        if dict_type and dict_type.name == 'dict' and len(dict_type.params) >= 2:
            k_type = self.cpp_type_name(dict_type.params[0])
            v_type = self.cpp_type_name(dict_type.params[1])
            return f"std::map<{k_type}, {v_type}>{{{inner}}}"
        
        return f"std::map<std::any, std::any>{{{inner}}}"

    def visit_set(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        return f"std::set<std::any>{{{items}}}"

    def visit_parameter(self, node):
        return node.value

    def visit_pass(self, node):
        return ""

    def visit_none(self, node):
        return "nullptr"

def print_symbol_table(symtab):
    print("\n" + "="*60)
    print("SYMBOL TABLE")
    print("="*60)
    print(symtab)
    print("="*60 + "\n")

def main():
    parser_cli = argparse.ArgumentParser(description="Visitor that generates C++ from AST")
    parser_cli.add_argument("input", help="Python source file")
    parser_cli.add_argument("-o", "--output", help="Optional output .cpp file", default=None)
    args = parser_cli.parse_args()

    fname = args.input
    if not os.path.exists(fname):
        print("File not found:", fname)
        sys.exit(1)

    src = open(fname, "r", encoding="utf-8").read()

    p = Parser.Parser(debug=False)
    p.build()
    ast_tree = p.parse(src)

    if p.errors:
        print("\n=== PARSE ERRORS ===")
        for e in p.errors:
            print(e)

    AnalyzerClass = Analyzer.Analyzer
    analyzer = AnalyzerClass()
    analyzer.analyze(ast_tree)

    # Print readable symbol table
    print_symbol_table(analyzer.symtab)

    visitor = CppVisitor(analyzer.symtab)
    cpp_code = visitor.visit(ast_tree)

    base = os.path.splitext(fname)[0]
    out_name = args.output if args.output else f"{base}.cpp"
    with open(out_name, "w", encoding="utf-8") as out:
        out.write(cpp_code)
    
    print(f"✓ Generated {out_name}")

if __name__ == "__main__":
    main()