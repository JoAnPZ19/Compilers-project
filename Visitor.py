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
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.symtab = analyzer.symtab
        self.type_history = analyzer.type_history if hasattr(analyzer, "type_history") else {}
        self.function_returns = analyzer.function_returns if hasattr(analyzer, "function_returns") else {}

        self.lines = []
        self.indent_level = 0
        self.top_level_statements = []
        self.inside_function = False
        self.declared_main = set()
        self.func_declared_stack = []
        self.current_function = None
        # When inside a function, these control numeric forcing
        self.current_function_numeric = False
        self.current_function_numeric_type = None  # "int" or "double"

    # --- Utilities ---
    def emit(self, text=""):
        self.lines.append("    " * self.indent_level + text)

    def push(self):
        self.indent_level += 1

    def pop(self):
            self.indent_level = max(0, self.indent_level - 1)

    def cpp_type(self, t):
        """
        Convierte un Type() propio del analyzer a un tipo C++.
        Reglas del usuario:
        - STRING literal → std::string
        - TODO lo demás numérico → double
        - Se soportan: int, double, bool, list, dict, tuple, func
        - NO USAR std::any
        """

        # ----- Caso 1: si viene como string directo (literal tipo)
        if isinstance(t, str):
            if t == "string":
                return "std::string"
            if t == "bool":
                return "bool"
            if t == "none":
                return "void"
            return "double"

        # Si no tiene nombre de tipo, fallback double
        name = getattr(t, "name", None)
        params = getattr(t, "params", [])

        # ----- Tipos primitivos -----
        if name == "string":
            return "std::string"
        if name == "bool":
            return "bool"
        if name in ("int", "double"):
            return "double"   # Regla del usuario: todo numérico -> double
        if name == "none":
            return "void"

        # ----- Listas -----
        if name == "list" and params:
            elem = params[0]
            return f"std::vector<{self.cpp_type(elem)}>"

        # ----- Diccionarios -----
        if name == "dict" and len(params) >= 2:
            k = self.cpp_type(params[0])
            v = self.cpp_type(params[1])
            return f"std::map<{k}, {v}>"

        # ----- Tuplas -----
        if name == "tuple" and params:
            inner = ", ".join(self.cpp_type(p) for p in params)
            return f"std::tuple<{inner}>"

        # ----- Funciones -----
        if name == "func":
            # Se infiere automáticamente
            return "auto"

        # ----- Fallback (NO usar std::any) -----
        return "double"


    def get_expr_type(self, node):
        return getattr(node, "inferred_type", None)

    # --- Module / main ---
    def visit_module(self, node):
        # collect functions first so signatures go above main
        for child in node.children or []:
            if isinstance(child, str):
                if child.strip() == "":
                    continue
            if is_node(child) and child.type == "function_def":
                self.visit(child)
            else:
                self.top_level_statements.append(child)

        includes = (
            "#include <any>\n"
            "#include <iostream>\n"
            "#include <string>\n"
            "#include <vector>\n"
            "#include <map>\n"
            "#include <set>\n"
            "#include <tuple>\n"
            "using namespace std;\n\n"
        )

        str_helper = (
            "// Helper function for str() conversion\n"
            "template<typename T>\n"
            "std::string str(T value) {\n"
            "    return std::to_string(value);\n"
            "}\n\n"
        )

        functions_cpp = "\n".join(self.lines)
        main = "int main(int argc, char *argv[]) {\n"
        for stmt in self.top_level_statements:
            line = self.visit(stmt)
            if line and line.strip():
                if line.strip().endswith(";"):
                    main += f"    {line}\n"
                else:
                    main += f"    {line};\n"
        main += "    return 0;\n}\n"

        return includes + str_helper + functions_cpp + "\n\n" + main

    # --- Helpers to inspect function body for strings / doubles ---
    def _scan_for_string_or_double(self, node):
        """Recursively scan node subtree.
        Return tuple(has_string_literal, has_double_literal).

        IMPORTANT: only *literal* string nodes (node.type == "string")
        count as strings for the 'force numeric' rule.
        We do NOT treat calls to str() or nodes with inferred_type=='string'
        as string markers for the whole function.
        """
        has_string = False
        has_double = False
        if node is None:
            return (False, False)

        ntype = getattr(node, "type", None)

        # Only literal nodes with type == "string" set has_string
        if ntype == "string":
            has_string = True

        # For doubles, use the analyzer's inference on number nodes (literal or annotated)
        if ntype == "number":
            nt = getattr(node, "inferred_type", None)
            if nt and getattr(nt, "name", None) == "double":
                has_double = True

        # Also consider explicit double inference anywhere (but do NOT treat inferred string)
        it = getattr(node, "inferred_type", None)
        if it and getattr(it, "name", None) == "double":
            has_double = True

        # Recurse
        for c in getattr(node, "children", []) or []:
            if isinstance(c, str):
                continue
            cs, cd = self._scan_for_string_or_double(c)
            has_string = has_string or cs
            has_double = has_double or cd

        return (has_string, has_double)


    # --- Function definitions (force numeric if no strings) ---
    def visit_function_def(self, node):
        name = node.value
        params_node = node.children[0] if len(node.children)>0 else None
        suite_node = node.children[1] if len(node.children)>1 else None

        # decide if function contains strings or doubles
        has_string = False
        has_double = False
        if suite_node:
            has_string, has_double = self._scan_for_string_or_double(suite_node)

        # If no strings -> force numeric function (Option A)
        if not has_string:
            self.current_function_numeric = True
            # choose numeric type: double if any double literal inside, else int
            self.current_function_numeric_type = "double" if has_double else "int"
        else:
            self.current_function_numeric = False
            self.current_function_numeric_type = None

        # get function type info from analyzer/symtab if available
        ftype = self.symtab.lookup(name)
        param_types = []
        ret_type = None
        if ftype and getattr(ftype, "name", None) == "func" and getattr(ftype, "params", None):
            param_types = ftype.params[:-1]
            ret_type = ftype.params[-1]
        else:
            ret_type = self.function_returns.get(name, None)

        # If we're forcing numeric, override param_types / ret_type accordingly
        if self.current_function_numeric:
            forced = ("int" if self.current_function_numeric_type=="int" else "double")
            # create simple Type-like placeholders (string names are okay for cpp_type)
            param_count = 0
            if params_node and is_node(params_node):
                param_count = len(params_node.children)
            param_types = [forced for _ in range(param_count)]
            ret_type = forced

        # build parameter declarations
        params = []
        if params_node and is_node(params_node):
            for idx, p in enumerate(params_node.children):
                if is_node(p) and p.type == "parameter":
                    pname = p.value
                    ptype = param_types[idx] if idx < len(param_types) else None
                    params.append((pname, ptype))

        # Generate signature using cpp_type (it accepts strings or Type objects)
        if self.current_function_numeric:
            ret_cpp = "double"
            # construir param_decls forzando double para cada parámetro
            param_decls = []
            for (n, _t) in params:
                param_decls.append(f"double {n}")
        else:
            ret_cpp = self.cpp_type(ret_type)
            param_decls = [f"{self.cpp_type(t)} {n}" if t is not None else f"std::any {n}" for (n,t) in params]

        # Emit function
        self.emit(f"{ret_cpp} {name}({', '.join(param_decls)}) {{")
        self.push()

        # Enter function context
        self.inside_function = True
        self.current_function = name
        self.func_declared_stack.append(set())

        # Visit body: but before that, if we're forcing numeric, ensure symbol table has param types set
        if self.current_function_numeric:
            # update symtab for param names
            if params_node and is_node(params_node):
                for idx, p in enumerate(params_node.children):
                    if is_node(p) and p.type == "parameter":
                        pname = p.value
                        ptype = param_types[idx] if idx < len(param_types) else None
                        # declare/override in current func scope
                        self.symtab.declare(pname, Type(ptype) if isinstance(ptype,str) else ptype)

        if suite_node:
            self.visit(suite_node)

        # Leave function
        self.pop()
        self.emit("}\n")
        self.func_declared_stack.pop()
        self.inside_function = False
        self.current_function = None
        self.current_function_numeric = False
        self.current_function_numeric_type = None

    # --- Control structures ---
    def visit_suite(self, node):
        for child in node.children or []:
            if isinstance(child, str):
                continue
            self.visit(child)

    def visit_if(self, node):
        cond = self.visit(node.children[0])
        self.emit(f"if ({cond}) {{")
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
                    elif item.type in ("else", "suite"):
                        self.emit("else {")
                        self.push()
                        self.visit(item.children[0] if item.children else item)
                        self.pop()
                        self.emit("}")

    def visit_elif(self, node):
        cond = self.visit(node.children[0])
        self.emit(f"else if ({cond}) {{")
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
        cond = self.visit(node.children[0])
        self.emit(f"while ({cond}) {{")
        self.push()
        self.visit(node.children[1])
        self.pop()
        self.emit("}")

    def visit_for(self, node):
        target = node.children[0]
        iterable = node.children[1]
        suite = node.children[2] if len(node.children)>2 else None

        target_name = self.visit(target)
        iterable_expr = self.visit(iterable)

        self.emit(f"for (auto {target_name} : {iterable_expr}) {{")
        self.push()
        if suite:
            self.visit(suite)
        self.pop()
        self.emit("}")

    # --- Statements ---
    def visit_assignment(self, node):
        name = node.value
        expr_node = node.children[0] if node.children else None
        expr = self.visit(expr_node) if expr_node else "/*missing_expr*/"

        # Determine desired cpp type for this variable
        declared_type = getattr(node, "inferred_type", None)
        # Detectar si la expresión es literal string
        is_string_literal = False
        if expr_node and getattr(expr_node, "type", None) == "string":
            is_string_literal = True

        if self.inside_function and self.current_function_numeric:
            # dentro de función numérica: forzamos double
            cpp_t = "double"
        else:
            # fuera de función: si analizer no dio tipo y no es string literal -> double
            if declared_type is None:
                if is_string_literal:
                    cpp_t = "std::string"
                else:
                    cpp_t = "double"
            else:
                cpp_t = self.cpp_type(declared_type)

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

    # --- Expressions ---
    def visit_expression_stmt(self, node):
        expr_node = node.children[0] if node.children else None
        if not expr_node:
            return ""
        expr_cpp = self.visit(expr_node)
        if self.inside_function:
            if expr_cpp and expr_cpp.strip():
                self.emit(f"{expr_cpp};")
            return ""
        else:
            return expr_cpp
        
    def wrap_any_cast(self, expr_str, node, target_cpp_type):
        """
        For our policy: treat any-unknown as numeric -> static_cast<double>(...)
        We avoid std::any_cast since we assume non-strings are doubles.
        """
        # Si node tiene tipo concreto no devolvemos cast
        node_t = getattr(node, "inferred_type", None)
        if node_t is not None and getattr(node_t, "name", None) != 'any':
            return expr_str

        # Forzamos static_cast al tipo objetivo (usualmente "double")
        if target_cpp_type == "double" or target_cpp_type == "int":
            return f"static_cast<{target_cpp_type}>({expr_str})"
        if target_cpp_type == "std::string":
            # si nos piden string, llamamos a helper str()
            return f"str({expr_str})"
        return expr_str

    def visit_binary_op(self, node):
        left_node = node.children[0]
        right_node = node.children[1]
        op = node.value

        left = self.visit(left_node)
        right = self.visit(right_node)

        # Detectar si alguno es STRING LITERAL
        left_is_literal_str  = getattr(left_node,  "type", None) == "string"
        right_is_literal_str = getattr(right_node, "type", None) == "string"

        # ============================================================
        # 1. CASO STRING — SOLO SI HAY LITERALES "...."
        # ============================================================
        if op == "+" and (left_is_literal_str or right_is_literal_str):
            # Ninguna inferencia puede quitar esto: concatenación string real
            return f"({left} + {right})"

        # ============================================================
        # 2. SI LA FUNCIÓN ESTÁ FORZADA A NUMÉRICA → SIEMPRE DOUBLE/INT
        # ============================================================
        if self.inside_function and self.current_function_numeric:
            target = "double" if self.current_function_numeric_type == "double" else "int"

            lt = getattr(left_node, "inferred_type", None)
            rt = getattr(right_node, "inferred_type", None)

            # Si ambos tienen tipo concreto → sin cast
            if lt and rt and lt.name != "any" and rt.name != "any":
                return f"({left} {op} {right})"

            # Si alguno es ANY → cast a numérico
            left_cast = (
                left if (lt and lt.name != "any") else self.wrap_any_cast(left, left_node, target)
            )
            right_cast = (
                right if (rt and rt.name != "any") else self.wrap_any_cast(right, right_node, target)
            )

            return f"({left_cast} {op} {right_cast})"

        # ============================================================
        # 3. CASO NORMAL: USAR inferred_type del nodo si es numérico
        # ============================================================
        result_type = getattr(node, "inferred_type", None)
        if result_type and result_type.name != "any" and result_type.name != "string":
            return f"({left} {op} {right})"

        # ============================================================
        # 4. Si ambos operandos son numéricos concretos → directo
        # ============================================================
        lt = getattr(left_node, "inferred_type", None)
        rt = getattr(right_node, "inferred_type", None)

        if lt and rt and lt.name != "any" and rt.name != "any" and lt.name != "string" and rt.name != "string":
            return f"({left} {op} {right})"

        # ============================================================
        # 5. ÚLTIMO RECURSO: CASTEAR A DOUBLE SI HAY ANY / mix raro
        # ============================================================
        lcast = self.wrap_any_cast(left, left_node, "double")
        rcast = self.wrap_any_cast(right, right_node, "double")
        return f"({lcast} {op} {rcast})"


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
        return f"({left} {op} {right})"

    def visit_boolean_op(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
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
            if self.inside_function:
                self.emit(f"std::cout << {join_expr} << std::endl;")
                return ""
            return f"std::cout << {join_expr} << std::endl"

        # type conversion helpers
        if func_name in ("str", "int", "float", "bool"):
            if arg_exprs:
                argn = args[0]
                argstr = arg_exprs[0]
                argt = getattr(argn, "inferred_type", None)
                if func_name == "str":
                    if argt and getattr(argt, "name", None) == "string":
                        return argstr
                    return f"str({argstr})"
                if func_name == "int":
                    return f"static_cast<int>({argstr})"
                if func_name == "float":
                    return f"static_cast<double>({argstr})"
                if func_name == "bool":
                    return f"static_cast<bool>({argstr})"
            return f"{func_name}()"

        if func_name == "len":
            if arg_exprs:
                return f"{arg_exprs[0]}.size()"
            return "0"

        if func_name == "range":
            if len(arg_exprs)==1:
                return f"/* range(0, {arg_exprs[0]}) */"
            return f"/* range({', '.join(arg_exprs)}) */"

        # user-defined function: respect signature if known
        if isinstance(func_name, str):
            ftype = self.symtab.lookup(func_name)
            # If callee is numeric-forced (i.e., inferred return numeric) we don't cast
            if ftype and getattr(ftype, "name", None) == "func" and getattr(ftype, "params", None):
                ret = ftype.params[-1]
                if getattr(ret, "name", None) in ("int", "double", "string", "bool"):
                    return f"{func_name}({', '.join(arg_exprs)})"
            return f"{func_name}({', '.join(arg_exprs)})"

        return f"{func_name}({', '.join(arg_exprs)})"

    def visit_subscript(self, node):
        obj = self.visit(node.children[0])
        idx = self.visit(node.children[1])
        return f"{obj}[{idx}]"

    def visit_identifier(self, node):
        return node.value

    def visit_number(self, node):
        v = node.value
        if isinstance(v, int):
            return str(v)
        return repr(v)

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
        list_type = getattr(node, "inferred_type", None)
        if list_type and getattr(list_type, "name", None) == 'list' and getattr(list_type, "params", None):
            elem = self.cpp_type(list_type.params[0])
            return f"std::vector<{elem}>{{{items}}}"
        return f"std::vector<std::any>{{{items}}}"

    def visit_tuple(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        tuple_type = getattr(node, "inferred_type", None)
        if tuple_type and getattr(tuple_type, "name", None) == 'tuple' and getattr(tuple_type, "params", None):
            types = ", ".join(self.cpp_type(p) for p in tuple_type.params)
            return f"std::tuple<{types}>({items})"
        return f"std::make_tuple({items})"

    def visit_dict(self, node):
        items = []
        for c in node.children:
            if is_node(c) and c.type == "pair":
                items.append(self.visit(c))
        inner = ", ".join(items)
        dict_type = getattr(node, "inferred_type", None)
        if dict_type and getattr(dict_type,"name",None) == 'dict' and getattr(dict_type,"params",None) and len(dict_type.params)>=2:
            k = self.cpp_type(dict_type.params[0]); v = self.cpp_type(dict_type.params[1])
            return f"std::map<{k}, {v}>{{{inner}}}"
        return f"std::map<std::any, std::any>{{{inner}}}"

    def visit_set(self, node):
        items = ", ".join(self.visit(c) for c in node.children)
        return f"std::set<std::any>{{{items}}}"

    def visit_parameter(self, node):
        return node.value

    def visit_pass(self, node):
        return ""

# end class
