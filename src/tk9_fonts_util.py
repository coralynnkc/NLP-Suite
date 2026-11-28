"""Make fonts on macOS + Tk 9 draw at the sizes the GUIs were laid out for (Tk 8.6's).

Tk 8.6 on the Mac drew a font of N points as N pixels (72 dpi). Tk 9 draws it as 4/3 N pixels and ignores
`tk scaling` for fonts, so every point-sized font in the Suite ("Courier", 12, "bold" ...) became a third wider and
the hand-placed rows ran off the window: 39 of 50 GUIs overflowed in gui_layout_gate.py on Tk 9, 1 on Tk 8.6
(27 Nov 2026). A negative size is in pixels and draws the same on both, so apply() turns a point size N into -N
wherever a font reaches Tk: widget options (creation, configure, canvas items, tags), ttk styles, tkinter.font.Font.
Nothing changes on Tk 8.6, Windows or Linux.
"""

import re
import sys

_SIZE_IN_STRING = re.compile(r"^(\{[^}]*\}|\S+)\s+(\d+)(\s.*)?$")
_applied = False


def needed(platform=None, tk_version=None):
    if platform is None:
        platform = sys.platform
    if tk_version is None:
        import tkinter

        tk_version = getattr(tkinter, "TkVersion", None)  # absent from gui_smoke's fake tkinter
    try:
        return platform == "darwin" and float(tk_version) >= 9
    except (TypeError, ValueError):  # a stubbed tkinter (tests, gui_smoke) has no real version
        return False


def px_font(value):
    """A font description with a positive point size, as the same number of pixels (a negative size)."""
    if isinstance(value, (tuple, list)) and len(value) >= 2 and isinstance(value[1], int) and value[1] > 0:
        return type(value)([value[0], -value[1], *value[2:]])
    if isinstance(value, str):
        m = _SIZE_IN_STRING.match(value)
        if m and int(m.group(2)) > 0:
            return f"{m.group(1)} -{m.group(2)}{m.group(3) or ''}"
    return value


def px_options(options):
    if isinstance(options, dict) and "font" in options:
        options = dict(options, font=px_font(options["font"]))
    return options


def apply():
    """Patch tkinter once, when needed (a Mac with Tk 9). Call before the first window is built."""
    global _applied
    if _applied or not needed():
        return
    import tkinter
    from tkinter import ttk
    import tkinter.font as tkfont

    _options = tkinter.Misc._options

    def options(self, cnf, kw=None):
        return _options(self, px_options(cnf), px_options(kw))

    tkinter.Misc._options = options

    _font_init, _font_configure = tkfont.Font.__init__, tkfont.Font.configure

    def font_init(self, root=None, font=None, name=None, exists=False, **opts):
        if isinstance(opts.get("size"), int) and opts["size"] > 0:
            opts["size"] = -opts["size"]
        _font_init(self, root, px_font(font), name, exists, **opts)

    def font_configure(self, **opts):
        if isinstance(opts.get("size"), int) and opts["size"] > 0:
            opts["size"] = -opts["size"]
        return _font_configure(self, **opts)

    tkfont.Font.__init__, tkfont.Font.configure = font_init, font_configure
    tkfont.Font.config = font_configure

    _style_configure = ttk.Style.configure

    def style_configure(self, style, query_opt=None, **kw):
        return _style_configure(self, style, query_opt, **px_options(kw))

    ttk.Style.configure = style_configure
    _applied = True
