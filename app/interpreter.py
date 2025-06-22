import math
import operator
import re

# Unterstützte Operatoren für Berechnungen
OPS = {
    "^": operator.pow,
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}

FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
}

CONSTANTS = {
    "pi": math.pi,
    "π": math.pi,
    "e": math.e,
}

def make_user_function(interpreter, arglist, expr):
        def user_func(*actuals):
            local_vars = dict(zip(arglist, actuals))
            return interpreter.eval_expr_with_scope(expr, local_vars)
        return user_func

class RetroInterpreter:
    def __init__(self):
        self.functions = {}  # Name -> (arg_list, body_expr)
        self.env = {}  # Variablen speichern
        self.in_if_block = False
        self.if_condition = None
        self.if_lines_true = []
        self.if_lines_false = []
        self.collecting_else = False
        self.in_while_block = False
        self.while_condition = None
        self.while_lines = []
        self.in_for_block = False
        self.for_var = None
        self.for_start = None
        self.for_end = None
        self.for_step = 1
        self.for_lines = []

    def run_line(self, line):
        line = line.strip()

        if not line:
            return ""

        if self.in_for_block:
            if line.upper() == "NEXT":
                return self._run_for_block()
            else:
                self.for_lines.append(line)
                return ""

        if line.upper().startswith("FOR "):
            return self._start_for_block(line)

        if self.in_while_block:
            if line.upper() == "ENDWHILE":
                return self._run_while_block()
            else:
                self.while_lines.append(line)
                return ""

        # Schleifenbeginn
        if line.upper().startswith("WHILE "):
            return self._start_while_block(line)

        if self.in_if_block:
            if line.upper() == "ELSE":
                self.collecting_else = True
                return ""
            elif line.upper() == "ENDIF":
                return self._run_if_block()
            else:
                if self.collecting_else:
                    self.if_lines_false.append(line)
                else:
                    self.if_lines_true.append(line)
                return ""

        if line.upper().startswith("IF "):
            return self._start_if_block(line)

        if line.upper() == "HELP":
            return self._handle_help()

        if line.upper().startswith("LET "):
            return self.handle_assignment(line[4:].strip())

        elif line.upper().startswith("PRINT "):
            return self.handle_print(line[6:].strip())

        elif line.upper().startswith("DEF "):
            return self.handle_function_def(line[4:].strip())

        else:
            return self.eval_expr(line)

    def _handle_help(self):
        return (
            "Retro Notebook Help:\n"
            "LET var = expr       - Assign value to variable\n"
            "PRINT expr           - Evaluate and print expression\n"
            "INPUT var            - Ask for user input (deaktiviert)\n"
            "DEF f(x) = expr      - Define a function\n"
            "IF cond THEN ... ELSE ... ENDIF - Conditional execution\n"
            "WHILE cond DO ... ENDWHILE      - While loop\n"
            "FOR i = a TO b [STEP s] ... NEXT - For loop\n"
            "HELP                  - Show this help message"
        )

    def _start_for_block(self, line):
            match = re.match(r"FOR ([a-zA-Z_][a-zA-Z0-9_]*) = (.+?) TO (.+?)( STEP (.+))?$", line, re.IGNORECASE)
            if not match:
                return "Syntax Error in FOR"

            self.in_for_block = True
            self.for_var = match.group(1)
            self.for_start = self.eval_expr(match.group(2))
            self.for_end = self.eval_expr(match.group(3))
            self.for_step = self.eval_expr(match.group(5)) if match.group(5) else 1
            self.for_lines = []

            return ""

    def _run_for_block(self):
        self.in_for_block = False
        outputs = []

        i = self.for_start
        self.env[self.for_var] = i

        cmp = (lambda a, b: a <= b) if self.for_step > 0 else (lambda a, b: a >= b)

        while cmp(i, self.for_end):
            self.env[self.for_var] = i
            for line in self.for_lines:
                out = self.run_line(line)
                if out:
                    outputs.append(out)
            i += self.for_step

        return "\n".join(outputs)

    def _start_while_block(self, line):
        match = re.match(r"WHILE (.+?) DO", line, re.IGNORECASE)
        if not match:
            return "Syntax Error in WHILE"

        self.in_while_block = True
        self.while_condition = match.group(1)
        self.while_lines = []
        return ""
    
    def _run_while_block(self):
        self.in_while_block = False
        outputs = []

        while True:
            condition_result = self.eval_expr(self.while_condition)
            if isinstance(condition_result, str) and condition_result.startswith("Error"):
                return condition_result
            if not condition_result:
                break

            for line in self.while_lines:
                out = self.run_line(line)
                if out:
                    outputs.append(out)

        return "\n".join(outputs)

    def _start_if_block(self, line):
        match = re.match(r"IF (.+?) THEN", line, re.IGNORECASE)
        if not match:
            return "Syntax Error in IF"

        condition = match.group(1)
        self.in_if_block = True
        self.if_condition = condition
        self.if_lines_true = []
        self.if_lines_false = []
        self.collecting_else = False
        return ""  # nichts sofort ausgeben

    def _run_if_block(self):
        self.in_if_block = False
        result = self.eval_expr(self.if_condition)

        if isinstance(result, str) and result.startswith("Error"):
            return result

        lines = self.if_lines_true if result else self.if_lines_false
        outputs = []

        for line in lines:
            out = self.run_line(line)
            if out:
                outputs.append(out)

        return "\n".join(outputs)

    # Funktion zur Handhabung von Funktionsdefinitionen
    def handle_assignment(self, statement):
        match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)", statement)
        if not match:
            return "Syntax Error in LET"

        name, expr = match.groups()
        value = self.eval_expr(expr)
        self.env[name] = value
        return f"{name} = {value}"

    # Funktion zur Handhabung von PRINT-Anweisungen
    def handle_print(self, expr):
        value = self.eval_expr(expr)
        return f"{value}"

    # Funktion zur Handhabung von Funktionsdefinitionen
    def handle_function_def(self, statement):
        # Beispiel: square(x) = x^2
        match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)\s*=\s*(.+)", statement)
        if not match:
            return "Syntax Error in DEF"

        name, arg_str, body = match.groups()
        args = [arg.strip() for arg in arg_str.split(",") if arg.strip()]

        self.functions[name] = (args, body)
        return f"Function '{name}' defined"
    
   # Funktion zur Auswertung von Ausdrücken
    def eval_expr(self, expr):
        # Ersetze bekannte Konstanten
        for const, val in CONSTANTS.items():
            expr = re.sub(rf"\b{re.escape(const)}\b", str(val), expr)

        # Ersetze ^ durch ** für Potenzen
        expr = expr.replace("^", "**")

        # Benutzerdefinierte Funktionen
        user_funcs = {}

        for name, (args, body) in self.functions.items():
            user_funcs[name] = make_user_function(self, args, body)

        try:
            safe_globals = {**FUNCTIONS, **user_funcs, **self.env}
            return eval(expr, {"__builtins__": {}}, safe_globals)
        except Exception as e:
            return f"Error: {e}"
        
    def eval_expr_with_scope(self, expr, local_vars):
        expr = expr.replace("^", "**")
        for const, val in CONSTANTS.items():
            expr = re.sub(rf"\b{re.escape(const)}\b", str(val), expr)
        try:
            scope = {**FUNCTIONS, **self.env, **local_vars}
            return eval(expr, {"__builtins__": {}}, scope)
        except Exception as e:
            return f"Error in func: {e}"