from importlib.resources import files
from tempfile import NamedTemporaryFile
from typing import List
import base64
import os

# ============================
#  CSS LOADER
# ============================

def _resource_path(*parts: str):
    """Internal: devuelve un objeto Path-like para un recurso dentro del paquete antyx."""
    return files("antyx").joinpath(*parts)

def load_css(name: str) -> str:
    """
    Devuelve el contenido de un archivo CSS dentro de antyx/styles/.
    Lanza RuntimeError con mensaje claro si el recurso no está disponible.
    """
    try:
        path = _resource_path("styles", name)
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise RuntimeError(
            f"Recurso no encontrado: 'antyx/styles/{name}'. "
            "Asegúrate de que el archivo esté incluido en la distribución (package-data / MANIFEST.in)."
        )

def embed_css(name: str) -> str:
    """Devuelve un bloque <style>...</style> con el CSS embebido."""
    css = load_css(name)
    return f"<style>\n{css}\n</style>"

def embed_multiple_css(names: List[str]) -> str:
    """Embebe múltiples CSS en un único bloque HTML."""
    return "\n".join(embed_css(n) for n in names)

def list_styles() -> List[str]:
    """Lista los nombres de archivos presentes en antyx/styles/ (útil para depuración)."""
    try:
        folder = _resource_path("styles")
        return [p.name for p in folder.iterdir() if p.is_file()]
    except FileNotFoundError:
        return []

def has_style(name: str) -> bool:
    """True si el estilo existe empaquetado."""
    try:
        p = _resource_path("styles", name)
        return p.exists()
    except Exception:
        return False

# ============================
#  ICONS / IMAGES (BASE64)
# ============================

def load_icon_b64(name: str) -> str:
    """
    Devuelve una cadena base64 para un icono dentro de antyx/icons/.
    Lanza RuntimeError si no existe.
    """
    try:
        path = _resource_path("icons", name)
        data = path.read_bytes()
        return base64.b64encode(data).decode("utf-8")
    except FileNotFoundError:
        raise RuntimeError(f"Icono no encontrado: 'antyx/icons/{name}'")

def embed_icon_img(name: str, mime: str = None) -> str:
    """
    Devuelve una etiqueta <img> con el icono embebido en base64.
    MIME se infiere por extensión si no se proporciona.
    """
    if mime is None:
        if name.endswith(".png"):
            mime = "image/png"
        elif name.endswith(".svg"):
            mime = "image/svg+xml"
        else:
            mime = "application/octet-stream"

    b64 = load_icon_b64(name)
    return f'<img src="data:{mime};base64,{b64}" />'

# ============================
#  RAW FILE ACCESS
# ============================

def load_raw(path: str) -> bytes:
    """
    Carga bytes de un recurso dentro de antyx.
    Ejemplo: load_raw("icons/ant_basic.png")
    """
    pkg, file = path.split("/", 1)
    try:
        full = _resource_path(pkg, file)
        return full.read_bytes()
    except FileNotFoundError:
        raise RuntimeError(f"Recurso no encontrado: 'antyx/{path}'")

def load_text(path: str) -> str:
    """Carga texto de un recurso dentro de antyx."""
    pkg, file = path.split("/", 1)
    try:
        full = _resource_path(pkg, file)
        return full.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise RuntimeError(f"Recurso no encontrado: 'antyx/{path}'")

def extract_resource_to_temp(package: str, *path_parts: str, suffix: str = "") -> str:
    """
    Extrae un recurso empaquetado a un archivo temporal y devuelve su ruta.
    Uso: extract_resource_to_temp("antyx", "styles", "base.css", suffix=".css")
    """
    try:
        res = files(package).joinpath(*path_parts)
        with res.open("rb") as fh:
            tmp = NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(fh.read())
            tmp.flush()
            return tmp.name
    except FileNotFoundError:
        raise RuntimeError(f"Recurso no encontrado: '{package}/{'/'.join(path_parts)}'")