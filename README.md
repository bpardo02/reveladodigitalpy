# Revelado Digital

Script en Python para convertir fotos escaneadas de negativos (color o blanco y negro) a positivos, eliminando el velo naranja y ajustando niveles automáticamente.

## Requisitos

```bash
pip install pillow numpy rawpy
```

## Uso

**Un solo archivo:**
```bash
python revelado_digital.py entrada.jpg salida.jpg
```

**Negativo en blanco y negro:**
```bash
python revelado_digital.py entrada.jpg salida.jpg --bw
```

**Carpeta completa (lote):**
```bash
python revelado_digital.py carpeta_negativos/ carpeta_positivos/ --lote
```

**Ajustar recorte de histograma y gamma:**
```bash
python revelado_digital.py entrada.jpg salida.jpg --clip 0.5 --gamma 1.1
```

## Parámetros

| Parámetro | Descripción | Default |
|---|---|---|
| `--bw` | Negativo en blanco y negro | color |
| `--lote` | Procesa todos los archivos de la carpeta de entrada | — |
| `--clip` | % de recorte de histograma (elimina polvo/rayas) | 0.5 |
| `--gamma` | Corrección de gamma (brillo medio) | 1.0 |

## Formatos soportados

- **Entrada:** JPG, PNG, TIFF, BMP, WEBP, y RAW (ARW, CR2, CR3, NEF, DNG, RAF, ORF, RW2)
- **Salida:** JPG, PNG, TIFF (no RAW)
