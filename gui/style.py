"""
GUI Style definitions for MAPD_Logistics.
Provides a consistent dark theme and professional aesthetics.
"""

# Color Palette (Dark Theme)
COLOR_BG = "#1E1E1E"          # Deep Grey / Carbon
COLOR_BG_LIGHT = "#2D2D2D"    # Lighter Grey for panels
COLOR_FG = "#E1E1E1"          # Soft White
COLOR_ACCENT = "#007ACC"      # Professional Blue
COLOR_SUCCESS = "#4CAF50"     # Green
COLOR_WARNING = "#FF9800"     # Orange
COLOR_ERROR = "#F44336"       # Red
COLOR_BORDER = "#404040"      # Border color

# Fonts
FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SMALL = ("Segoe UI", 9)

# Spacing & Dimensions
PADDING_S = 5
PADDING_M = 10
PADDING_L = 20

# Configuration for Tkinter Widgets
STYLE_CONFIG = {
    "bg": COLOR_BG,
    "fg": COLOR_FG,
    "insertbackground": COLOR_FG,  # Cursor color for Entry
    "highlightthickness": 1,
    "highlightbackground": COLOR_BORDER,
    "highlightcolor": COLOR_ACCENT
}

def apply_dark_theme(widget):
    """Recursively apply dark theme to a widget and its children."""
    try:
        widget.configure(bg=COLOR_BG)
        if hasattr(widget, "configure"):
            if "fg" in widget.keys():
                widget.configure(fg=COLOR_FG)
    except:
        pass
    for child in widget.winfo_children():
        apply_dark_theme(child)
