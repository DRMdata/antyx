from importlib.resources import files
import base64


# ============================
#  CSS LOADER
# ============================

def load_css(name: str) -> str:
    """
    Returns the content of a CSS file inside antyx/styles/.
    """
    path = files("antyx.styles").joinpath(name)
    return path.read_text(encoding="utf-8")


def embed_css(name: str) -> str:
    """
    Returns a <style>...</style> block with the CSS content.
    """
    css = load_css(name)
    return f"<style>\n{css}\n</style>"


def embed_multiple_css(names: list[str]) -> str:
    """
    Embeds multiple CSS files into a single HTML block.
    """
    return "\n".join(embed_css(n) for n in names)


# ============================
#  ICONS / IMAGES (BASE64)
# ============================

def load_icon_b64(name: str) -> str:
    """
    Returns a base64-encoded string for an icon inside antyx/icons/.
    """
    path = files("antyx.icons").joinpath(name)
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def embed_icon_img(name: str, mime: str = None) -> str:
    """
    Returns an <img> tag with the icon embedded as base64.
    MIME type is inferred from extension if not provided.
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
    Generic loader for any file inside the antyx package.
    Example: load_raw("icons/ant_basic.png")
    """
    pkg, file = path.split("/", 1)
    full = files(f"antyx.{pkg}").joinpath(file)
    return full.read_bytes()


def load_text(path: str) -> str:
    """
    Generic text loader for any file inside antyx.
    """
    pkg, file = path.split("/", 1)
    full = files(f"antyx.{pkg}").joinpath(file)
    return full.read_text(encoding="utf-8")