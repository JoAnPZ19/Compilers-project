# debug_tokens.py
import sys
sys.path.append('.')  # para cargar los módulos locales
import Lexer

if len(sys.argv) < 2:
    print("Uso: python debug_tokens.py <archivo>")
    sys.exit(1)

fname = sys.argv[1]
with open(fname, "r", encoding="utf-8") as f:
    src = f.read()

lex = Lexer.IndentLexer()
lex.input(src)

paren_stack = []  # stack of (token, lineno, col approximate)
line_positions = src.splitlines(True)

def token_pos(tok):
    # approximate column: find tok.value in its line (best-effort)
    try:
        linetext = line_positions[tok.lineno - 1]
        col = linetext.find(str(tok.value))
        if col == -1:
            col = 0
    except Exception:
        col = 0
    return col

print("=== TOKENS (lineno, type, value) and bracket nesting ===")
count = 0
while True:
    tok = lex.token()
    if not tok:
        break
    count += 1
    col = token_pos(tok)
    t = f"{tok.lineno:3} {tok.type:12} {repr(tok.value):30} col={col}"
    # update stack for brackets
    if tok.type in ('LPAREN', 'LBRACKET', 'LKEY'):
        paren_stack.append((tok.type, tok.lineno, col))
    elif tok.type in ('RPAREN', 'RBRACKET', 'RKEY'):
        # map closers to openers
        expected = None
        if tok.type == 'RPAREN': expected = 'LPAREN'
        if tok.type == 'RBRACKET': expected = 'LBRACKET'
        if tok.type == 'RKEY': expected = 'LKEY'
        if not paren_stack:
            t += "   <<UNMATCHED_CLOSER>>"
        else:
            opener, olineno, ocol = paren_stack[-1]
            if opener != expected:
                t += f"   <<MISMATCH opener={opener} at line {olineno}>>"
                paren_stack.pop()
            else:
                paren_stack.pop()
    print(t)
    # stop early if many tokens
    if count > 2000:
        print("... too many tokens, stopped")
        break

print("\n=== STACK AFTER TOKENIZATION ===")
if paren_stack:
    for opener, lineno, col in paren_stack:
        print(f"UNMATCHED opener {opener} at line {lineno} col={col}")
else:
    print("All brackets matched at lexer level.")

# Also re-run lexer but print tokens around the problematic area (line ~50-70)
print("\n=== TOKENS AROUND LINES 45-75 (for quick inspection) ===")
lex.input(src)
tok = lex.token()
while tok:
    if 45 <= tok.lineno <= 75:
        print(f"{tok.lineno:3} {tok.type:12} {repr(tok.value)}")
    tok = lex.token()

print("\nDone.")
