import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib as mpl
from DataLoadingPanel import DataLoadingPanel

try:
    from HspyPrep import HspyPrep
    from SpecVision import CondAns
except ImportError:
    try:
        messagebox.showerror(
            "Import Error",
            "Could not import 'HspyPrep' or 'SpecVision'.\n"
            "Make sure both .py files are in the same directory as this app."
        )
    except Exception:
        print("ImportError: Could not import HspyPrep/SpecVision")
    raise


def _apply_theme(style: ttk.Style) -> None:
    """Configure a clean, modern look on top of the 'clam' base theme."""
    # ── palette ──────────────────────────────────────────────────────────
    BG          = "#F4F6F9"   # window / frame background
    SURFACE     = "#FFFFFF"   # input / card surfaces
    PRIMARY     = "#1A56DB"   # accent blue
    PRIMARY_DK  = "#1E429F"   # darker blue for hover/press
    BORDER      = "#CBD5E1"   # subtle border
    TEXT        = "#1E293B"   # primary text
    TEXT_MUTED  = "#64748B"   # secondary / placeholder text
    SEL_FG      = "#FFFFFF"   # selected foreground

    # ── global defaults ──────────────────────────────────────────────────
    style.configure(
        ".",
        background=BG,
        foreground=TEXT,
        font=("Helvetica Neue", 11),
        borderwidth=0,
        relief="flat",
    )

    # ── frames ───────────────────────────────────────────────────────────
    style.configure("TFrame",      background=BG)
    style.configure("TLabelframe", background=BG,     bordercolor=BORDER,    relief="groove")
    style.configure("TLabelframe.Label",
                    background=BG,
                    foreground=PRIMARY,
                    font=("Helvetica Neue", 11, "bold"))

    # ── labels ───────────────────────────────────────────────────────────
    style.configure("TLabel",          background=BG,  foreground=TEXT)
    style.configure("AppTitle.TLabel", background=BG,  foreground=PRIMARY,
                    font=("Helvetica Neue", 18, "bold"))
    style.configure("AppSub.TLabel",   background=BG,  foreground=TEXT_MUTED,
                    font=("Helvetica Neue", 13))

    # ── buttons ──────────────────────────────────────────────────────────
    style.configure(
        "TButton",
        background=SURFACE,
        foreground=TEXT,
        padding=(10, 5),
        relief="flat",
        borderwidth=1,
        bordercolor=BORDER,
    )
    style.map(
        "TButton",
        background=[("active", "#EFF6FF"), ("pressed", BORDER), ("disabled", BG)],
        foreground=[("disabled", TEXT_MUTED)],
        relief=[("pressed", "flat")],
    )

    style.configure(
        "Accent.TButton",
        background=PRIMARY,
        foreground=SEL_FG,
        padding=(14, 7),
        relief="flat",
        borderwidth=0,
        font=("Helvetica Neue", 11, "bold"),
    )
    style.map(
        "Accent.TButton",
        background=[("active", PRIMARY_DK), ("pressed", PRIMARY_DK), ("disabled", BORDER)],
        foreground=[("disabled", TEXT_MUTED)],
    )

    # ── entry / spinbox ──────────────────────────────────────────────────
    style.configure(
        "TEntry",
        fieldbackground=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        insertcolor=TEXT,
        padding=5,
        relief="flat",
    )
    style.map("TEntry", bordercolor=[("focus", PRIMARY)])

    # ── checkbutton / radiobutton ────────────────────────────────────────
    style.configure("TCheckbutton", background=BG, foreground=TEXT)
    style.configure("TRadiobutton", background=BG, foreground=TEXT)
    style.map("TCheckbutton", background=[("active", BG)])
    style.map("TRadiobutton", background=[("active", BG)])

    # ── scale ────────────────────────────────────────────────────────────
    style.configure("TScale", background=BG, troughcolor=BORDER, sliderlength=16)

    # ── separator ────────────────────────────────────────────────────────
    style.configure("TSeparator", background=BORDER)

    # ── treeview ─────────────────────────────────────────────────────────
    style.configure(
        "Treeview",
        background=SURFACE,
        fieldbackground=SURFACE,
        foreground=TEXT,
        rowheight=28,
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        background=BG,
        foreground=PRIMARY,
        font=("Helvetica Neue", 11, "bold"),
        relief="flat",
        padding=(6, 4),
    )
    style.map(
        "Treeview",
        background=[("selected", PRIMARY)],
        foreground=[("selected", SEL_FG)],
    )

    # ── notebook ─────────────────────────────────────────────────────────
    style.configure("TNotebook",      background=BG, tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab",
                    background=BORDER,
                    foreground=TEXT_MUTED,
                    padding=(14, 6),
                    font=("Helvetica Neue", 11))
    style.map(
        "TNotebook.Tab",
        background=[("selected", SURFACE)],
        foreground=[("selected", PRIMARY)],
        font=[("selected", ("Helvetica Neue", 11, "bold"))],
    )

    # ── scrollbar ────────────────────────────────────────────────────────
    style.configure("Vertical.TScrollbar",
                    background=BG, troughcolor=BG,
                    arrowcolor=TEXT_MUTED, bordercolor=BG,
                    relief="flat")
    style.map("Vertical.TScrollbar",
              background=[("active", BORDER), ("pressed", BORDER)])


def _setup_mpl_style() -> None:
    """Apply a clean, publication-quality matplotlib style to every figure."""
    _COLORS = [
        "#1A56DB",  # primary blue
        "#E3342F",  # red
        "#38A169",  # green
        "#D69E2E",  # amber
        "#805AD5",  # purple
        "#DD6B20",  # orange
        "#0694A2",  # teal
        "#C81E1E",  # dark red
    ]
    mpl.rcParams.update({
        # Figure
        "figure.facecolor":       "white",
        "figure.edgecolor":       "white",
        "figure.dpi":             100,
        # Axes background & spines
        "axes.facecolor":         "#FAFBFC",
        "axes.edgecolor":         "#CBD5E1",
        "axes.linewidth":         0.9,
        "axes.spines.top":        False,
        "axes.spines.right":      False,
        "axes.labelsize":         11,
        "axes.titlesize":         12,
        "axes.titleweight":       "semibold",
        "axes.titlepad":          9,
        "axes.labelpad":          6,
        # Grid
        "axes.grid":              True,
        "grid.color":             "#E2E8F0",
        "grid.linewidth":         0.7,
        "grid.alpha":             1.0,
        "grid.linestyle":         "-",
        # Color cycle
        "axes.prop_cycle":        mpl.cycler("color", _COLORS),
        # Lines & markers
        "lines.linewidth":        1.6,
        "lines.markersize":       5,
        "lines.solid_capstyle":   "round",
        # Ticks
        "xtick.labelsize":        10,
        "ytick.labelsize":        10,
        "xtick.direction":        "in",
        "ytick.direction":        "in",
        "xtick.major.size":       4,
        "ytick.major.size":       4,
        "xtick.minor.visible":    False,
        "ytick.minor.visible":    False,
        # Font
        "font.family":            "sans-serif",
        "font.size":              11,
        # Legend
        "legend.fontsize":        10,
        "legend.framealpha":      0.92,
        "legend.edgecolor":       "#CBD5E1",
        "legend.fancybox":        True,
        "legend.borderpad":       0.6,
        "legend.labelspacing":    0.3,
        # Images
        "image.cmap":             "viridis",
        # Save
        "savefig.dpi":            300,
        "savefig.bbox":           "tight",
        "savefig.facecolor":      "white",
    })


def _center_window(root: tk.Tk, width: int, height: int) -> None:
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x  = (sw - width)  // 2
    y  = (sh - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")


if __name__ == "__main__":
    _setup_mpl_style()

    root = tk.Tk()
    root.configure(bg="#F4F6F9")

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    _apply_theme(style)

    _center_window(root, 880, 800)

    app = DataLoadingPanel(root)
    root.mainloop()
