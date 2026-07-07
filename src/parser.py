"""Parser descendente recursivo para Vec3D."""

from __future__ import annotations

from . import ast_nodes as ast
from .lexer import Lexer, Token, TokenType


class ParseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors: list[str] = []

    def parse(self) -> ast.Program | None:
        try:
            statements = self._statement_list()
            self._expect(TokenType.EOF)
            return ast.Program(statements=statements)
        except ParseError as exc:
            if exc.message not in self.errors:
                self.errors.append(exc.message)
            return None

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def _expect(self, token_type: TokenType, label: str | None = None) -> Token:
        tok = self._current()
        if tok.type != token_type:
            expected = label or _token_label(token_type)
            raise ParseError(
                f"Error sintáctico [línea {tok.line}, columna {tok.column}]: "
                f"se esperaba {expected} antes de '{_token_text(tok)}'"
            )
        return self._advance()

    def _match(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _synchronize(self):
        while self._current().type != TokenType.EOF:
            if self._current().type == TokenType.SEMI:
                self._advance()
                return
            if self._current().type in {TokenType.VEC, TokenType.VAR, TokenType.IMPRIMIR, TokenType.SI, TokenType.ID}:
                return
            self._advance()

    def _statement_list(self) -> list[object]:
        statements: list[object] = []
        while self._match(TokenType.VEC, TokenType.VAR, TokenType.IMPRIMIR, TokenType.SI, TokenType.ID):
            try:
                statements.append(self._statement())
            except ParseError as exc:
                self.errors.append(exc.message)
                self._synchronize()
        return statements

    def _statement(self) -> object:
        tok = self._current()
        if tok.type == TokenType.VEC:
            return self._vec_decl()
        if tok.type == TokenType.VAR:
            return self._var_decl()
        if tok.type == TokenType.IMPRIMIR:
            return self._print_stmt()
        if tok.type == TokenType.SI:
            return self._if_stmt()
        if tok.type == TokenType.ID:
            return self._assignment()
        raise ParseError(
            f"Error sintáctico [línea {tok.line}, columna {tok.column}]: se esperaba una sentencia válida"
        )

    def _vec_decl(self) -> ast.VecDecl:
        pos = _pos(self._advance())
        name = self._expect(TokenType.ID, "un identificador").value
        self._expect(TokenType.ASSIGN, "'='")
        init_expr = self._expr()
        self._expect(TokenType.SEMI, "';'")
        return ast.VecDecl(name=name, init_expr=init_expr, pos=pos)

    def _var_decl(self) -> ast.VarDecl:
        pos = _pos(self._advance())
        name = self._expect(TokenType.ID, "un identificador").value
        init_expr = None
        if self._match(TokenType.ASSIGN):
            self._advance()
            init_expr = self._expr()
        self._expect(TokenType.SEMI, "';'")
        return ast.VarDecl(name=name, init_expr=init_expr, pos=pos)

    def _assignment(self) -> ast.Assignment:
        name = self._advance().value
        pos = _pos(self.tokens[self.pos - 1])
        self._expect(TokenType.ASSIGN, "'='")
        expr = self._expr()
        self._expect(TokenType.SEMI, "';'")
        return ast.Assignment(name=name, expr=expr, pos=pos)

    def _print_stmt(self) -> ast.PrintStmt:
        pos = _pos(self._advance())
        expr = self._expr()
        self._expect(TokenType.SEMI, "';'")
        return ast.PrintStmt(expr=expr, pos=pos)

    def _if_stmt(self) -> ast.IfStmt:
        pos = _pos(self._advance())
        self._expect(TokenType.LPAREN, "'('")
        condition = self._expr()
        self._expect(TokenType.RPAREN, "')'")
        then_body = self._block().statements
        else_body: list[object] = []
        if self._match(TokenType.SINO):
            self._advance()
            else_body = self._block().statements
        return ast.IfStmt(condition=condition, then_body=then_body, else_body=else_body, pos=pos)

    def _block(self) -> ast.Block:
        pos = _pos(self._expect(TokenType.LBRACE, "'{'"))
        statements = self._statement_list()
        self._expect(TokenType.RBRACE, "'}'")
        return ast.Block(statements=statements, pos=pos)

    def _vector_components(self) -> list[object]:
        self._expect(TokenType.LPAREN, "'('")
        components = [self._expr()]
        while self._match(TokenType.COMMA):
            self._advance()
            components.append(self._expr())
        self._expect(TokenType.RPAREN, "')'")
        return components

    def _looks_like_vector(self) -> bool:
        idx = self.pos + 1
        while idx < len(self.tokens):
            t = self.tokens[idx].type
            if t == TokenType.COMMA:
                return True
            if t in {TokenType.RPAREN, TokenType.EOF}:
                return False
            idx += 1
        return False

    def _expr(self) -> object:
        return self._expr_relational()

    def _expr_relational(self) -> object:
        left = self._expr_additive()
        while self._match(TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE, TokenType.EQ, TokenType.NE):
            op = self._advance().value
            right = self._expr_additive()
            left = ast.BinaryOp(op=op, left=left, right=right, pos=_pos(self.tokens[self.pos - 1]))
        return left

    def _expr_additive(self) -> object:
        left = self._expr_multiplicative()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._expr_multiplicative()
            left = ast.BinaryOp(op=op, left=left, right=right, pos=_pos(self.tokens[self.pos - 1]))
        return left

    def _expr_multiplicative(self) -> object:
        left = self._expr_unary()
        while self._match(TokenType.STAR, TokenType.SLASH):
            op = self._advance().value
            right = self._expr_unary()
            left = ast.BinaryOp(op=op, left=left, right=right, pos=_pos(self.tokens[self.pos - 1]))
        return left

    def _expr_unary(self) -> object:
        if self._match(TokenType.MINUS, TokenType.PLUS):
            op = self._advance().value
            operand = self._expr_unary()
            return ast.UnaryOp(op=op, operand=operand, pos=_pos(self.tokens[self.pos - 1]))
        return self._primary()

    def _primary(self) -> object:
        tok = self._current()
        if tok.type == TokenType.FLOAT:
            self._advance()
            return ast.NumberLiteral(value=float(tok.value), pos=_pos(tok))
        if tok.type == TokenType.INT:
            self._advance()
            return ast.NumberLiteral(value=float(tok.value), pos=_pos(tok))
        if tok.type == TokenType.STRING:
            self._advance()
            return ast.StringLiteral(value=tok.value, pos=_pos(tok))
        if tok.type == TokenType.ID:
            self._advance()
            return ast.Identifier(name=tok.value, pos=_pos(tok))
        if tok.type == TokenType.DOT:
            return self._dot_call()
        if tok.type == TokenType.CROSS:
            return self._cross_call()
        if tok.type == TokenType.NORM:
            return self._norm_call()
        if tok.type == TokenType.LPAREN:
            if self._looks_like_vector():
                return ast.VectorLiteral(components=self._vector_components(), pos=_pos(tok))
            self._advance()
            expr = self._expr()
            self._expect(TokenType.RPAREN, "')'")
            return expr
        raise ParseError(
            f"Error sintáctico [línea {tok.line}, columna {tok.column}]: se esperaba una expresión"
        )

    def _dot_call(self) -> ast.DotCall:
        pos = _pos(self._advance())
        self._expect(TokenType.LPAREN, "'('")
        left = self._expect(TokenType.ID, "un identificador").value
        self._expect(TokenType.COMMA, "','")
        right = self._expect(TokenType.ID, "un identificador").value
        self._expect(TokenType.RPAREN, "')'")
        return ast.DotCall(left=left, right=right, pos=pos)

    def _cross_call(self) -> ast.CrossCall:
        pos = _pos(self._advance())
        self._expect(TokenType.LPAREN, "'('")
        left = self._expect(TokenType.ID, "un identificador").value
        self._expect(TokenType.COMMA, "','")
        right = self._expect(TokenType.ID, "un identificador").value
        self._expect(TokenType.RPAREN, "')'")
        return ast.CrossCall(left=left, right=right, pos=pos)

    def _norm_call(self) -> ast.NormCall:
        pos = _pos(self._advance())
        self._expect(TokenType.LPAREN, "'('")
        vector = self._expect(TokenType.ID, "un identificador").value
        self._expect(TokenType.RPAREN, "')'")
        return ast.NormCall(vector=vector, pos=pos)


def _pos(tok: Token) -> ast.Position:
    return ast.Position(tok.line, tok.column)


def _token_label(token_type: TokenType) -> str:
    labels = {
        TokenType.SEMI: "';'",
        TokenType.ASSIGN: "'='",
        TokenType.LPAREN: "'('",
        TokenType.RPAREN: "')'",
        TokenType.LBRACE: "'{'",
        TokenType.RBRACE: "'}'",
        TokenType.COMMA: "','",
        TokenType.ID: "un identificador",
    }
    return labels.get(token_type, "un token válido")


def _token_text(tok: Token) -> str:
    if tok.type == TokenType.EOF:
        return "fin de archivo"
    return str(tok.value)


def parse_source(source: str) -> tuple[ast.Program | None, list[str]]:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    return program, lexer.errors + parser.errors
