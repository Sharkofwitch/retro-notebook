import ast
import operator

# Unterstützte Operatoren (mehr kann man später hinzufügen)
ops = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}

def eval_expr(expr):
    try:
        tree = ast.parse(expr, mode='eval')

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                return ops[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = _eval(node.operand)
                return ops[type(node.op)](operand)
            elif isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Constant):  # für neuere Python-Versionen
                return node.value
            else:
                raise TypeError(f"Unsupported type: {type(node)}")

        return _eval(tree)
    except Exception as e:
        return f"Error: {e}"