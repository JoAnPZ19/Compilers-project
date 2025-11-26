# /mnt/data/Analyzer.py
# Analyzer: recorre AST e infiere tipos simples (int/double/string/bool/none/list/dict/any/func/tuple)

from collections import deque
import ast

# --- Tipos simples ---
class Type:
    def __init__(self, name, params=None):
        self.name = name
        self.params = params or []

    def __repr__(self):
        if not self.params:
            return self.name
        inner = ", ".join(repr(p) for p in self.params)
        return f"{self.name}<{inner}>"

    def is_numeric(self):
        return self.name in ('int', 'double')

    def equals(self, other):
        if other is None:
            return False
        if not isinstance(other, Type):
            return False
        if self.name != other.name:
            return False
        if len(self.params) != len(other.params):
            return False
        for a, b in zip(self.params, other.params):
            if not a.equals(b):
                return False
        return True

# Builtin singletons
INT = Type('int')
DOUBLE = Type('double')
STRING = Type('string')
BOOL = Type('bool')
NONE = Type('none')
ANY = Type('any')

# --- Symbol table with scope stack ---
class Symbol:
    def __init__(self, name, type_):
        self.name = name
        self.type = type_

    def __repr__(self):
        return f"{self.name}:{self.type}"

class SymbolTable:
    def __init__(self):
        self.scopes = [dict()]

    def push(self):
        self.scopes.append({})

    def pop(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, type_):
        self.scopes[-1][name] = Symbol(name, type_)

    def update(self, name, type_):
        for s in reversed(self.scopes):
            if name in s:
                s[name].type = type_
                return
        self.declare(name, type_)

    def lookup(self, name):
        for s in reversed(self.scopes):
            if name in s:
                return s[name].type
        return None

    def current_scope(self):
        return self.scopes[-1]

    def __repr__(self):
        s = []
        for scope in self.scopes:
            items = ", ".join(f"{k}:{v.type}" for k,v in scope.items())
            s.append("{" + items + "}")
        return "SymbolTable(" + " | ".join(s) + ")"

def is_node(x):
    return hasattr(x, "type") and hasattr(x, "children")

class Analyzer:
    def __init__(self):
        self.symtab = SymbolTable()
        self.function_returns = {}
        self.errors = []
        self._debug = False
        self.type_history = {} 

    def analyze(self, node):
        self.visit(node)
        return self.symtab

    def annotate(self, node, t):
        if node is None:
            return None
        setattr(node, "inferred_type", t)
        return t

    def visit(self, node):
        if node is None:
            return None
        if isinstance(node, str):
            return None
        method = getattr(self, f"visit_{node.type}", self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        for c in getattr(node, "children", []) or []:
            self.visit(c)
        return None

    def visit_module(self, node):
        for child in node.children or []:
            if isinstance(child, str) and child.strip() == "":
                continue
            self.visit(child)

    def visit_suite(self, node):
        for child in node.children or []:
            if isinstance(child, str):
                continue
            self.visit(child)

    def visit_pass(self, node):
        return self.annotate(node, NONE)
    
    def record_type(self, name, t, node=None):
        """Record each type change for a variable for type evolution tracing."""
        if name not in self.type_history:
            self.type_history[name] = []

        lineno = getattr(node, "lineno", None)
        self.type_history[name].append((lineno, t))

        # --- Literals ---
    def visit_number(self, node):
        v = node.value
        if isinstance(v, int):
            return self.annotate(node, INT)
        else:
            return self.annotate(node, DOUBLE)

    def visit_string(self, node):
        raw = node.value
        try:
            literal = ast.literal_eval(raw)
        except Exception:
            literal = raw.strip("'\"")
        node.literal = literal
        return self.annotate(node, STRING)

    def visit_boolean(self, node):
        return self.annotate(node, BOOL)

    def visit_none(self, node):
        return self.annotate(node, NONE)

    def visit_identifier(self, node):
        t = self.symtab.lookup(node.value)
        if t is None:
            t = ANY
        return self.annotate(node, t)

    # --- Assignment ---
    def visit_assignment(self, node):
        name = node.value
        expr_node = node.children[0] if node.children else None
        t_expr = self.visit(expr_node) or ANY

        prev = self.symtab.lookup(name)
        if prev is None:
            self.symtab.declare(name, t_expr)
        else:
            if prev.equals(ANY):
                self.symtab.update(name, t_expr)
            elif prev.is_numeric() and t_expr.is_numeric():
                if prev.equals(DOUBLE) or t_expr.equals(DOUBLE):
                    self.symtab.update(name, DOUBLE)
                else:
                    self.symtab.update(name, INT)
            else:
                self.symtab.update(name, t_expr)

        # AFTER updating the final type in the symbol table:
        final_type = self.symtab.lookup(name)
        self.record_type(name, final_type, node)

        return self.annotate(node, final_type)

    def visit_expression_stmt(self, node):
        if not node.children:
            return None
        child = node.children[0]
        if is_node(child) and child.type in ("assignment", "augmented_assignment"):
            return self.visit(child)
        return self.visit(child)

    # --- Binary ops ---
    def visit_binary_op(self, node):
        left_node = node.children[0]
        right_node = node.children[1]
        op = node.value

        # Inferimos tipos de los hijos
        t_left = self.visit(left_node) or ANY
        t_right = self.visit(right_node) or ANY

        # Detectores útiles
        left_is_ident = is_node(left_node) and getattr(left_node, "type", None) == "identifier"
        right_is_ident = is_node(right_node) and getattr(right_node, "type", None) == "identifier"
        left_is_string_literal = getattr(left_node, "type", None) == "string"
        right_is_string_literal = getattr(right_node, "type", None) == "string"

        # Helper: actualizar symbol table y registrar historial si actualizamos un identificador
        def promote_ident_to(name, new_type, node_ref=None):
            prev = self.symtab.lookup(name)
            if prev is None:
                self.symtab.declare(name, new_type)
                self.record_type(name, new_type, node_ref)
            else:
                # Si prev es ANY o distinto a new_type, actualizamos (con reglas numéricas)
                if prev.equals(ANY):
                    self.symtab.update(name, new_type)
                    self.record_type(name, new_type, node_ref)
                elif prev.is_numeric() and new_type.is_numeric():
                    # promover int->double si aplica
                    if prev.equals(DOUBLE) or new_type.equals(DOUBLE):
                        self.symtab.update(name, DOUBLE)
                        self.record_type(name, DOUBLE, node_ref)
                    else:
                        self.symtab.update(name, INT)
                        self.record_type(name, INT, node_ref)
                else:
                    # si hay conflicto tipo (ej: string vs int), preferimos new_type only if prev==ANY handled above.
                    # No forzamos sobreescritura arbitraria; dejamos prev y señalizamos error si viene una operación incompatible.
                    pass

        # -- Regla 1: Si cualquiera es literal string y operador '+' => concatenación string
        if op == '+' and (left_is_string_literal or right_is_string_literal):
            # Promocionar el identificador opuesto a string si era ANY
            if left_is_string_literal and right_is_ident:
                promote_ident_to(right_node.value, STRING, right_node)
                t_right = self.symtab.lookup(right_node.value) or t_right
            if right_is_string_literal and left_is_ident:
                promote_ident_to(left_node.value, STRING, left_node)
                t_left = self.symtab.lookup(left_node.value) or t_left
            return self.annotate(node, STRING)

        # -- Regla 2: Si ambos ya son string inferidos => string (concatenación)
        if t_left.equals(STRING) and t_right.equals(STRING):
            if op == '+':
                return self.annotate(node, STRING)
            else:
                self.errors.append(f"Incompatible operator '{op}' for strings")
                return self.annotate(node, ANY)

        # -- Regla 3: Si uno es literal numérico y el otro es identificador ANY, promovemos el identificador
        # Detectar literal por el nodo hijo
        if left_is_ident and t_left.equals(ANY) and t_right.is_numeric():
            # Promover left identificador al tipo de right (INT/DOUBLE)
            promote_ident_to(left_node.value, t_right, left_node)
            t_left = self.symtab.lookup(left_node.value) or t_left

        if right_is_ident and t_right.equals(ANY) and t_left.is_numeric():
            promote_ident_to(right_node.value, t_left, right_node)
            t_right = self.symtab.lookup(right_node.value) or t_right

        # -- Regla 4: Operaciones numéricas normales
        if t_left.is_numeric() and t_right.is_numeric():
            # division fuerza double
            if op == '/':
                return self.annotate(node, DOUBLE)
            # si cualquiera es DOUBLE -> DOUBLE
            if t_left.equals(DOUBLE) or t_right.equals(DOUBLE):
                return self.annotate(node, DOUBLE)
            return self.annotate(node, INT)

        # -- Regla 5: Mezcla STRING <-> NUMERIC => incompatible (no forzamos string)
        if (t_left.equals(STRING) and t_right.is_numeric()) or (t_right.equals(STRING) and t_left.is_numeric()):
            self.errors.append(f"Incompatible operands for '{op}': STRING and NUMERIC")
            return self.annotate(node, ANY)

        # -- Comparisons y booleanos
        if op in ('==', '!=', '<', '<=', '>', '>='):
            return self.annotate(node, BOOL)

        if op in ('and', 'or', '&&', '||'):
            return self.annotate(node, BOOL)

        # -- Si alguno es ANY y no hemos tomado decisión -> ANY
        if t_left.equals(ANY) or t_right.equals(ANY):
            return self.annotate(node, ANY)

        # Fallback conservador
        return self.annotate(node, ANY)


    def visit_unary_op(self, node):
        operand = node.children[0]
        ot = self.visit(operand)
        if node.value == 'not':
            return self.annotate(node, BOOL)
        if ot and ot.is_numeric():
            return self.annotate(node, ot)
        return self.annotate(node, ANY)

    def visit_comparison(self, node):
        self.visit(node.children[0])
        self.visit(node.children[1])
        return self.annotate(node, BOOL)

    def visit_boolean_op(self, node):
        self.visit(node.children[0])
        self.visit(node.children[1])
        return self.annotate(node, BOOL)

    # --- Calls ---
    def visit_call(self, node):
        arg_types = [self.visit(a) or ANY for a in (node.children or [])]

        if isinstance(node.value, str):
            fn = node.value.lower()
            
            # Built-in type conversions
            if fn == "str":
                return self.annotate(node, STRING)
            if fn == "int":
                return self.annotate(node, INT)
            if fn == "float":
                return self.annotate(node, DOUBLE)
            if fn == "bool":
                return self.annotate(node, BOOL)
                
            # Other builtins
            if fn == "print":
                return self.annotate(node, NONE)
            if fn == "len":
                return self.annotate(node, INT)
            if fn == "range":
                return self.annotate(node, Type('list', [INT]))

        # User-defined function
        if isinstance(node.value, str):
            ftype = self.symtab.lookup(node.value)
            if ftype and isinstance(ftype, Type) and ftype.name == 'func' and ftype.params:
                ret = ftype.params[-1]
                return self.annotate(node, ret)

        return self.annotate(node, ANY)

    # --- Function defs ---
    def visit_function_def(self, node):
        name = node.value
        params_node = node.children[0] if len(node.children) > 0 else None
        suite_node = node.children[1] if len(node.children) > 1 else None

        params = []
        if params_node and is_node(params_node):
            for p in params_node.children:
                if is_node(p) and p.type == "parameter":
                    pname = p.value
                    params.append((pname, ANY))

        func_type = Type('func', [*(pt for (_n,pt) in params), ANY])
        self.symtab.declare(name, func_type)

        self.symtab.push()
        for pname, ptype in params:
            self.symtab.declare(pname, ptype)

        ret_types = []
        self._collect_returns(suite_node, ret_types)

        self.visit(suite_node)

        ret_final = NONE
        if ret_types:
            unified = ret_types[0]
            for rt in ret_types[1:]:
                if unified.is_numeric() and rt.is_numeric():
                    unified = DOUBLE if (unified.equals(DOUBLE) or rt.equals(DOUBLE)) else INT
                elif not unified.equals(rt):
                    unified = ANY
            ret_final = unified
        else:
            ret_final = NONE

        ftype = self.symtab.lookup(name)
        if ftype and isinstance(ftype, Type) and ftype.name == 'func':
            ftype.params = ftype.params[:-1] + [ret_final]
            self.symtab.update(name, ftype)
            self.function_returns[name] = ret_final

        self.symtab.pop()
        return self.annotate(node, Type('func', [*(pt for (_n,pt) in params), ret_final]))

    def _collect_returns(self, node, ret_types):
        if node is None:
            return
        if is_node(node) and node.type == "return":
            if node.children:
                expr = node.children[0]
                t = self.visit(expr)
                if t:
                    ret_types.append(t)
                else:
                    ret_types.append(NONE)
            else:
                ret_types.append(NONE)
            return
        for c in getattr(node, "children", []) or []:
            self._collect_returns(c, ret_types)

    # --- Lists / tuples / dicts / sets ---
    def visit_list(self, node):
        elem_types = []
        for c in node.children or []:
            t = self.visit(c) or ANY
            elem_types.append(t)
        if not elem_types:
            el = ANY
        else:
            el = elem_types[0]
            for et in elem_types[1:]:
                if el.is_numeric() and et.is_numeric():
                    el = DOUBLE if (el.equals(DOUBLE) or et.equals(DOUBLE)) else INT
                elif not el.equals(et):
                    el = ANY
        return self.annotate(node, Type('list', [el]))

    def visit_tuple(self, node):
        elems = [self.visit(c) or ANY for c in node.children or []]
        return self.annotate(node, Type('tuple', elems))

    def visit_dict(self, node):
        key_types, val_types = [], []
        for pair in node.children or []:
            if is_node(pair) and pair.type == "pair":
                kt = self.visit(pair.children[0]) or ANY
                vt = self.visit(pair.children[1]) or ANY
                key_types.append(kt)
                val_types.append(vt)
        if key_types:
            k = key_types[0]
            for kt in key_types[1:]:
                if not k.equals(kt):
                    k = ANY
            v = val_types[0]
            for vt in val_types[1:]:
                if not v.equals(vt):
                    v = ANY
        else:
            k = ANY; v = ANY
        return self.annotate(node, Type('dict', [k, v]))

    def visit_pair(self, node):
        self.visit(node.children[0])
        self.visit(node.children[1])

    def visit_subscript(self, node):
        ot = self.visit(node.children[0])
        it = self.visit(node.children[1])
        if ot and isinstance(ot, Type) and ot.name == 'list' and ot.params:
            return self.annotate(node, ot.params[0])
        if ot and isinstance(ot, Type) and ot.name == 'dict' and len(ot.params) >= 2:
            return self.annotate(node, ot.params[1])
        return self.annotate(node, ANY)

    def visit_parameter(self, node):
        return None

    def visit_if(self, node):
        self.visit(node.children[0])
        self.visit(node.children[1])
        if len(node.children) > 2:
            self.visit(node.children[2])

    def visit_elif(self, node):
        self.visit(node.children[0])
        self.visit(node.children[1])

    def visit_else(self, node):
        if node.children:
            self.visit(node.children[0])

    def visit_while(self, node):
        self.visit(node.children[0])
        self.visit(node.children[1])

    def visit_for(self, node):
        target = node.children[0]
        iterable = node.children[1]
        suite = node.children[2]
        it = self.visit(iterable)
        if target and is_node(target) and target.type == "identifier":
            tname = target.value
            if it and isinstance(it, Type) and it.name == 'list' and it.params:
                self.symtab.declare(tname, it.params[0])
            else:
                self.symtab.declare(tname, ANY)
        self.visit(suite)