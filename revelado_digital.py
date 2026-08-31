#!/usr/bin/env python3
"""
Revelado digital de negativos escaneados.

Convierte fotos de negativos (color o blanco y negro) a positivos,
eliminando el velo naranja de los negativos color y ajustando niveles
automáticamente por canal.

Uso:
    python revelado_digital.py entrada.jpg salida.jpg
    python revelado_digital.py entrada.jpg salida.jpg --bw
    python revelado_digital.py carpeta_negativos/ carpeta_positivos/ --lote
    python revelado_digital.py entrada.jpg salida.jpg --clip 0.5 --gamma 1.1

Dependencias:
    pip install pillow numpy rawpy
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import rawpy
from PIL import Image, ImageOps

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
EXTENSIONES_RAW = {".arw", ".cr2", ".cr3", ".nef", ".dng", ".raf", ".orf", ".rw2"}
EXTENSIONES_TODAS = EXTENSIONES_VALIDAS | EXTENSIONES_RAW


def estirar_canal(canal: np.ndarray, clip_pct: float) -> np.ndarray:
    """Estira el histograma de un canal usando percentiles, recortando
    outliers (polvo, rayas, bordes del negativo)."""
    lo, hi = np.percentile(canal, [clip_pct, 100 - clip_pct])
    if hi <= lo:
        return canal
    out = (canal.astype(np.float32) - lo) / (hi - lo)
    return np.clip(out, 0, 1)


def revelar_color(img: Image.Image, clip_pct: float, gamma: float) -> Image.Image:
    """Invierte y corrige un negativo a color, quitando el velo naranja
    mediante estiramiento de histograma independiente por canal RGB."""
    arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0

    # Invertir (negativo -> positivo)
    inv = 1.0 - arr

    # Estirar cada canal por separado: esto corrige el velo naranja,
    # que afecta a cada canal de forma distinta
    out = np.zeros_like(inv)
    for c in range(3):
        out[:, :, c] = estirar_canal(inv[:, :, c], clip_pct)

    # Corrección de gamma para ajustar el brillo medio
    out = np.power(out, 1.0 / gamma)

    out_img = Image.fromarray((out * 255).astype(np.uint8), mode="RGB")
    return out_img


def revelar_bn(img: Image.Image, clip_pct: float, gamma: float) -> Image.Image:
    """Invierte y corrige un negativo en blanco y negro."""
    gris = ImageOps.grayscale(img)
    arr = np.asarray(gris, dtype=np.float32) / 255.0
    inv = 1.0 - arr
    out = estirar_canal(inv, clip_pct)
    out = np.power(out, 1.0 / gamma)
    return Image.fromarray((out * 255).astype(np.uint8), mode="L")


def abrir_imagen(ruta: Path) -> Image.Image:
    """Abre un archivo normal (jpg/png/tiff) o un RAW (ARW, CR2, NEF, DNG...)."""
    if ruta.suffix.lower() in EXTENSIONES_RAW:
        with rawpy.imread(str(ruta)) as raw:
            # Demosaico "plano": sin auto-brillo ni curvas de cámara,
            # para no interferir con nuestro propio ajuste de niveles.
            rgb = raw.postprocess(
                use_camera_wb=True,
                no_auto_bright=True,
                output_bps=16,
                gamma=(1, 1),
            )
        return Image.fromarray((rgb / 256).astype(np.uint8), mode="RGB")
    return Image.open(ruta)


def procesar_archivo(ruta_in: Path, ruta_out: Path, bw: bool, clip_pct: float, gamma: float) -> None:
    if ruta_out.suffix.lower() in EXTENSIONES_RAW:
        print(
            f"Error: no se puede guardar en formato RAW ({ruta_out.suffix}). "
            "Usá .jpg, .png o .tif como salida.",
            file=sys.stderr,
        )
        sys.exit(1)

    img = abrir_imagen(ruta_in)
    img = ImageOps.exif_transpose(img)  # respeta orientación original

    resultado = revelar_bn(img, clip_pct, gamma) if bw else revelar_color(img, clip_pct, gamma)

    ruta_out.parent.mkdir(parents=True, exist_ok=True)
    resultado.save(ruta_out, quality=95)
    print(f"OK: {ruta_in.name} -> {ruta_out}")


def main() -> None:
    p = argparse.ArgumentParser(description="Revelado digital rápido de negativos escaneados")
    p.add_argument("entrada", help="Archivo o carpeta de entrada")
    p.add_argument("salida", help="Archivo o carpeta de salida")
    p.add_argument("--bw", action="store_true", help="Negativo en blanco y negro (por defecto: color)")
    p.add_argument("--lote", action="store_true", help="Procesar todos los archivos de una carpeta")
    p.add_argument("--clip", type=float, default=0.5, help="Porcentaje de recorte de histograma (default 0.5)")
    p.add_argument("--gamma", type=float, default=1.0, help="Corrección de gamma (default 1.0)")
    args = p.parse_args()

    entrada = Path(args.entrada)
    salida = Path(args.salida)

    if args.lote or entrada.is_dir():
        archivos = sorted(
            f for f in entrada.iterdir()
            if f.suffix.lower() in EXTENSIONES_TODAS
        )
        if not archivos:
            print(f"No se encontraron imágenes en {entrada}", file=sys.stderr)
            sys.exit(1)
        for f in archivos:
            destino = salida / f"{f.stem}_positivo.jpg"
            procesar_archivo(f, destino, args.bw, args.clip, args.gamma)
    else:
        procesar_archivo(entrada, salida, args.bw, args.clip, args.gamma)


if __name__ == "__main__":
    main()