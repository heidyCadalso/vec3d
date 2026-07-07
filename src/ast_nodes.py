"""Nodos del AST para Vec3D."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Position:
    line: int
    column: int


@dataclass(kw_only=True)
class Program:
    statements: list[object]
    pos: Position | None = None


@dataclass(kw_only=True)
class VecDecl:
    name: str
    init_expr: object
    pos: Position | None = None


@dataclass(kw_only=True)
class VarDecl:
    name: str
    init_expr: object | None = None
    pos: Position | None = None


@dataclass(kw_only=True)
class Assignment:
    name: str
    expr: object
    pos: Position | None = None


@dataclass(kw_only=True)
class PrintStmt:
    expr: object
    pos: Position | None = None


@dataclass(kw_only=True)
class IfStmt:
    condition: object
    then_body: list[object]
    else_body: list[object] = field(default_factory=list)
    pos: Position | None = None


@dataclass(kw_only=True)
class Block:
    statements: list[object]
    pos: Position | None = None


@dataclass(kw_only=True)
class BinaryOp:
    op: str
    left: object
    right: object
    pos: Position | None = None


@dataclass(kw_only=True)
class UnaryOp:
    op: str
    operand: object
    pos: Position | None = None


@dataclass(kw_only=True)
class NumberLiteral:
    value: float
    pos: Position | None = None


@dataclass(kw_only=True)
class StringLiteral:
    value: str
    pos: Position | None = None


@dataclass(kw_only=True)
class Identifier:
    name: str
    pos: Position | None = None


@dataclass(kw_only=True)
class VectorLiteral:
    components: list[object]
    pos: Position | None = None


@dataclass(kw_only=True)
class DotCall:
    left: str
    right: str
    pos: Position | None = None


@dataclass(kw_only=True)
class CrossCall:
    left: str
    right: str
    pos: Position | None = None


@dataclass(kw_only=True)
class NormCall:
    vector: str
    pos: Position | None = None
