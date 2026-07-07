"""Analizador semántico para Vec3D."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

from . import ast_nodes as ast


@dataclass
class Symbol:
    name: str
    kind: str  # vec | numero
    initialized: bool = False
    components: list[float] | None = None
    line: int = 0
    column: int = 0


@dataclass
class Scope:
    symbols: dict[str, Symbol] = field(default_factory=dict)
    parent: Scope | None = None

    def define(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Symbol | None:
        scope: Scope | None = self
        while scope:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None


class SemanticAnalyzer:
    def __init__(self):
        self.errors: list[str] = []
        self.scope = Scope()
        self.vector_values: dict[str, tuple[float, float, float]] = {}
        self._dim_errors: set[str] = set()

    def analyze(self, program: ast.Program) -> bool:
        self.errors = []
        self.scope = Scope()
        self.vector_values = {}
        self._dim_errors = set()
        for stmt in program.statements:
            self._analyze_statement(stmt, self.scope)
        return len(self.errors) == 0

    def _error(self, pos: ast.Position | None, message: str):
        if pos:
            self.errors.append(f"Error semántico [línea {pos.line}, columna {pos.column}]: {message}")
        else:
            self.errors.append(f"Error semántico: {message}")

    def _analyze_statement(self, stmt: object, scope: Scope):
        if isinstance(stmt, ast.VecDecl):
            self._analyze_vec_decl(stmt, scope)
        elif isinstance(stmt, ast.VarDecl):
            self._analyze_var_decl(stmt, scope)
        elif isinstance(stmt, ast.Assignment):
            self._analyze_assignment(stmt, scope)
        elif isinstance(stmt, ast.PrintStmt):
            self._analyze_expr(stmt.expr, scope)
        elif isinstance(stmt, ast.IfStmt):
            self._analyze_if(stmt, scope)

    def _analyze_vec_decl(self, decl: ast.VecDecl, scope: Scope):
        if isinstance(decl.init_expr, ast.VectorLiteral) and len(decl.init_expr.components) != 3:
            self._error(
                decl.pos,
                f"el vector '{decl.name}' tiene {len(decl.init_expr.components)} componentes; se esperaban exactamente 3",
            )
            self._dim_errors.add(decl.name)

        value_type = "error"
        if isinstance(decl.init_expr, ast.VectorLiteral) and len(decl.init_expr.components) != 3:
            value_type = "vec"
        else:
            value_type = self._analyze_expr(decl.init_expr, scope)
            if value_type != "vec":
                self._error(decl.pos, f"no se puede asignar un valor de tipo '{value_type}' a un vector")
                return

        components: list[float] | None = None
        if isinstance(decl.init_expr, ast.VectorLiteral):
            components = [float(c.value) for c in decl.init_expr.components if isinstance(c, ast.NumberLiteral)]

        if decl.name in scope.symbols:
            self._error(decl.pos, f"el vector '{decl.name}' ya fue declarado en este ámbito")
            return

        scope.symbols[decl.name] = Symbol(
            name=decl.name,
            kind="vec",
            initialized=True,
            components=components,
            line=decl.pos.line if decl.pos else 0,
            column=decl.pos.column if decl.pos else 0,
        )

        if components and len(components) == 3:
            self.vector_values[decl.name] = (components[0], components[1], components[2])

    def _analyze_var_decl(self, decl: ast.VarDecl, scope: Scope):
        initialized = decl.init_expr is not None
        if not scope.define(
            Symbol(
                name=decl.name,
                kind="numero",
                initialized=initialized,
                line=decl.pos.line if decl.pos else 0,
                column=decl.pos.column if decl.pos else 0,
            )
        ):
            self._error(decl.pos, f"la variable '{decl.name}' ya fue declarada en este ámbito")
            return
        if decl.init_expr:
            t = self._analyze_expr(decl.init_expr, scope)
            if t != "numero":
                self._error(decl.pos, f"no se puede asignar un valor de tipo '{t}' a una variable escalar")
            else:
                scope.symbols[decl.name].initialized = True

    def _analyze_assignment(self, assign: ast.Assignment, scope: Scope):
        symbol = scope.lookup(assign.name)
        if not symbol:
            self._error(assign.pos, f"la variable '{assign.name}' no ha sido declarada")
            return
        value_type = self._analyze_expr(assign.expr, scope)
        if symbol.kind == "numero" and value_type != "numero":
            self._error(assign.pos, f"no se puede asignar un valor de tipo '{value_type}' a una variable escalar")
        elif symbol.kind == "vec":
            if value_type != "vec":
                self._error(assign.pos, f"no se puede asignar un valor de tipo '{value_type}' a un vector")
            else:
                symbol.initialized = True
        else:
            symbol.initialized = True

    def _analyze_if(self, stmt: ast.IfStmt, scope: Scope):
        cond_type = self._analyze_expr(stmt.condition, scope)
        if cond_type != "booleano":
            self._error(stmt.pos, f"la condición de 'si' debe ser booleana, se recibió '{cond_type}'")
        then_scope = Scope(parent=scope)
        for s in stmt.then_body:
            self._analyze_statement(s, then_scope)
        if stmt.else_body:
            else_scope = Scope(parent=scope)
            for s in stmt.else_body:
                self._analyze_statement(s, else_scope)

    def _analyze_expr(self, expr: object, scope: Scope) -> str:
        if isinstance(expr, ast.NumberLiteral):
            return "numero"
        if isinstance(expr, ast.StringLiteral):
            return "cadena"
        if isinstance(expr, ast.Identifier):
            symbol = scope.lookup(expr.name)
            if not symbol:
                self._error(expr.pos, f"la variable '{expr.name}' no ha sido declarada")
                return "error"
            if not symbol.initialized:
                self._error(expr.pos, f"la variable '{expr.name}' se usa antes de ser asignada")
            return symbol.kind
        if isinstance(expr, ast.VectorLiteral):
            types = [self._analyze_expr(c, scope) for c in expr.components]
            if any(t != "numero" for t in types):
                self._error(expr.pos, "los componentes de un vector deben ser numéricos")
            if len(expr.components) != 3:
                self._error(expr.pos, f"un vector literal debe tener 3 componentes, se recibieron {len(expr.components)}")
            return "vec"
        if isinstance(expr, ast.DotCall):
            return self._analyze_dot(expr, scope)
        if isinstance(expr, ast.CrossCall):
            return self._analyze_cross(expr, scope)
        if isinstance(expr, ast.NormCall):
            return self._analyze_norm(expr, scope)
        if isinstance(expr, ast.UnaryOp):
            operand_type = self._analyze_expr(expr.operand, scope)
            if operand_type != "numero":
                self._error(expr.pos, f"el operador unario '{expr.op}' requiere un operando numérico")
            return "numero"
        if isinstance(expr, ast.BinaryOp):
            return self._analyze_binary(expr, scope)
        return "error"

    def _analyze_dot(self, call: ast.DotCall, scope: Scope) -> str:
        left = scope.lookup(call.left)
        right = scope.lookup(call.right)
        if not left:
            self._error(call.pos, f"el vector '{call.left}' no ha sido declarado")
            return "error"
        if not right:
            self._error(call.pos, f"el vector '{call.right}' no ha sido declarado")
            return "error"
        if left.kind != "vec" or right.kind != "vec":
            self._error(call.pos, "dot solo acepta operandos de tipo 'vec'")
            return "error"
        self._check_vector_dim(call.left, left, call.pos)
        self._check_vector_dim(call.right, right, call.pos)
        return "numero"

    def _analyze_cross(self, call: ast.CrossCall, scope: Scope) -> str:
        left = scope.lookup(call.left)
        right = scope.lookup(call.right)
        if not left:
            self._error(call.pos, f"el vector '{call.left}' no ha sido declarado")
            return "error"
        if not right:
            self._error(call.pos, f"el vector '{call.right}' no ha sido declarado")
            return "error"
        if left.kind != "vec" or right.kind != "vec":
            self._error(call.pos, "cross solo acepta operandos de tipo 'vec'")
            return "error"
        self._check_vector_dim(call.left, left, call.pos)
        self._check_vector_dim(call.right, right, call.pos)
        return "vec"

    def _analyze_norm(self, call: ast.NormCall, scope: Scope) -> str:
        symbol = scope.lookup(call.vector)
        if not symbol:
            self._error(call.pos, f"el vector '{call.vector}' no ha sido declarado")
            return "error"
        if symbol.kind != "vec":
            self._error(call.pos, f"'{call.vector}' no es un vector")
            return "error"
        self._check_vector_dim(call.vector, symbol, call.pos)
        return "numero"

    def _analyze_binary(self, expr: ast.BinaryOp, scope: Scope) -> str:
        left_type = self._analyze_expr(expr.left, scope)
        right_type = self._analyze_expr(expr.right, scope)

        if expr.op in {"+", "-"}:
            if left_type == "vec" and right_type == "vec":
                return "vec"
            if left_type == "numero" and right_type == "numero":
                return "numero"
            if left_type == "vec" and right_type == "numero":
                self._error(expr.pos, "no se puede sumar un escalar con un vector")
            elif left_type == "numero" and right_type == "vec":
                self._error(expr.pos, "no se puede sumar un escalar con un vector")
            else:
                self._error(
                    expr.pos,
                    f"no se puede aplicar '{expr.op}' entre valores de tipo '{left_type}' y '{right_type}'",
                )
            return "error"

        if expr.op == "*":
            if left_type == "numero" and right_type == "vec":
                return "vec"
            if left_type == "vec" and right_type == "numero":
                return "vec"
            if left_type == "vec" and right_type == "vec":
                self._error(expr.pos, "multiplicar dos vectores es ambiguo; use dot o cross")
                return "error"
            if left_type == "numero" and right_type == "numero":
                return "numero"
            self._error(
                expr.pos,
                f"no se puede multiplicar valores de tipo '{left_type}' y '{right_type}'",
            )
            return "error"

        if expr.op == "/":
            if left_type == "vec" and right_type == "numero":
                return "vec"
            if left_type == "numero" and right_type == "numero":
                return "numero"
            self._error(
                expr.pos,
                f"no se puede dividir valores de tipo '{left_type}' y '{right_type}'",
            )
            return "error"

        if expr.op in {"<", ">", "<=", ">=", "==", "!="}:
            if left_type != "numero" or right_type != "numero":
                self._error(
                    expr.pos,
                    f"no se puede comparar valores de tipo '{left_type}' y '{right_type}'",
                )
                return "error"
            return "booleano"

        return "error"

    def _check_vector_dim(self, name: str, symbol: Symbol, pos: ast.Position | None):
        if name in self._dim_errors:
            return
        if symbol.components and len(symbol.components) != 3:
            self._error(
                pos,
                f"el vector '{name}' tiene {len(symbol.components)} componentes; se esperaban exactamente 3",
            )

    def _eval_numeric_components(self, components: list[object], scope: Scope) -> tuple[float, float, float] | None:
        values: list[float] = []
        for comp in components:
            if isinstance(comp, ast.NumberLiteral):
                values.append(comp.value)
            elif isinstance(comp, ast.Identifier):
                sym = scope.lookup(comp.name)
                if not sym or sym.kind != "numero" or not sym.initialized:
                    return None
                values.append(0.0)
            else:
                return None
        if len(values) != 3:
            return tuple(values)  # type: ignore
        return (values[0], values[1], values[2])

    def evaluate_program(self, program: ast.Program) -> list[str]:
        outputs: list[str] = []
        env_num: dict[str, float] = {}
        env_vec: dict[str, tuple[float, float, float]] = dict(self.vector_values)

        def vec_value(name: str) -> tuple[float, float, float]:
            return env_vec[name]

        def eval_expr(expr: object):
            if isinstance(expr, ast.NumberLiteral):
                return expr.value
            if isinstance(expr, ast.StringLiteral):
                return expr.value
            if isinstance(expr, ast.Identifier):
                sym = self.scope.lookup(expr.name)
                if sym and sym.kind == "vec":
                    return env_vec[expr.name]
                return env_num[expr.name]
            if isinstance(expr, ast.VectorLiteral):
                return tuple(float(eval_expr(c)) for c in expr.components)
            if isinstance(expr, ast.DotCall):
                a = vec_value(expr.left)
                b = vec_value(expr.right)
                return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
            if isinstance(expr, ast.CrossCall):
                a = vec_value(expr.left)
                b = vec_value(expr.right)
                return (
                    a[1] * b[2] - a[2] * b[1],
                    a[2] * b[0] - a[0] * b[2],
                    a[0] * b[1] - a[1] * b[0],
                )
            if isinstance(expr, ast.NormCall):
                v = vec_value(expr.vector)
                return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
            if isinstance(expr, ast.UnaryOp):
                val = eval_expr(expr.operand)
                return -float(val) if expr.op == "-" else float(val)
            if isinstance(expr, ast.BinaryOp):
                left = eval_expr(expr.left)
                right = eval_expr(expr.right)
                if expr.op == "+":
                    if isinstance(left, tuple) and isinstance(right, tuple):
                        return (left[0] + right[0], left[1] + right[1], left[2] + right[2])
                    return float(left) + float(right)
                if expr.op == "-":
                    if isinstance(left, tuple) and isinstance(right, tuple):
                        return (left[0] - right[0], left[1] - right[1], left[2] - right[2])
                    return float(left) - float(right)
                if expr.op == "*":
                    if isinstance(left, (int, float)) and isinstance(right, tuple):
                        return (left * right[0], left * right[1], left * right[2])
                    if isinstance(left, tuple) and isinstance(right, (int, float)):
                        return (left[0] * right, left[1] * right, left[2] * right)
                    return float(left) * float(right)
                if expr.op == "/":
                    if isinstance(left, tuple) and isinstance(right, (int, float)):
                        return (left[0] / right, left[1] / right, left[2] / right)
                    return float(left) / float(right)
                ops = {
                    "<": lambda a, b: a < b,
                    ">": lambda a, b: a > b,
                    "<=": lambda a, b: a <= b,
                    ">=": lambda a, b: a >= b,
                    "==": lambda a, b: a == b,
                    "!=": lambda a, b: a != b,
                }
                return ops[expr.op](float(left), float(right))
            raise ValueError("expresión no evaluable")

        def run_statements(stmts: list[object]):
            for stmt in stmts:
                if isinstance(stmt, ast.VecDecl):
                    val = eval_expr(stmt.init_expr)
                    if isinstance(val, tuple):
                        env_vec[stmt.name] = val
                elif isinstance(stmt, ast.VarDecl) and stmt.init_expr:
                    env_num[stmt.name] = float(eval_expr(stmt.init_expr))
                elif isinstance(stmt, ast.Assignment):
                    val = eval_expr(stmt.expr)
                    sym = self.scope.lookup(stmt.name)
                    if sym and sym.kind == "vec":
                        env_vec[stmt.name] = val  # type: ignore
                    else:
                        env_num[stmt.name] = float(val)
                elif isinstance(stmt, ast.PrintStmt):
                    value = eval_expr(stmt.expr)
                    if isinstance(value, tuple):
                        outputs.append(f"({value[0]}, {value[1]}, {value[2]})")
                    else:
                        outputs.append(str(round(float(value), 4) if isinstance(value, float) else value))
                elif isinstance(stmt, ast.IfStmt):
                    if bool(eval_expr(stmt.condition)):
                        run_statements(stmt.then_body)
                    elif stmt.else_body:
                        run_statements(stmt.else_body)

        run_statements(program.statements)
        return outputs
