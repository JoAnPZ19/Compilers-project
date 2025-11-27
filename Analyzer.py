from collections import deque
import ast

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
        self.scope_names = ["global"]

    def push(self, name="<scope>"):
        self.scopes.append({})
        self.scope_names.append(name)

    def pop(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.scope_names.pop()

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
        lines = []
        for i, (scope, scope_name) in enumerate(zip(self.scopes, self.scope_names)):
            items = []
            for k, v in scope.items():
                items.append(f"  {k}: {v.type}")
            if items:
                lines.append(f"Scope {i} ({scope_name}):")
                lines.extend(items)
            else:
                lines.append(f"Scope {i} ({scope_name}): <empty>")
        return "\n".join(lines)

def is_node(x):
    return hasattr(x, "type") and hasattr(x, "children")

class Analyzer:
    def __init__(self):
        self.symtab = SymbolTable()
        self.function_returns = {}
        self.errors = []
        self._debug = False
        self.ANY = ANY

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

        return self.annotate(node, t_expr)

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

        t_left = self.visit(left_node) or ANY
        t_right = self.visit(right_node) or ANY

        # String concatenation
        if op == '+' and (t_left.equals(STRING) or t_right.equals(STRING)):
            return self.annotate(node, STRING)

        # Both strings
        if t_left.equals(STRING) and t_right.equals(STRING):
            if op == '+':
                return self.annotate(node, STRING)
            else:
                self.errors.append(f"Incompatible operator '{op}' for strings")
                return self.annotate(node, ANY)

        # Numeric ops
        if t_left.is_numeric() and t_right.is_numeric():
            if t_left.equals(DOUBLE) or t_right.equals(DOUBLE):
                return self.annotate(node, DOUBLE)
            else:
                if op == '/':
                    return self.annotate(node, DOUBLE)
                return self.annotate(node, INT)

        # Comparisons
        if op in ('==', '!=', '<', '<=', '>', '>='):
            return self.annotate(node, BOOL)

        # Boolean ops
        if op in ('and', 'or', '&&', '||'):
            return self.annotate(node, BOOL)

        # ------------------------------------------------------------------
        # NUEVA REGLA: Si la operación es aritmética en tipos ANY, asumir INT.
        # (Esto resuelve la inferencia de tipo para `hola(a,b): return a + b`)
        # ------------------------------------------------------------------
        if op in ('+', '-', '*', '/', '**'):
            if t_left.equals(ANY) and t_right.equals(ANY):
                return self.annotate(node, INT)

        # Fallback to ANY
        if t_left.equals(ANY) or t_right.equals(ANY):
            return self.annotate(node, ANY)

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

    # --- Type Unification Logic (RECURSIVE FIX) ---
    def _unify_types(self, types):
        if not types:
            return NONE
        
        # Eliminar duplicados para simplificar el análisis
        unique_types = []
        for t in types:
            if t not in unique_types:
                unique_types.append(t)
        types = unique_types
        
        # CORRECCIÓN PARA RECURSIVIDAD (Priorizar concretos sobre ANY)
        if len(types) >= 2 and ANY in types:
            concrete_types = [t for t in types if t != ANY]
            
            # Si solo hay tipos ANY y tipos numéricos
            if all(t.is_numeric() for t in concrete_types):
                if any(t.equals(DOUBLE) for t in concrete_types):
                    return DOUBLE
                if any(t.equals(INT) for t in concrete_types):
                    return INT
            
            # Si solo hay tipos ANY y string
            if all(t.equals(STRING) for t in concrete_types):
                return STRING
                
            # Si solo hay tipos ANY y boolean
            if all(t.equals(BOOL) for t in concrete_types):
                return BOOL
        
        # Si ANY sigue siendo un tipo o fue el único tipo (incompatible o no se cumple la regla anterior)
        if ANY in types:
            return ANY

        # Lógica original de unificación de tipos concretos:
        if len(types) == 1:
            return types[0]
            
        # Unificar tipos numéricos
        if all(t.is_numeric() for t in types):
            return DOUBLE if any(t.equals(DOUBLE) for t in types) else INT

        # Si todos los tipos son el mismo tipo no numérico, devolver ese tipo
        if all(t.equals(types[0]) for t in types):
            return types[0]

        # Tipos incompatibles (ej. INT y STRING) resultan en ANY
        return ANY

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

        # Pre-declare function with ANY return type
        func_type = Type('func', [*(pt for (_n,pt) in params), ANY])
        self.symtab.declare(name, func_type)

        # Push new scope for function
        self.symtab.push(f"function:{name}")
        for pname, ptype in params:
            self.symtab.declare(pname, ptype)

        # Collect return types before visiting body
        ret_types = []
        self._collect_returns(suite_node, ret_types)

        # Visit function body
        self.visit(suite_node)

        # Determine final return type
        ret_final = NONE
        if ret_types:
            # USAMOS EL MÉTODO DE UNIFICACIÓN MEJORADO
            ret_final = self._unify_types(ret_types)
        
        # Update function type with actual return type in parent scope
        self.symtab.pop()
        
        # Update in global scope
        ftype = self.symtab.lookup(name)
        if ftype and isinstance(ftype, Type) and ftype.name == 'func':
            ftype.params = ftype.params[:-1] + [ret_final]
            self.symtab.update(name, ftype)
            self.function_returns[name] = ret_final

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
            # Usar el unificador para elementos de lista
            el = self._unify_types(elem_types)

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
            # Usar el unificador para llaves y valores de diccionario
            k = self._unify_types(key_types)
            v = self._unify_types(val_types)
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
            for item in node.children[2:]:
                self.visit(item)

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

        self.visit(iterable)

        if target.type == "identifier":
            name = target.value
            self.symtab.declare(name, self.ANY)

        self.visit(suite)