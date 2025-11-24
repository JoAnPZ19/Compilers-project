#!/usr/bin/env python3
import sys
import os
import Parser


# ======================================================
# === Symbol Table =====================================
# ======================================================

class SymbolInfo:
    def __init__(self, name, sym_type="any", declared_at=None):
        self.name = name
        self.type = sym_type
        self.declared_at = declared_at

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def define(self, name, info):
        self.symbols[name] = info

    def lookup(self, name):
        scope = self
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None


# ======================================================
# === Visitor Base =====================================
# ======================================================

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
        fn = getattr(self, f"visit_{node.type}", self.generic_visit)
        return fn(node)

    def generic_visit(self, node):
        result = ""
        for c in node.children:
            result += self.visit(c) or ""
        return result


# ======================================================
# === Primer Pase: Construcción de tabla de símbolos ====
# ======================================================

class SymbolTableVisitor(Visitor):
    def __init__(self):
        self.global_scope = SymbolTable(parent=None)
        self.current_scope = self.global_scope
        self.errors = []

    def enter_scope(self):
        new = SymbolTable(parent=self.current_scope)
        self.current_scope = new
        return new

    def exit_scope(self):
        self.current_scope = self.current_scope.parent

    def visit_module(self, node):
        for child in node.children:
            self.visit(child)
        return self.global_scope

    def visit_function_def(self, node):
        name = node.value
        self.global_scope.define(name, SymbolInfo(name, "function"))

        self.enter_scope()

        params_node = node.children[0]
        for p in params_node.children:
            self.current_scope.define(p.value, SymbolInfo(p.value, "param"))

        suite = node.children[1]
        self.visit(suite)

        self.exit_scope()

    def visit_assignment(self, node):
        var = node.value
        self.current_scope.define(var, SymbolInfo(var, "any"))
        self.visit(node.children[0])

    def visit_identifier(self, node):
        name = node.value
        if not self.current_scope.lookup(name):
            self.errors.append(
                f"Variable '{name}' usada sin definir (posible error)"
            )
        return name


# ======================================================
# === Segundo pase: Transpilación C++ ===================
# ======================================================

class CppVisitor(Visitor):
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.lines = []
        self.indent_level = 0

    def emit(self, text=""):
        self.lines.append("    " * self.indent_level + text)

    def push(self): self.indent_level += 1
    def pop(self): self.indent_level -= 1

    def get_code(self):
        header = [
            "#include <any>",
            "#include <iostream>",
            "#include <vector>",
            "#include <map>",
            "#include <set>",
            "using namespace std;",
            ""
        ]
        return "\n".join(header + self.lines)

    # === nodos ===

    def visit_module(self, node):
        for c in node.children:
            self.visit(c)
        return self.get_code()

    def visit_function_def(self, node):
        name = node.value
        params_node = node.children[0]
        suite_node = node.children[1]

        params = [f"std::any {p.value}" for p in params_node.children]
        cpp_params = ", ".join(params)

        self.emit(f"std::any {name}({cpp_params}) {{")
        self.push()
        self.visit(suite_node)
        self.pop()
        self.emit("}\n")

    def visit_suite(self, node):
        for c in node.children:
            if isinstance(c, str):
                continue
            self.visit(c)

    def visit_assignment(self, node):
        name = node.value
        expr = self.visit(node.children[0])
        self.emit(f"std::any {name} = {expr};")

    def visit_return(self, node):
        expr = self.visit(node.children[0])
        self.emit(f"return {expr};")

    def visit_expression_stmt(self, node):
        code = self.visit(node.children[0])
        if code.strip():
            self.emit(code + ";")

    def visit_binary_op(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value
        return f"std::any_cast<double>({left}) {op} std::any_cast<double>({right})"

    def visit_identifier(self, node):
        return node.value

    def visit_number(self, node):
        return str(node.value)

    def visit_string(self, node):
        v = node.value
        if v.startswith("'"):
            return '"' + v[1:-1] + '"'
        return v


# ======================================================
# === Main: parser → symbols → transpiler ==============
# ======================================================

def main():
    if len(sys.argv) < 2:
        print("Uso: python Visitor.py archivo.py")
        return

    filename = sys.argv[1]
    source = open(filename, "r", encoding="utf-8").read()

    parser = Parser.Parser(debug=False)
    parser.build()
    ast = parser.parse(source)

    # Pase 1: tabla de símbolos
    sym_builder = SymbolTableVisitor()
    global_scope = sym_builder.visit(ast)

    if sym_builder.errors:
        print("\n=== Errores detectados en tabla de símbolos ===")
        for e in sym_builder.errors:
            print(" -", e)

    # Pase 2: generar C++
    cpp_gen = CppVisitor(global_scope)
    cpp_code = cpp_gen.visit(ast)

    out_file = filename.replace(".py", ".cpp")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(cpp_code)

    print(f"\n✅ Código C++ generado en: {out_file}")


if __name__ == "__main__":
    main()
