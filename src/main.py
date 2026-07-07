"""Punto de entrada del analizador Vec3D."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .parser import parse_source
from .semantic import SemanticAnalyzer


def analyze_source(source: str, show_ast: bool = False) -> int:
    ast, errors = parse_source(source)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    if ast is None:
        print("Error sintáctico: no se pudo construir el AST", file=sys.stderr)
        return 1

    if show_ast:
        print("=== AST ===")
        print(_ast_to_dict(ast))
        print()

    semantic = SemanticAnalyzer()
    if not semantic.analyze(ast):
        for err in semantic.errors:
            print(err, file=sys.stderr)
        return 1

    print("Análisis completado sin errores.")
    outputs = semantic.evaluate_program(ast)
    for line in outputs:
        print(f"Salida: {line}")
    return 0


def _ast_to_dict(node) -> dict:
    from dataclasses import asdict, is_dataclass

    if is_dataclass(node):
        data = asdict(node)
        data["__type__"] = type(node).__name__
        return data
    if isinstance(node, list):
        return [_ast_to_dict(n) for n in node]
    return node


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analizador léxico, sintáctico y semántico para Vec3D"
    )
    parser.add_argument("archivo", help="Archivo fuente .vec3d a analizar")
    parser.add_argument("--ast", action="store_true", help="Mostrar el AST en JSON")
    args = parser.parse_args(argv)

    path = Path(args.archivo)
    if not path.exists():
        print(f"Error: el archivo '{path}' no existe", file=sys.stderr)
        return 1

    return analyze_source(path.read_text(encoding="utf-8"), show_ast=args.ast)


if __name__ == "__main__":
    raise SystemExit(main())
