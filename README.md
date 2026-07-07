# Vec3D — Analizador de vectores tridimensionales

Proyecto final de **Compiladores**. Implementa un analizador para **Vec3D**, un DSL para trabajar con vectores en R³: suma, producto punto, producto cruz y norma.

## Requisitos

- Python 3.10 o superior
- Sin dependencias externas

## Estructura

```
vec3d/
├── vec3d.py
├── src/
│   ├── lexer.py
│   ├── parser.py
│   ├── semantic.py
│   ├── ast_nodes.py
│   └── main.py
├── examples/
│   ├── prueba_valida.vec3d
│   ├── prueba_error_sintactico.vec3d
│   └── prueba_error_semantico.vec3d
└── docs/
    └── DOCUMENTO_TECNICO.pdf
```

## Ejecución

```bash
cd vec3d
py vec3d.py examples/prueba_valida.vec3d
```

Opción `--ast` para ver el árbol sintáctico.

## Ejemplo

```text
vec a = (1, 2, 3);
vec b = (4, 5, 6);
imprimir dot(a, b);
imprimir cross(a, b);
imprimir norm(a);
vec c = a + b;
imprimir c;
```

## Documentación

Ver `docs/DOCUMENTO_TECNICO.pdf`.

## Autor

Heidy cadalso Ramirez — Compiladores — Vec3D (Estudiante 6)
