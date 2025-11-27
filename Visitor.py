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
        self.function_lines = []  
        self.main_lines = []     
        self.symtab = symtab
        self.indent_level = 0
        self.inside_function = False
        self.declared_main = set()
        self.func_declared_stack = []
        self.current_output = None  
        self.global_vars = set()
        self.local_vars = {}
        self.errors = []
        self.current_function = None
        # Aseguramos que los singletons de Analyzer estén disponibles
        self.ANY = Analyzer.ANY
        self.INT = Analyzer.INT
        self.BOOL = Analyzer.BOOL

    def emit(self, text=""):
        line = "    " * self.indent_level + text
        if self.current_output is not None:
            self.current_output.append(line)

    def push(self):
        self.indent_level += 1

    def pop(self):
        self.indent_level = max(0, self.indent_level - 1)

    def get_op_symbol(self, op_value):
        """Mapea operadores Python a símbolos C++."""
        if op_value == 'and': return '&&'
        if op_value == 'or': return '||'
        if op_value == '**': return '*' 
        return op_value

    def cpp_type_name(self, t):
        if t is None or t.equals(self.ANY):
            return "std::any"
        
        if isinstance(t, str):
            tname = t.lower()
        else:
            tname = t.name.lower()

        if tname == 'int': return "int"
        if tname in ('float', 'double'): return "double"
        if tname == 'string': return "std::string"
        if tname == 'bool': return "bool"
        if tname == 'none': return "void"
        if tname == 'void': return "void"
        
        # Tipos compuestos (asumimos que 't' es un objeto Type si no es ANY o None)
        if isinstance(t, Analyzer.Type):
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

        return "std::any"

    def get_expr_type(self, node):
        """Get the inferred type of an expression node"""
        return getattr(node, "inferred_type", self.ANY)

    def visit_module(self, node):
        self.func_declared_stack = [self.declared_main]
        self.indent_level = 0

        for child in node.children:
            if isinstance(child, str) and child.strip() == "":
                continue

            if is_node(child) and child.type == "function_def":
                self.current_output = self.function_lines
                self.inside_function = True
                self.visit(child)
                self.inside_function = False
            else:
                self.current_output = self.main_lines
                self.inside_function = False
                self.indent_level = 1
                self.visit(child)
                self.indent_level = 0

        # clear the stack when done
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
        self.current_function = name
        self.local_vars[name] = set()

        # --- existing param extraction ----
        params_node = node.children[0] if len(node.children) > 0 else None
        suite_node  = node.children[1] if len(node.children) > 1 else None

        params = []
        if params_node and is_node(params_node):
            for p in params_node.children:
                if is_node(p):
                    params.append(p.value)
                    self.local_vars[name].add(p.value)   # track parameters

        # ----------------------------------------------
        # MODIFICACIÓN CLAVE: OBTENER EL TIPO FINAL DESDE LA TABLA DE SÍMBOLOS
        # ----------------------------------------------
        func_type = self.symtab.lookup(name) if self.symtab else None 
        ret_type_str = "std::any"
        cpp_params = []

        if func_type and func_type.name == 'func':
            param_types = func_type.params[:-1]
            for idx, pname in enumerate(params):
                # Usar el tipo de parámetro inferido
                ptype = param_types[idx] if idx < len(param_types) else self.ANY
                cpp_params.append(f"{self.cpp_type_name(ptype)} {pname}")
            
            # El último parámetro es el tipo de retorno
            if len(func_type.params) >= 1:
                ret_type_str = self.cpp_type_name(func_type.params[-1])
        else:
            # Fallback si no se encuentra el tipo de función
            cpp_params = [f"std::any {p}" for p in params]
        # ----------------------------------------------

        # track declared vars
        self.func_declared_stack.append(set(params))

        # emit C++ function header
        self.emit(f"{ret_type_str} {name}({', '.join(cpp_params)}) {{")
        self.push()

        if suite_node:
            self.visit(suite_node)

        self.pop()
        self.emit("}\n")

        self.func_declared_stack.pop()
        self.current_function = None


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

        if is_node(target) and getattr(target, "type", None) == "identifier":
            target_name = target.value
        else:
            target_name = self.visit(target)

        # Track the variable as declared
        if self.func_declared_stack:
            self.func_declared_stack[-1].add(target_name)
        else:
            self.declared_main.add(target_name)

        if self.current_function:
            if self.current_function not in self.local_vars:
                self.local_vars[self.current_function] = set()
            self.local_vars[self.current_function].add(target_name)

        # Check if iterable is a range() call
        is_range_call = (is_node(iterable) and 
                        iterable.type == "call" and 
                        iterable.value == "range")

        if is_range_call:
            # Handle range() - generate standard C++ for loop
            args = iterable.children or []
            
            if len(args) == 1:
                # range(n) -> for(int i = 0; i < n; i++)
                end_expr = self.visit(args[0])
                self.emit(f"for (int {target_name} = 0; {target_name} < {end_expr}; {target_name}++) {{")
            elif len(args) == 2:
                # range(start, end) -> for(int i = start; i < end; i++)
                start_expr = self.visit(args[0])
                end_expr = self.visit(args[1])
                self.emit(f"for (int {target_name} = {start_expr}; {target_name} < {end_expr}; {target_name}++) {{")
            elif len(args) == 3:
                # range(start, end, step)
                start_expr = self.visit(args[0])
                end_expr = self.visit(args[1])
                step_expr = self.visit(args[2])
                # Determine comparison operator based on step (positive vs negative)
                # For simplicity, assume positive step and use <
                self.emit(f"for (int {target_name} = {start_expr}; {target_name} < {end_expr}; {target_name} += {step_expr}) {{")
            else:
                # Fallback for invalid range
                self.emit(f"for (int {target_name} = 0; {target_name} < 0; {target_name}++) {{")
        else:
            # Handle regular iterables (lists, etc.) - range-based for loop
            iterable_expr = self.visit(iterable)
            iter_type = self.get_expr_type(iterable)
            
            if iter_type and getattr(iter_type, "name", None) == 'list' and iter_type.params:
                elem_type = self.cpp_type_name(iter_type.params[0])
                self.emit(f"for ({elem_type} {target_name} : {iterable_expr}) {{")
            else:
                # Fallback to auto if type is unknown or complex
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

        t = self.get_expr_type(node)
        if t.equals(self.ANY) and self.symtab is not None:
            # Intenta obtener el tipo más actualizado del symtab
            tt = self.symtab.lookup(name)
            t = tt if tt is not None else self.ANY

        cpp_t = self.cpp_type_name(t)

        if self.current_function is None:
            self.global_vars.add(name)
        else:
            if self.current_function not in self.local_vars:
                self.local_vars[self.current_function] = set()
            self.local_vars[self.current_function].add(name)

        cur_declared = self.func_declared_stack[-1] if self.func_declared_stack else self.declared_main
        
        # Declarar si no ha sido declarada
        if name not in cur_declared:
            # Usar tipo inferido si es concreto, sino 'auto' o 'std::any'
            decl_type = cpp_t if not t.equals(self.ANY) else "auto"
            self.emit(f"{decl_type} {name} = {expr};")
            cur_declared.add(name)
        else:
            self.emit(f"{name} = {expr};")


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

        if is_node(expr_node) and expr_node.type == "assignment":
            self.visit(expr_node)
            return ""

        expr_cpp = self.visit(expr_node)
        
        if expr_cpp and expr_cpp.strip():
            if not (is_node(expr_node) and expr_node.type == "call" and expr_node.value == "print"):
                self.emit(f"{expr_cpp};")
        
        return ""

    # -------------------------------------------------------------
    # CORRECCIÓN CLAVE: visit_binary_op
    # Inyecta std::any_cast<T> en operaciones aritméticas
    # -------------------------------------------------------------
    def visit_binary_op(self, node):
        op = self.get_op_symbol(node.value)
        
        t_expr = self.get_expr_type(node) 
        t_left = self.get_expr_type(node.children[0])
        t_right = self.get_expr_type(node.children[1])
        
        left_code = self.visit(node.children[0])
        right_code = self.visit(node.children[1])
        
        def unwrap_any(code, inferred_type, target_type):
            """Inserta std::any_cast si el tipo inferido es ANY."""
            if inferred_type.equals(self.ANY):
                target_type_str = self.cpp_type_name(target_type)
                # Si el tipo es 'void', usamos el tipo numérico más probable: int
                if target_type_str in ('void', 'nullptr', 'std::any'):
                    target_type_str = 'int' 
                return f"std::any_cast<{target_type_str}>({code})"
            return code
            
        # Determinar si la operación es numérica o de comparación
        is_numeric_op = node.value in ('+', '-', '*', '/', '**')
        is_comparison_op = node.value in ('==', '!=', '<', '<=', '>', '>=')
        
        if is_numeric_op or is_comparison_op:
            # El tipo de destino para el cast es el tipo inferido de la expresión resultante
            # o INT si el resultado es booleano (para la comparación)
            cast_type = t_expr if t_expr.is_numeric() else self.INT
            
            # Solo si la operación es aritmética/comparativa y el tipo es ANY (por defecto de parámetro)
            if is_numeric_op or (is_comparison_op and (t_left.equals(self.ANY) or t_right.equals(self.ANY))):
                left_code = unwrap_any(left_code, t_left, cast_type)
                right_code = unwrap_any(right_code, t_right, cast_type)
        
        # Manejar Python's pow (**)
        if node.value == '**':
            return f"std::pow({left_code}, {right_code})"
            
        # Manejar la concatenación de strings (ya maneja la conversión implícita)
        if t_expr.equals(Analyzer.STRING):
            op = "+"
            
        return f"({left_code} {op} {right_code})"


    def visit_unary_op(self, node):
        operand = self.visit(node.children[0])
        op = node.value
        if op == 'not':
            return f"!({operand})"
        return f"{op}({operand})"

    def visit_comparison(self, node):
        # La lógica de any_cast ya fue integrada en visit_binary_op si se usa == o !=
        # Para el resto de comparaciones, necesitamos el mismo manejo de any_cast.
        return self.visit_binary_op(node)

    def visit_boolean_op(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = self.get_op_symbol(node.value)
            
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
                # 'float' -> 'double'
                cast_name = "double" if func_name == "float" else func_name
                # El código tiene un error: b = (a + static_cast<str>(b)); 
                # Se corrige a: b = (a + str(b)); y se usa la función helper str(b)
                if func_name == "str":
                    return f"str({arg_exprs[0]})"
                return f"static_cast<{cast_name}>({arg_exprs[0]})"
            return f"{func_name}()"

        if func_name == "len":
            if arg_exprs:
                return f"{arg_exprs[0]}.size()"
            return "0"

        if func_name == "range":
            # Esto debe ser manejado en la gramática o en un helper de C++.
            # Por ahora, dejamos el comentario.
            return f"/* range({', '.join(arg_exprs)}) */"

        return f"{func_name}({', '.join(arg_exprs)})"

    def visit_subscript(self, node):
        obj = self.visit(node.children[0])
        idx = self.visit(node.children[1])
        return f"{obj}[{idx}]"

    def visit_identifier(self, node):
        varname = node.value
        return varname

    def visit_number(self, node):
        return str(node.value)

    def visit_string(self, node):
        raw = node.value
        try:
            literal = ast.literal_eval(raw)
        except Exception:
            literal = raw[1:-1] if isinstance(raw, str) and len(raw) >= 2 else raw
        
        if isinstance(literal, str):
            escaped = literal.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
            return f'"{escaped}"'
        return raw


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
        
        list_type = self.get_expr_type(node)
        if list_type and list_type.name == 'list' and list_type.params:
            elem_cpp_type = self.cpp_type_name(list_type.params[0])
            return f"std::vector<{elem_cpp_type}>{{{items}}}"
        
        return f"std::vector<std::any>{{{items}}}"

    def visit_tuple(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        
        tuple_type = self.get_expr_type(node)
        if tuple_type and tuple_type.name == 'tuple' and tuple_type.params:
            types = ", ".join(self.cpp_type_name(p) for p in tuple_type.params)
            # Usamos std::make_tuple si los tipos son std::any para simplificar
            if any(t.equals(self.ANY) for t in tuple_type.params):
                return f"std::make_tuple({items})"
            return f"std::tuple<{types}>({items})"
        
        return f"std::make_tuple({items})"

    def visit_dict(self, node):
        items = []
        for c in node.children:
            if is_node(c) and c.type == "pair":
                items.append(self.visit(c))
        inner = ", ".join(items)
        
        dict_type = self.get_expr_type(node)
        if dict_type and dict_type.name == 'dict' and len(dict_type.params) >= 2:
            k_type = self.cpp_type_name(dict_type.params[0])
            v_type = self.cpp_type_name(dict_type.params[1])
            return f"std::map<{k_type}, {v_type}>{{{inner}}}"
        
        return f"std::map<std::any, std::any>{{{inner}}}"

    def visit_set(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        
        set_type = self.get_expr_type(node)
        elem_type = self.ANY
        if set_type and set_type.name == 'set' and set_type.params:
            elem_type = set_type.params[0]
            
        return f"std::set<{self.cpp_type_name(elem_type)}>{{{items}}}"


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

    try:
        p = Parser.Parser(debug=False)
        p.build()
        ast_tree = p.parse(src)
    except NameError:
        print("Error: The Parser class from Parser.py is required but not available.")
        sys.exit(1)


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