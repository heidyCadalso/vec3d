"""Analizador léxico para Vec3D."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    VEC = auto()
    DOT = auto()
    CROSS = auto()
    NORM = auto()
    IMPRIMIR = auto()
    VAR = auto()
    SI = auto()
    SINO = auto()
    ID = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    EQ = auto()
    NE = auto()
    ASSIGN = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    SEMI = auto()
    COMMA = auto()
    EOF = auto()


RESERVED = {
    "vec": TokenType.VEC,
    "dot": TokenType.DOT,
    "cross": TokenType.CROSS,
    "norm": TokenType.NORM,
    "imprimir": TokenType.IMPRIMIR,
    "var": TokenType.VAR,
    "si": TokenType.SI,
    "sino": TokenType.SINO,
}


@dataclass
class Token:
    type: TokenType
    value: object
    line: int
    column: int


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.errors: list[str] = []

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.pos < len(self.source):
            self._skip_whitespace()
            if self.pos >= len(self.source):
                break
            start_line, start_col = self.line, self.column
            ch = self.source[self.pos]

            if ch == "\n":
                self._advance()
                continue

            if ch == "/" and self._peek(1) == "/":
                self._line_comment()
                continue

            if ch == "/" and self._peek(1) == "*":
                if not self._block_comment():
                    self.errors.append(
                        f"Error léxico [línea {start_line}, columna {start_col}]: comentario de bloque sin cerrar"
                    )
                continue

            if ch == '"':
                value = self._string()
                if value is None:
                    self.errors.append(
                        f"Error léxico [línea {start_line}, columna {start_col}]: cadena sin cerrar"
                    )
                else:
                    tokens.append(Token(TokenType.STRING, value, start_line, start_col))
                continue

            if ch.isdigit() or (ch == "-" and self._peek(1).isdigit()):
                tokens.append(Token(*self._number(start_line, start_col)))
                continue

            two_ops = {"<=": TokenType.LE, ">=": TokenType.GE, "==": TokenType.EQ, "!=": TokenType.NE}
            pair = self.source[self.pos : self.pos + 2]
            if pair in two_ops:
                self._advance(2)
                tokens.append(Token(two_ops[pair], pair, start_line, start_col))
                continue

            one_ops = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "<": TokenType.LT,
                ">": TokenType.GT,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                ";": TokenType.SEMI,
                ",": TokenType.COMMA,
                "=": TokenType.ASSIGN,
            }
            if ch in one_ops:
                self._advance()
                tokens.append(Token(one_ops[ch], ch, start_line, start_col))
                continue

            if ch.isalpha() or ch == "_":
                ident = self._identifier()
                token_type = RESERVED.get(ident, TokenType.ID)
                tokens.append(Token(token_type, ident, start_line, start_col))
                continue

            self.errors.append(
                f"Error léxico [línea {start_line}, columna {start_col}]: carácter inesperado '{ch}'"
            )
            self._advance()

        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else ""

    def _advance(self, count: int = 1):
        for _ in range(count):
            if self.pos < len(self.source):
                if self.source[self.pos] == "\n":
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.pos += 1

    def _skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in " \t\r":
            self._advance()

    def _line_comment(self):
        while self.pos < len(self.source) and self.source[self.pos] != "\n":
            self._advance()

    def _block_comment(self) -> bool:
        self._advance(2)
        while self.pos < len(self.source):
            if self.source[self.pos : self.pos + 2] == "*/":
                self._advance(2)
                return True
            self._advance()
        return False

    def _string(self) -> str | None:
        self._advance()
        chars: list[str] = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == '"':
                self._advance()
                return "".join(chars)
            if ch == "\\":
                nxt = self._peek(1)
                mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                if nxt in mapping:
                    chars.append(mapping[nxt])
                    self._advance(2)
                    continue
            chars.append(ch)
            self._advance()
        return None

    def _number(self, line: int, column: int) -> tuple[TokenType, object, int, int]:
        start = self.pos
        if self.source[self.pos] == "-":
            self._advance()
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self._advance()
        if self.pos < len(self.source) and self.source[self.pos] == ".":
            self._advance()
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                self._advance()
            return TokenType.FLOAT, float(self.source[start : self.pos]), line, column
        return TokenType.INT, int(self.source[start : self.pos]), line, column

    def _identifier(self) -> str:
        start = self.pos
        while self.pos < len(self.source) and (
            self.source[self.pos].isalnum() or self.source[self.pos] == "_"
        ):
            self._advance()
        return self.source[start : self.pos]
