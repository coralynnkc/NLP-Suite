"""tk9_fonts_util: on macOS, Tk 9 draws a point-sized font a third larger than Tk 8.6 did.

Tk 8.6 on the Mac drew 12 pt as 12 pixels; Tk 9 draws it as 16 and ignores `tk scaling` for fonts. The GUIs are
laid out in pixels for 8.6 sizes, so on Tk 9 39 of 50 ran off their window (gui_layout_gate.py, 27 Nov). The shim
turns a point size N into the pixel size -N, which both Tk versions draw as 8.6 drew N pt.
"""

import tk9_fonts_util as t


def test_tuples_get_pixel_sizes():
    assert t.px_font(("Courier", 12, "bold")) == ("Courier", -12, "bold")
    assert t.px_font(["Arial", 11]) == ["Arial", -11]


def test_strings_get_pixel_sizes():
    assert t.px_font("Courier 12 bold") == "Courier -12 bold"
    assert t.px_font("{Times New Roman} 14") == "{Times New Roman} -14"


def test_pixel_sizes_named_fonts_and_other_values_are_left_alone():
    for value in (("Courier", -12), "TkDefaultFont", ("Courier",), "Courier", None, 12, ("Courier", 0)):
        assert t.px_font(value) == value


def test_options_rewrite_only_the_font():
    assert t.px_options({"font": ("Arial", 9), "text": "Arial 9"}) == {"font": ("Arial", -9), "text": "Arial 9"}


def test_needed_only_on_a_mac_with_tk_9():
    assert t.needed("darwin", 9.0)
    assert not t.needed("darwin", 8.6)
    assert not t.needed("win32", 9.0)
    assert not t.needed("linux", 9.0)


def test_a_stubbed_tkinter_needs_nothing():
    from unittest.mock import MagicMock

    assert not t.needed("darwin", MagicMock())
