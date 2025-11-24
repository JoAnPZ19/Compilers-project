# Analyzer.py
# Nuevo archivo: implementa tabla de símbolos y un inferidor simple.

from collections import deque

# --- Tipos simples ---
class Type:
    def __init__(self, name, params=None):
        self.name = name  # 'int', 'double', 'string', 'bool', 'none', 'list', 'dict', 'any', 'func'
        self.params = params or []  # para contenedores: e.g. list<int> -> params = [Type('int')]

    def __repr__(self):
        if not self.params:
            return self.name
        else:
            inner = ", ".join(repr(p) for p in self.params)
            return f"{self.name}<{inner}>"

    def is_numeric(self):
        return self.name in ('int', 'double')

    def equals(self, other):
        if other is None:
            return False
        if self.name != other.name:
            return False
        if len(self.params) != len(other.params):
            return False
        for a,b in zip(self.params, other.params):
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
        self.scopes = [dict()]  # list of dicts, last = current

    def push(self):
        self.scopes.append({})

    def pop(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, type_):
        self.scopes[-1][name] = Symbol(name, type_)

    def update(self, name, type_):
        # Update nearest scope where variable exists; else declare in current
        for s in reversed(self.scopes):
            if name in s:
                s[name].type = type_
                return
        # not found: declare in current
        self.declare(name, type_)

    def lookup(self, name):
        for s in reversed(self.scopes):
            if name in s:
                return s[name].type
        return None

    def current_scope(self):
        return self.scopes[-1]

    def __repr__(self):
        return "SymbolTable(" + " | ".join(str(s) for s in self.scopes) + ")"

# --- Analyzer: recorre AST e infiere tipos ---
def is_node(x):
    return hasattr(x, "type") and hasattr(x, "children")

class Analyzer:
    def __init__(self):
        self.symtab = SymbolTable()
        self.function_returns = {}  # name -> return type (inferred)
        self.errors = []

    def analyze(self, node):
        # Entrypoint: annotate tree with .inferred_type
        self.visit(node)
        return self.symtab

    def annotate(self, node, t):
        if node is None:
            return
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
        # default: visit children, if expression, don't infer
        for c in getattr(node, "children", []) or []:
            self.visit(c)
        return None

    # Module / suite / statements
    def visit_module(self, node):
        for child in node.children:
            self.visit(child)

    def visit_suite(self, node):
        for child in node.children:
            self.visit(child)

    def visit_pass(self, node):
        return self.annotate(node, NONE)

    # --- Literals ---
    def visit_number(self, node):
        # parser stores ints as int, decimals as DOUBLE
        v = node.value
        if isinstance(v, int):
            return self.annotate(node, INT)
        else:
            return self.annotate(node, DOUBLE)

    def visit_string(self, node):
        return self.annotate(node, STRING)

    def visit_boolean(self, node):
        return self.annotate(node, BOOL)

    def visit_none(self, node):
        return self.annotate(node, NONE)

    def visit_identifier(self, node):
        t = self.symtab.lookup(node.value)
        if t is None:
            # unknown -> ANY (deferred)
            t = ANY
        return self.annotate(node, t)

    # --- Assignment ---
    def visit_assignment(self, node):
        name = node.value
        expr = node.children[0] if node.children else None
        t_expr = self.visit(expr)
        if t_expr is None:
            t_expr = ANY
        # declare or update
        prev = self.symtab.lookup(name)
        if prev is None:
            self.symtab.declare(name, t_expr)
        else:
            # try to unify: if prev is ANY, set to expr; if same keep; if numeric mismatch promote to DOUBLE
            if prev.equals(ANY):
                self.symtab.update(name, t_expr)
            elif prev.is_numeric() and t_expr.is_numeric():
                # if either DOUBLE -> DOUBLE
                if prev.equals(DOUBLE) or t_expr.equals(DOUBLE):
                    self.symtab.update(name, DOUBLE)
                else:
                    self.symtab.update(name, INT)
            else:
                # incompatible -> keep prev but warn
                if not prev.equals(t_expr):
                    # best-effort: set to ANY
                    self.symtab.update(name, ANY)
                    self.errors.append(f"Type conflict for variable '{name}': {prev} vs {t_expr}")
        # annotate assignment node
        return self.annotate(node, self.symtab.lookup(name))

    # --- Binary ops ---
    def visit_binary_op(self, node):
        left = node.children[0]
        right = node.children[1]
        lt = self.visit(left)
        rt = self.visit(right)
        if lt is None: lt = ANY
        if rt is None: rt = ANY
        # numeric ops: + - * / pow etc. -> numeric promotion
        if lt.is_numeric() and rt.is_numeric():
            # DOUBLE if either DOUBLE
            if lt.equals(DOUBLE) or rt.equals(DOUBLE):
                res = DOUBLE
            else:
                res = INT
        elif lt.equals(STRING) or rt.equals(STRING):
            # string concatenation?
            res = STRING
        else:
            res = ANY
        return self.annotate(node, res)

    def visit_unary_op(self, node):
        operand = node.children[0]
        ot = self.visit(operand)
        if ot and ot.is_numeric():
            return self.annotate(node, ot)
        if node.value == 'not':
            return self.annotate(node, BOOL)
        return self.annotate(node, ANY)

    def visit_comparison(self, node):
        # comparisons -> bool
        self.visit(node.children[0])
        self.visit(node.children[1])
        return self.annotate(node, BOOL)

    def visit_boolean_op(self, node):
        self.visit(node.children[0])
        self.visit(node.children[1])
        return self.annotate(node, BOOL)

    def visit_expression_stmt(self, node):
        return self.visit(node.children[0]) if node.children else None

    # --- Calls ---
    def visit_call(self, node):
        # First visit args
        arg_types = []
        for a in node.children or []:
            arg_types.append(self.visit(a) or ANY)
        # Simple builtins:
        if node.value == "print":
            return self.annotate(node, NONE)
        # If function declared in table?
        ftype = self.symtab.lookup(node.value)
        if ftype and ftype.name == 'func':
            # function type: params..., return in params[-1]
            # here we return the return type if available
            ret = ftype.params[-1] if ftype.params else ANY
            return self.annotate(node, ret)
        # Unknown function: ANY
        return self.annotate(node, ANY)

    # --- Function defs ---
    def visit_function_def(self, node):
        # node.value: name; children: [parameters_node, suite_node]
        name = node.value
        params_node = node.children[0] if len(node.children) > 0 else None
        suite_node = node.children[1] if len(node.children) > 1 else None

        # prepare function scope
        # collect param names and default types = ANY
        params = []
        if params_node and is_node(params_node):
            for p in params_node.children:
                if is_node(p) and p.type == "parameter":
                    pname = p.value
                    params.append((pname, ANY))

        # declare function symbol with func signature (params..., return=ANY)
        func_type = Type('func', [*(pt for (_n,pt) in params), ANY])
        self.symtab.declare(name, func_type)

        # enter scope
        self.symtab.push()
        # declare params in new scope
        for pname, ptype in params:
            self.symtab.declare(pname, ptype)

        # visit body; find return statements and try to infer return type
        ret_types = []
        self._collect_returns(suite_node, ret_types)
        # analyze body (so assignments inside update symbol table)
        self.visit(suite_node)

        # now unify return types
        if ret_types:
            # unify numeric -> DOUBLE if mixture
            unified = ret_types[0]
            for rt in ret_types[1:]:
                if unified.is_numeric() and rt.is_numeric():
                    if unified.equals(DOUBLE) or rt.equals(DOUBLE):
                        unified = DOUBLE
                    else:
                        unified = INT
                elif not unified.equals(rt):
                    unified = ANY
            # update function symbol return type
            ftype = self.symtab.lookup(name)
            if ftype and ftype.name == 'func':
                # set last param as return
                ftype.params = ftype.params[:-1] + [unified]
                self.symtab.update(name, ftype)
                self.function_returns[name] = unified
        else:
            # no return statements -> return none
            ftype = self.symtab.lookup(name)
            if ftype and ftype.name == 'func':
                ftype.params = ftype.params[:-1] + [NONE]
                self.symtab.update(name, ftype)
                self.function_returns[name] = NONE

        # pop function scope
        self.symtab.pop()
        return self.annotate(node, Type('func', [*(pt for (_n,pt) in params), self.function_returns.get(name, ANY)]))

    def _collect_returns(self, node, ret_types):
        if node is None:
            return
        if is_node(node) and node.type == "return":
            if node.children:
                # infer the return expression type
                # NOTE: do not visit body here (we'll later visit), but infer type of the expression
                expr = node.children[0]
                t = self.visit(expr)
                if t:
                    ret_types.append(t)
            else:
                ret_types.append(NONE)
            return
        # else recurse
        for c in getattr(node, "children", []) or []:
            self._collect_returns(c, ret_types)

    # --- Lists / tuples / dicts / sets ---
    def visit_list(self, node):
        # infer element type as unified of children
        elem_types = []
        for c in node.children:
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
        # tuple of heterogeneous types -> list as any tuple type
        elems = [self.visit(c) or ANY for c in node.children]
        return self.annotate(node, Type('tuple', elems))

    def visit_dict(self, node):
        # map key->value: unify key types and value types
        key_types, val_types = [], []
        for pair in node.children:
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
        # returns nothing by itself; but visit children
        self.visit(node.children[0])
        self.visit(node.children[1])

    # --- subscripts / attributes ---
    def visit_subscript(self, node):
        # visit object and index
        ot = self.visit(node.children[0])
        it = self.visit(node.children[1])
        # if object is list<T> -> result is T
        if ot and ot.name == 'list' and ot.params:
            return self.annotate(node, ot.params[0])
        # if dict<K,V> and index type matches K -> V
        if ot and ot.name == 'dict' and len(ot.params) >= 2:
            return self.annotate(node, ot.params[1])
        return self.annotate(node, ANY)

    # --- parameter ---
    def visit_parameter(self, node):
        # name only, type inferred in function scope
        return None

    # --- others ---
    def visit_if(self, node):
        self.visit(node.children[0])  # condition
        self.visit(node.children[1])  # body
        if len(node.children) > 2:
            self.visit(node.children[2])  # elif/else

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
        # children: target, iterable, suite
        target = node.children[0]
        iterable = node.children[1]
        suite = node.children[2]
        it = self.visit(iterable)
        # if iterable is list<T> then declare target as T in for-scope
        if target and is_node(target) and target.type == "identifier":
            tname = target.value
            if it and it.name == 'list' and it.params:
                self.symtab.declare(tname, it.params[0])
            else:
                self.symtab.declare(tname, ANY)
        # analyze body
        self.visit(suite)
