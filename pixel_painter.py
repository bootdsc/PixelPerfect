#!/usr/bin/env python3
"""
PixelPainter — dark-mode pixel art tool for game assets.

Created by Bootdsc for all you Chooms to use, copy, and modify
(CC BY-NC-SA 4.0 — attribution required, non-commercial).

Project format: .ppix (JSON). Export: PNG and C RGB565 headers.
UI chrome: dark gray / light gray / green only.
"""

from __future__ import annotations

import colorsys
import json
import math
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from PIL import Image, ImageTk, ImageGrab
except ImportError:
    print("Pillow required:  pip install Pillow")
    sys.exit(1)

# ---------------------------------------------------------------------------
# App palette ONLY — no red / blue UI chrome
# ---------------------------------------------------------------------------
class Theme:
    BG = "#1a1a1a"          # dark gray
    BG_PANEL = "#242424"    # dark gray panel
    BG_INPUT = "#2e2e2e"
    FG = "#c8c8c8"          # light gray text
    FG_DIM = "#8a8a8a"
    GREEN = "#5cb85c"       # green accents / selection
    GREEN_DK = "#2d5a2d"    # dark green
    BORDER = "#3a3a3a"
    CANVAS_BG = "#0f0f0f"
    GRID_LINE = "#333333"
    CHECKER_A = "#1e1e1e"
    CHECKER_B = "#161616"

APP_NAME = "PixelPainter"
APP_AUTHOR = "Bootdsc"
APP_TAGLINE = "Created by Bootdsc for all you Chooms to use, copy, and modify."
APP_DIR = Path.home() / ".pixel_painter"
RECENT_PATH = APP_DIR / "recent.json"
CONFIG_PATH = APP_DIR / "config.json"
MAX_RECENT = 12

# Classic MS Paint–style defaults (index 0 = transparent / black)
MS_PAINT_PALETTE = [
    "#000000",  # 0 transparent/black
    "#ffffff",
    "#c0c0c0",
    "#808080",
    "#000000",
    "#800000",
    "#ff0000",
    "#ff8080",
    "#ffff00",
    "#808000",
    "#00ff00",
    "#008000",
    "#00ffff",
    "#008080",
    "#0000ff",
    "#000080",
    "#ff00ff",
    "#800080",
    "#ff8000",
    "#a0522d",
    "#ffc0cb",
    "#ffff80",
    "#80ff80",
    "#80ffff",
    "#8080ff",
    "#ff80ff",
    "#400000",
    "#404000",
]

# Named presets (first color stays transparent black)
PALETTE_PRESETS = {
    "MS Paint classic": MS_PAINT_PALETTE,
    "Grayscale": [
        "#000000",
        "#ffffff",
        "#e0e0e0",
        "#c0c0c0",
        "#a0a0a0",
        "#808080",
        "#606060",
        "#404040",
        "#202020",
        "#101010",
        "#000000",
    ],
    "Earth / biomech": [
        "#000000",
        "#ffffff",
        "#1a1a1a",
        "#4a4a4a",
        "#8a8a8a",
        "#c8c8c8",
        "#2d5a2d",
        "#3d7a3d",
        "#5cb85c",
        "#8fd98f",
        "#c4a574",
        "#8b6914",
        "#5c4033",
        "#3d2914",
        "#e8d5a3",
        "#6b8e9f",
    ],
    "Complementary pair (teal/coral)": [
        "#000000",
        "#ffffff",
        "#008080",
        "#00a0a0",
        "#40c0c0",
        "#80e0e0",
        "#004040",
        "#ff7f50",
        "#ff9966",
        "#ffcc99",
        "#cc4400",
        "#662200",
        "#404040",
        "#808080",
        "#c0c0c0",
    ],
    "Complementary pair (purple/lime)": [
        "#000000",
        "#ffffff",
        "#6b2d8b",
        "#8b4dab",
        "#b07cc8",
        "#d4a8e8",
        "#3a1848",
        "#b8e62e",
        "#d4ff4a",
        "#8fb820",
        "#4a6010",
        "#404040",
        "#808080",
        "#c0c0c0",
    ],
    "Warm sunset": [
        "#000000",
        "#ffffff",
        "#1a0a00",
        "#4a2000",
        "#8b4000",
        "#cc6600",
        "#ff8800",
        "#ffaa33",
        "#ffcc66",
        "#ffe0a0",
        "#ff6040",
        "#c02020",
        "#602010",
        "#404040",
        "#808080",
    ],
    "Cool night": [
        "#000000",
        "#ffffff",
        "#0a0a1a",
        "#14142e",
        "#28285a",
        "#4040a0",
        "#6060d0",
        "#8080ff",
        "#a0c0ff",
        "#c0e0ff",
        "#204060",
        "#408080",
        "#60a0a0",
        "#404040",
        "#808080",
    ],
}

DEFAULT_PALETTE = list(MS_PAINT_PALETTE)

DEFAULT_GRID_W = 32
DEFAULT_GRID_H = 32
MIN_CELL_PX = 8
MAX_CELL_PX = 48
DEFAULT_CELL_PX = 16


def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5)


def resize_palette(palette: List[str], n: int) -> List[str]:
    """Grow/shrink palette. New slots default to white. Index 0 stays black/transparent."""
    n = max(2, min(64, n))
    out = list(palette[:n])
    while len(out) < n:
        out.append("#ffffff")
    if out:
        # Keep slot 0 as transparent convention if empty was black
        if len(palette) == 0:
            out[0] = "#000000"
    return out


def ensure_app_dir() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def load_recent() -> List[str]:
    ensure_app_dir()
    if not RECENT_PATH.exists():
        return []
    try:
        data = json.loads(RECENT_PATH.read_text(encoding="utf-8"))
        return [p for p in data if isinstance(p, str) and Path(p).exists()]
    except Exception:
        return []


def save_recent(paths: List[str]) -> None:
    ensure_app_dir()
    # de-dupe keep order
    seen = set()
    out = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    RECENT_PATH.write_text(json.dumps(out[:MAX_RECENT], indent=2), encoding="utf-8")


def add_recent(path: str) -> None:
    paths = load_recent()
    path = str(Path(path).resolve())
    if path in paths:
        paths.remove(path)
    paths.insert(0, path)
    save_recent(paths)


def load_app_config() -> dict:
    ensure_app_dir()
    defaults = {
        "canvas_bg": "#3a3a3a",
        "use_checker": False,
        "show_grid": True,
        "cell_px": DEFAULT_CELL_PX,
    }
    if not CONFIG_PATH.exists():
        return defaults
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return defaults
        defaults.update({k: data[k] for k in defaults if k in data})
        return defaults
    except Exception:
        return defaults


def save_app_config(cfg: dict) -> None:
    ensure_app_dir()
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def grab_screen_pixel(x: int, y: int) -> Tuple[int, int, int]:
    """Sample one pixel from the desktop (Windows multi-monitor friendly when possible)."""
    try:
        # Pillow 9.2+: all_screens covers multi-monitor virtual desktop
        img = ImageGrab.grab(all_screens=True)
    except TypeError:
        img = ImageGrab.grab()
    # Clamp to image bounds
    x = max(0, min(img.width - 1, int(x)))
    y = max(0, min(img.height - 1, int(y)))
    pix = img.getpixel((x, y))
    if isinstance(pix, int):  # palette mode unlikely
        return pix, pix, pix
    return int(pix[0]), int(pix[1]), int(pix[2])


def make_hsv_wheel(size: int = 200, value: float = 1.0) -> Image.Image:
    """Circular HSV color wheel (S radial, H angular) at fixed V."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    cx = cy = size // 2
    radius = size // 2 - 2
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > radius:
                continue
            # angle 0 = red, clockwise-ish
            ang = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)  # 0..1
            sat = min(1.0, dist / radius)
            r, g, b = hsv_to_rgb(ang, sat, value)
            px[x, y] = (r, g, b, 255)
    return img


class PixelDocument:
    """In-memory image: grid of palette indices + palette hex colors."""

    def __init__(
        self,
        width: int = DEFAULT_GRID_W,
        height: int = DEFAULT_GRID_H,
        palette: Optional[List[str]] = None,
    ):
        self.width = max(1, min(256, width))
        self.height = max(1, min(256, height))
        self.palette = list(palette or DEFAULT_PALETTE)
        # 0 = transparent (index 0 treated as clear for export if flag set)
        self.pixels: List[List[int]] = [
            [0 for _ in range(self.width)] for _ in range(self.height)
        ]
        self.path: Optional[str] = None
        self.dirty = False

    def resize(self, w: int, h: int, keep: bool = True) -> None:
        w = max(1, min(256, w))
        h = max(1, min(256, h))
        new_px = [[0 for _ in range(w)] for _ in range(h)]
        if keep:
            for y in range(min(h, self.height)):
                for x in range(min(w, self.width)):
                    new_px[y][x] = self.pixels[y][x]
        self.width, self.height = w, h
        self.pixels = new_px
        self.dirty = True

    def set_pixel(self, x: int, y: int, idx: int) -> bool:
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.pixels[y][x] != idx:
                self.pixels[y][x] = idx
                self.dirty = True
                return True
        return False

    def get_pixel(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[y][x]
        return 0

    def flood_fill(self, x: int, y: int, new_idx: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        old = self.pixels[y][x]
        if old == new_idx:
            return False
        stack = [(x, y)]
        changed = False
        while stack:
            cx, cy = stack.pop()
            if not (0 <= cx < self.width and 0 <= cy < self.height):
                continue
            if self.pixels[cy][cx] != old:
                continue
            self.pixels[cy][cx] = new_idx
            changed = True
            stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
        if changed:
            self.dirty = True
        return changed

    def to_dict(self) -> dict:
        return {
            "format": "ppix",
            "version": 1,
            "width": self.width,
            "height": self.height,
            "palette": self.palette,
            "pixels": self.pixels,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PixelDocument":
        doc = cls(data["width"], data["height"], data.get("palette"))
        doc.pixels = data["pixels"]
        # validate
        if len(doc.pixels) != doc.height or any(len(r) != doc.width for r in doc.pixels):
            raise ValueError("Corrupt pixel grid")
        return doc

    def save_ppix(self, path: str) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        self.path = path
        self.dirty = False
        add_recent(path)

    @classmethod
    def load_ppix(cls, path: str) -> "PixelDocument":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format") != "ppix":
            raise ValueError("Not a .ppix project file")
        doc = cls.from_dict(data)
        doc.path = path
        doc.dirty = False
        add_recent(path)
        return doc

    def export_png(self, path: str, scale: int = 1, transparent_zero: bool = True) -> None:
        """Lossless PNG — pixel-perfect when scale is integer."""
        scale = max(1, min(64, scale))
        img = Image.new("RGBA", (self.width * scale, self.height * scale), (0, 0, 0, 0))
        px = img.load()
        for y in range(self.height):
            for x in range(self.width):
                idx = self.pixels[y][x]
                if transparent_zero and idx == 0:
                    continue
                idx = max(0, min(idx, len(self.palette) - 1))
                r, g, b = hex_to_rgb(self.palette[idx])
                for dy in range(scale):
                    for dx in range(scale):
                        px[x * scale + dx, y * scale + dy] = (r, g, b, 255)
        img.save(path, "PNG")
        add_recent(path)

    def export_c_rgb565(self, path: str, array_name: str = "sprite") -> None:
        """C header for embedded (ESP32 / M5GFX) — RGB565, 0x0000 = transparent if index 0."""
        lines = [
            f"// Auto-generated by {APP_NAME} ({APP_AUTHOR})",
            f"// {self.width}x{self.height} RGB565",
            f"#pragma once",
            f"#include <stdint.h>",
            f"static const int {array_name}_w = {self.width};",
            f"static const int {array_name}_h = {self.height};",
            f"static const uint16_t {array_name}_data[{self.width * self.height}] = {{",
        ]
        vals = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                idx = self.pixels[y][x]
                if idx == 0:
                    row.append("0x0000")
                else:
                    idx = max(0, min(idx, len(self.palette) - 1))
                    r, g, b = hex_to_rgb(self.palette[idx])
                    # RGB565
                    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                    row.append(f"0x{c:04X}")
            vals.append("  " + ", ".join(row) + ",")
        lines.extend(vals)
        lines.append("};")
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


class PixelPainterApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.minsize(800, 600)
        self.root.geometry("1024x720")
        self.root.configure(bg=Theme.BG)

        self.doc = PixelDocument(DEFAULT_GRID_W, DEFAULT_GRID_H, list(DEFAULT_PALETTE))
        self.color_idx = 1
        self.brush = 1  # 1,2,3,4
        self.tool = tk.StringVar(value="paint")  # paint | erase | fill | eye | sel_box | sel_free
        cfg = load_app_config()
        self.show_grid = tk.BooleanVar(value=bool(cfg.get("show_grid", True)))
        self.use_checker = tk.BooleanVar(value=bool(cfg.get("use_checker", False)))
        self.canvas_bg = str(cfg.get("canvas_bg", "#3a3a3a"))
        # Palette slot count = full palette length (not "visible only")
        self.palette_count = tk.IntVar(value=len(self.doc.palette))
        self.preset_name = tk.StringVar(value="MS Paint classic")
        self.cell_px = int(cfg.get("cell_px", DEFAULT_CELL_PX))
        self.cell_px = max(MIN_CELL_PX, min(MAX_CELL_PX, self.cell_px))
        self._paint_down = False
        self._space_held = False
        self._alt_held = False
        self._panning = False
        self._last_cell: Optional[Tuple[int, int]] = None
        self._photo: Optional[ImageTk.PhotoImage] = None
        self._wheel_photo: Optional[ImageTk.PhotoImage] = None
        self._rebuild_ui_lock = False
        self._screen_pick_overlay: Optional[tk.Toplevel] = None
        self._screen_pick_target = "palette"

        # Selection / floating move
        # sel_cells: set of (x,y) on the grid that are selected
        # float_items: list of (lx, ly, color_idx) local coords when moving (origin = float_ox/oy)
        # moving: True after "Move selection" lifts pixels
        self.sel_cells: set = set()
        self._sel_box_start: Optional[Tuple[int, int]] = None
        self._sel_box_end: Optional[Tuple[int, int]] = None
        self.moving = False
        self.float_items: List[Tuple[int, int, int]] = []  # lx, ly, idx
        self.float_ox = 0  # world grid origin of float (can be off-canvas)
        self.float_oy = 0
        self._move_drag_last: Optional[Tuple[int, int]] = None

        self._build_menu()
        self._build_ui()
        self._bind_keys()
        self.root.bind("<Configure>", self._on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._refresh_title()
        self.root.after(50, self._redraw)

    def _persist_view_config(self) -> None:
        save_app_config(
            {
                "canvas_bg": self.canvas_bg,
                "use_checker": bool(self.use_checker.get()),
                "show_grid": bool(self.show_grid.get()),
                "cell_px": int(self.cell_px),
            }
        )

    # ----- UI chrome -----
    def _style_btn(self, btn: tk.Button, active: bool = False) -> None:
        btn.configure(
            bg=Theme.GREEN_DK if active else Theme.BG_PANEL,
            fg=Theme.FG,
            activebackground=Theme.GREEN,
            activeforeground=Theme.BG,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=Theme.GREEN if active else Theme.BORDER,
            highlightcolor=Theme.GREEN,
            padx=8,
            pady=4,
            cursor="hand2",
        )

    def _label(self, parent, text: str, **kw) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=kw.pop("bg", Theme.BG_PANEL),
            fg=kw.pop("fg", Theme.FG),
            font=kw.pop("font", ("Segoe UI", 9)),
            **kw,
        )

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root, bg=Theme.BG_PANEL, fg=Theme.FG, tearoff=0,
                          activebackground=Theme.GREEN_DK, activeforeground=Theme.FG)
        file_m = tk.Menu(menubar, tearoff=0, bg=Theme.BG_PANEL, fg=Theme.FG,
                         activebackground=Theme.GREEN_DK, activeforeground=Theme.FG)
        file_m.add_command(label="New…", command=self.cmd_new, accelerator="Ctrl+N")
        file_m.add_command(label="Open…", command=self.cmd_open, accelerator="Ctrl+O")
        file_m.add_command(label="Save", command=self.cmd_save, accelerator="Ctrl+S")
        file_m.add_command(label="Save As…", command=self.cmd_save_as, accelerator="Ctrl+Shift+S")
        file_m.add_separator()
        file_m.add_command(label="Export PNG…", command=self.cmd_export_png)
        file_m.add_command(label="Export C RGB565…", command=self.cmd_export_c)
        file_m.add_separator()
        self.recent_menu = tk.Menu(file_m, tearoff=0, bg=Theme.BG_PANEL, fg=Theme.FG,
                                   activebackground=Theme.GREEN_DK, activeforeground=Theme.FG)
        file_m.add_cascade(label="Recent Files", menu=self.recent_menu)
        file_m.add_separator()
        file_m.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_m)

        edit_m = tk.Menu(menubar, tearoff=0, bg=Theme.BG_PANEL, fg=Theme.FG,
                         activebackground=Theme.GREEN_DK, activeforeground=Theme.FG)
        edit_m.add_command(label="Resize grid…", command=self.cmd_resize)
        edit_m.add_command(label="Clear canvas", command=self.cmd_clear)
        edit_m.add_separator()
        edit_m.add_command(label="Edit color (wheel)…", command=self.cmd_edit_color, accelerator="C")
        edit_m.add_command(label="Set palette size…", command=self.cmd_set_palette_size)
        edit_m.add_command(label="Screen pick → palette", command=self.cmd_screen_pick, accelerator="P")
        edit_m.add_separator()
        edit_m.add_command(label="Clear selection", command=self.cmd_clear_selection)
        menubar.add_cascade(label="Edit", menu=edit_m)

        view_m = tk.Menu(menubar, tearoff=0, bg=Theme.BG_PANEL, fg=Theme.FG,
                         activebackground=Theme.GREEN_DK, activeforeground=Theme.FG)
        view_m.add_command(label="Canvas background color…", command=self.cmd_set_bg)
        view_m.add_command(label="Screen pick → background", command=lambda: self.cmd_screen_pick_bg())
        view_m.add_separator()
        view_m.add_checkbutton(label="Show grid", variable=self.show_grid, command=self._on_view_toggle)
        view_m.add_checkbutton(label="Checker empty cells", variable=self.use_checker, command=self._on_view_toggle)
        view_m.add_separator()
        view_m.add_command(label="Zoom in", command=lambda: self._zoom_by(2), accelerator="Ctrl+=")
        view_m.add_command(label="Zoom out", command=lambda: self._zoom_by(-2), accelerator="Ctrl+-")
        view_m.add_command(label="Reset zoom (16px/cell)", command=self._zoom_reset)
        menubar.add_cascade(label="View", menu=view_m)

        pal_m = tk.Menu(menubar, tearoff=0, bg=Theme.BG_PANEL, fg=Theme.FG,
                        activebackground=Theme.GREEN_DK, activeforeground=Theme.FG)
        for name in PALETTE_PRESETS:
            pal_m.add_command(label=name, command=lambda n=name: self.cmd_apply_preset(n))
        menubar.add_cascade(label="Palette", menu=pal_m)

        help_m = tk.Menu(menubar, tearoff=0, bg=Theme.BG_PANEL, fg=Theme.FG,
                         activebackground=Theme.GREEN_DK, activeforeground=Theme.FG)
        help_m.add_command(label="About / formats", command=self.cmd_about)
        menubar.add_cascade(label="Help", menu=help_m)

        self.root.config(menu=menubar)
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self) -> None:
        self.recent_menu.delete(0, tk.END)
        recent = load_recent()
        if not recent:
            self.recent_menu.add_command(label="(empty)", state=tk.DISABLED)
            return
        for p in recent:
            self.recent_menu.add_command(
                label=p, command=lambda path=p: self._open_path(path)
            )

    def _build_ui(self) -> None:
        # Top toolbar
        top = tk.Frame(self.root, bg=Theme.BG_PANEL, height=44)
        top.pack(side=tk.TOP, fill=tk.X)
        top.pack_propagate(False)

        self._label(top, "Tool:").pack(side=tk.LEFT, padx=(10, 4), pady=8)
        self.tool_btns = {}
        for name, label in [
            ("paint", "Paint"),
            ("erase", "Erase"),
            ("fill", "Fill"),
            ("eye", "Eyedrop"),
            ("sel_box", "Box"),
            ("sel_free", "Free"),
        ]:
            b = tk.Button(top, text=label, command=lambda n=name: self._set_tool(n))
            self._style_btn(b, active=(name == "paint"))
            b.pack(side=tk.LEFT, padx=2, pady=6)
            self.tool_btns[name] = b

        tk.Frame(top, bg=Theme.BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=8)

        self._label(top, "Brush:").pack(side=tk.LEFT, padx=(0, 4))
        self.brush_btns = {}
        for s in (1, 2, 3, 4):
            b = tk.Button(top, text=f"{s}×{s}", command=lambda n=s: self._set_brush(n))
            self._style_btn(b, active=(s == 1))
            b.pack(side=tk.LEFT, padx=2, pady=6)
            self.brush_btns[s] = b

        tk.Frame(top, bg=Theme.BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=8)

        gchk = tk.Checkbutton(
            top,
            text="Grid",
            variable=self.show_grid,
            command=self._on_view_toggle,
            bg=Theme.BG_PANEL,
            fg=Theme.FG,
            selectcolor=Theme.BG_INPUT,
            activebackground=Theme.BG_PANEL,
            activeforeground=Theme.GREEN,
            highlightthickness=0,
        )
        gchk.pack(side=tk.LEFT, padx=4)

        cchk = tk.Checkbutton(
            top,
            text="Checker",
            variable=self.use_checker,
            command=self._on_view_toggle,
            bg=Theme.BG_PANEL,
            fg=Theme.FG,
            selectcolor=Theme.BG_INPUT,
            activebackground=Theme.BG_PANEL,
            activeforeground=Theme.GREEN,
            highlightthickness=0,
        )
        cchk.pack(side=tk.LEFT, padx=4)

        b_pick = tk.Button(top, text="Pick→slot", command=self.cmd_screen_pick)
        self._style_btn(b_pick)
        b_pick.pack(side=tk.LEFT, padx=2, pady=6)

        self.status = self._label(top, "16×16", bg=Theme.BG_PANEL, fg=Theme.FG_DIM)
        self.status.pack(side=tk.RIGHT, padx=12)

        # Body: left palette | center canvas | right props
        body = tk.Frame(self.root, bg=Theme.BG)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left palette panel (wider for presets + swatches)
        left = tk.Frame(body, bg=Theme.BG_PANEL, width=168)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        self._label(left, "PALETTE", font=("Segoe UI", 9, "bold")).pack(pady=(10, 2))

        self._label(left, "Preset", bg=Theme.BG_PANEL, fg=Theme.FG_DIM).pack(anchor=tk.W, padx=8)
        preset_box = ttk.Combobox(
            left,
            textvariable=self.preset_name,
            values=list(PALETTE_PRESETS.keys()),
            state="readonly",
            width=18,
        )
        preset_box.pack(fill=tk.X, padx=8, pady=2)
        preset_box.bind("<<ComboboxSelected>>", lambda e: self.cmd_apply_preset(self.preset_name.get()))

        size_row = tk.Frame(left, bg=Theme.BG_PANEL)
        size_row.pack(fill=tk.X, padx=8, pady=(8, 2))
        self._label(size_row, "Slots:", bg=Theme.BG_PANEL).pack(side=tk.LEFT)
        self.size_spin = tk.Spinbox(
            size_row,
            from_=2,
            to=64,
            width=4,
            textvariable=self.palette_count,
            command=self._on_palette_count_spin,
            bg=Theme.BG_INPUT,
            fg=Theme.FG,
            buttonbackground=Theme.BG_PANEL,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            insertbackground=Theme.FG,
        )
        self.size_spin.pack(side=tk.LEFT, padx=4)
        self.size_spin.bind("<Return>", lambda e: self._on_palette_count_spin())
        self.size_spin.bind("<FocusOut>", lambda e: self._on_palette_count_spin())
        self._label(size_row, "(+white)", bg=Theme.BG_PANEL, fg=Theme.FG_DIM).pack(side=tk.LEFT)

        # Scrollable swatch area
        sw_wrap = tk.Frame(left, bg=Theme.BG_PANEL)
        sw_wrap.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.palette_canvas = tk.Canvas(sw_wrap, bg=Theme.BG_PANEL, highlightthickness=0)
        sb = tk.Scrollbar(sw_wrap, orient=tk.VERTICAL, command=self.palette_canvas.yview)
        self.palette_frame = tk.Frame(self.palette_canvas, bg=Theme.BG_PANEL)
        self.palette_frame.bind(
            "<Configure>",
            lambda e: self.palette_canvas.configure(scrollregion=self.palette_canvas.bbox("all")),
        )
        self.palette_canvas.create_window((0, 0), window=self.palette_frame, anchor=tk.NW)
        self.palette_canvas.configure(yscrollcommand=sb.set)
        self.palette_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_row = tk.Frame(left, bg=Theme.BG_PANEL)
        btn_row.pack(fill=tk.X, padx=8, pady=(0, 4))
        for text, cmd in [
            ("Wheel", self.cmd_edit_color),
            ("Pick", self.cmd_screen_pick),
        ]:
            b = tk.Button(btn_row, text=text, command=cmd)
            self._style_btn(b)
            b.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Selection move / place (left side as requested)
        self._label(left, "SELECTION", font=("Segoe UI", 9, "bold"), bg=Theme.BG_PANEL).pack(
            pady=(6, 2)
        )
        self.move_btn = tk.Button(left, text="Move selection", command=self.cmd_toggle_move)
        self._style_btn(self.move_btn)
        self.move_btn.pack(fill=tk.X, padx=8, pady=2)
        b_clr = tk.Button(left, text="Clear select", command=self.cmd_clear_selection)
        self._style_btn(b_clr)
        b_clr.pack(fill=tk.X, padx=8, pady=2)

        self._label(
            left,
            "Box/Free to select\n"
            "Move = lift & drag\n"
            "(off-grid OK)\n"
            "Place = drop (clips)\n"
            "Space+drag = erase\n"
            "  on Paint tool",
            bg=Theme.BG_PANEL,
            fg=Theme.FG_DIM,
            justify=tk.LEFT,
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W, padx=8, pady=(4, 8))

        # Center canvas + scrollbars (large grids)
        center = tk.Frame(body, bg=Theme.CANVAS_BG)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        center.rowconfigure(0, weight=1)
        center.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            center,
            bg=Theme.CANVAS_BG,
            highlightthickness=0,
            bd=0,
            cursor="crosshair",
            xscrollincrement=1,
            yscrollincrement=1,
        )
        self.h_scroll = tk.Scrollbar(
            center, orient=tk.HORIZONTAL, command=self.canvas.xview,
            bg=Theme.BG_PANEL, troughcolor=Theme.BG, activebackground=Theme.GREEN_DK,
        )
        self.v_scroll = tk.Scrollbar(
            center, orient=tk.VERTICAL, command=self.canvas.yview,
            bg=Theme.BG_PANEL, troughcolor=Theme.BG, activebackground=Theme.GREEN_DK,
        )
        self.canvas.configure(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-3>", self._on_rpress)
        self.canvas.bind("<B3-Motion>", self._on_rdrag)
        self.canvas.bind("<Motion>", self._on_motion)
        # Alt + drag = pan (trackpad-friendly)
        self.canvas.bind("<Alt-ButtonPress-1>", self._pan_start)
        self.canvas.bind("<Alt-B1-Motion>", self._pan_move)
        self.canvas.bind("<Alt-ButtonRelease-1>", self._pan_end)
        self.canvas.bind("<ButtonPress-2>", self._pan_start)  # middle mouse also pans
        self.canvas.bind("<B2-Motion>", self._pan_move)
        self.canvas.bind("<ButtonRelease-2>", self._pan_end)
        # Trackpad-friendly: Space held while dragging inverts paint/erase
        self.canvas.bind("<KeyPress-space>", self._on_space_down)
        self.canvas.bind("<KeyRelease-space>", self._on_space_up)
        self.root.bind_all("<KeyPress-space>", self._on_space_down)
        self.root.bind_all("<KeyRelease-space>", self._on_space_up)
        self.root.bind_all("<KeyPress-Alt_L>", self._on_alt_down)
        self.root.bind_all("<KeyRelease-Alt_L>", self._on_alt_up)
        self.root.bind_all("<KeyPress-Alt_R>", self._on_alt_down)
        self.root.bind_all("<KeyRelease-Alt_R>", self._on_alt_up)
        self.canvas.bind("<Control-MouseWheel>", self._on_zoom_wheel)
        self.canvas.bind("<Control-Button-4>", lambda e: self._zoom_by(2))
        self.canvas.bind("<Control-Button-5>", lambda e: self._zoom_by(-2))

        # Right info
        right = tk.Frame(body, bg=Theme.BG_PANEL, width=160)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)
        self._label(right, "DOCUMENT", font=("Segoe UI", 9, "bold")).pack(pady=(10, 6))
        self.info = self._label(right, "", justify=tk.LEFT, fg=Theme.FG_DIM)
        self.info.pack(anchor=tk.W, padx=10)

        for text, cmd in [
            ("New grid…", self.cmd_new),
            ("Resize…", self.cmd_resize),
            ("Save As…", self.cmd_save_as),
            ("Export PNG…", self.cmd_export_png),
            ("Export C…", self.cmd_export_c),
        ]:
            b = tk.Button(right, text=text, command=cmd)
            self._style_btn(b)
            b.pack(fill=tk.X, padx=10, pady=3)

        self.preview_label = self._label(right, "1:1 preview", fg=Theme.FG_DIM)
        self.preview_label.pack(pady=(16, 4))
        self.preview_canvas = tk.Canvas(
            right, width=128, height=128, bg=Theme.CANVAS_BG, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        self.preview_canvas.pack(padx=10)

        self._rebuild_palette_swatches()
        self._update_info()

    def _bind_keys(self) -> None:
        r = self.root
        r.bind("<Control-n>", lambda e: self.cmd_new())
        r.bind("<Control-o>", lambda e: self.cmd_open())
        r.bind("<Control-s>", lambda e: self.cmd_save())
        r.bind("<Control-S>", lambda e: self.cmd_save_as())
        r.bind("1", lambda e: self._set_brush(1))
        r.bind("2", lambda e: self._set_brush(2))
        r.bind("3", lambda e: self._set_brush(3))
        r.bind("4", lambda e: self._set_brush(4))
        r.bind("b", lambda e: self._set_tool("paint"))
        r.bind("e", lambda e: self._set_tool("erase"))
        r.bind("f", lambda e: self._set_tool("fill"))
        r.bind("i", lambda e: self._set_tool("eye"))
        r.bind("r", lambda e: self._set_tool("sel_box"))
        r.bind("l", lambda e: self._set_tool("sel_free"))
        r.bind("m", lambda e: self.cmd_toggle_move())
        r.bind("g", lambda e: (self.show_grid.set(not self.show_grid.get()), self._on_view_toggle()))
        r.bind("p", lambda e: self.cmd_screen_pick())
        r.bind("P", lambda e: self.cmd_screen_pick())
        r.bind("c", lambda e: self.cmd_edit_color())
        r.bind("C", lambda e: self.cmd_edit_color())
        r.bind("<Escape>", lambda e: self.cmd_clear_selection())
        r.bind("<Control-equal>", lambda e: self._zoom_by(2))
        r.bind("<Control-plus>", lambda e: self._zoom_by(2))
        r.bind("<Control-minus>", lambda e: self._zoom_by(-2))
        r.bind("<Control-0>", lambda e: self._zoom_reset())

    def _on_space_down(self, event=None) -> str:
        # Don't type spaces into spinboxes
        w = self.root.focus_get()
        if w is not None and w.winfo_class() in ("Entry", "TEntry", "Spinbox", "TCombobox"):
            return ""
        self._space_held = True
        self._update_info()
        return "break"

    def _on_space_up(self, event=None) -> str:
        self._space_held = False
        self._update_info()
        return "break"

    def _on_alt_down(self, event=None) -> None:
        self._alt_held = True
        try:
            self.canvas.configure(cursor="fleur")
        except Exception:
            pass

    def _on_alt_up(self, event=None) -> None:
        self._alt_held = False
        self._panning = False
        try:
            self.canvas.configure(cursor="crosshair")
        except Exception:
            pass

    def _pan_start(self, event) -> str:
        self._panning = True
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.configure(cursor="fleur")
        return "break"

    def _pan_move(self, event) -> str:
        if self._panning or self._alt_held:
            self.canvas.scan_dragto(event.x, event.y, gain=1)
        return "break"

    def _pan_end(self, event=None) -> str:
        self._panning = False
        if not self._alt_held:
            self.canvas.configure(cursor="crosshair")
        return "break"

    def _zoom_by(self, delta: int) -> None:
        self.cell_px = max(MIN_CELL_PX, min(MAX_CELL_PX, self.cell_px + delta))
        self._persist_view_config()
        self._redraw()

    def _zoom_reset(self) -> None:
        self.cell_px = DEFAULT_CELL_PX
        self._persist_view_config()
        self._redraw()

    def _on_zoom_wheel(self, event) -> str:
        if event.delta > 0 or getattr(event, "num", 0) == 4:
            self._zoom_by(2)
        else:
            self._zoom_by(-2)
        return "break"

    def _effective_tool(self) -> str:
        """Space inverts paint↔erase (trackpad substitute for right-drag erase)."""
        t = self.tool.get()
        if not self._space_held:
            return t
        if t == "paint":
            return "erase"
        if t == "erase":
            return "paint"
        if t == "fill":
            return "erase"  # space+fill = brush erase
        return t

    def _on_view_toggle(self) -> None:
        self._persist_view_config()
        self._redraw()

    def _set_canvas_bg(self, hex_color: str) -> None:
        try:
            hex_to_rgb(hex_color)
        except Exception:
            return
        if not hex_color.startswith("#"):
            hex_color = "#" + hex_color
        self.canvas_bg = hex_color.lower()
        self.use_checker.set(False)
        self._persist_view_config()
        self._redraw()

    def _apply_picked_color(self, hex_color: str, target: str) -> None:
        """target: palette | background | both"""
        hex_color = hex_color.lower()
        if target in ("background", "both"):
            self._set_canvas_bg(hex_color)
        if target in ("palette", "both"):
            # Prefer replacing current swatch (if not index 0), else add
            if self.color_idx == 0 and len(self.doc.palette) > 1:
                self.color_idx = 1
            if 0 <= self.color_idx < len(self.doc.palette):
                self.doc.palette[self.color_idx] = hex_color
            else:
                self.doc.palette.append(hex_color)
                self.color_idx = len(self.doc.palette) - 1
            self.doc.dirty = True
            self.palette_count.set(len(self.doc.palette))
            self._rebuild_palette_swatches()
            self._redraw()
            self._refresh_title()

    def _set_tool(self, name: str) -> None:
        # Leaving move mode without placing? keep float until place/clear
        self.tool.set(name)
        for n, b in self.tool_btns.items():
            self._style_btn(b, active=(n == name))
        self._update_info()

    def _set_brush(self, n: int) -> None:
        self.brush = n
        for s, b in self.brush_btns.items():
            self._style_btn(b, active=(s == n))
        self._update_info()

    def _on_palette_count_spin(self) -> None:
        try:
            n = int(self.palette_count.get())
        except Exception:
            return
        n = max(2, min(64, n))
        self.palette_count.set(n)
        old_len = len(self.doc.palette)
        self.doc.palette = resize_palette(self.doc.palette, n)
        if n != old_len:
            self.doc.dirty = True
        if self.color_idx >= n:
            self.color_idx = n - 1
        self._rebuild_palette_swatches()
        self._refresh_title()
        self._update_info()

    def _rebuild_palette_swatches(self) -> None:
        for w in self.palette_frame.winfo_children():
            w.destroy()
        n = len(self.doc.palette)
        self.palette_count.set(n)
        # Grid of swatches (4 columns)
        cols = 4
        for i in range(n):
            color = self.doc.palette[i]
            r, c = divmod(i, cols)
            cell = tk.Frame(self.palette_frame, bg=Theme.BG_PANEL)
            cell.grid(row=r, column=c, padx=2, pady=2)
            sw = tk.Canvas(
                cell,
                width=28,
                height=22,
                bg=color,
                highlightthickness=2,
                highlightbackground=Theme.GREEN if i == self.color_idx else Theme.BORDER,
                cursor="hand2",
            )
            sw.pack()
            sw.bind("<Button-1>", lambda e, idx=i: self._pick_color(idx))
            sw.bind("<Double-Button-1>", lambda e, idx=i: self._edit_color_idx(idx))
            lab = self._label(
                cell,
                "T" if i == 0 else str(i),
                fg=Theme.GREEN if i == self.color_idx else Theme.FG_DIM,
                font=("Segoe UI", 7),
            )
            lab.pack()
        self.palette_frame.update_idletasks()
        if hasattr(self, "palette_canvas"):
            self.palette_canvas.configure(scrollregion=self.palette_canvas.bbox("all"))

    def _pick_color(self, idx: int) -> None:
        self.color_idx = idx
        self._rebuild_palette_swatches()
        self._update_info()

    def _edit_color_idx(self, idx: int) -> None:
        self.color_idx = idx
        self.cmd_edit_color()

    def cmd_apply_preset(self, name: str) -> None:
        if name not in PALETTE_PRESETS:
            return
        if self.doc.dirty or any(any(px != 0 for px in row) for row in self.doc.pixels):
            if not messagebox.askyesno(
                APP_NAME,
                f"Replace palette with “{name}”?\n"
                "(Pixel indices stay the same — colors will remap.)",
                parent=self.root,
            ):
                return
        self.preset_name.set(name)
        base = list(PALETTE_PRESETS[name])
        # Keep current slot count if larger
        n = max(len(base), int(self.palette_count.get()) if self.palette_count.get() else len(base))
        n = max(2, min(64, n))
        self.doc.palette = resize_palette(base, n)
        self.doc.dirty = True
        self.color_idx = min(self.color_idx, n - 1)
        if self.color_idx == 0 and n > 1:
            self.color_idx = 1
        self._rebuild_palette_swatches()
        self._redraw()
        self._refresh_title()

    def cmd_set_palette_size(self) -> None:
        n = simpledialog.askinteger(
            "Palette size",
            "Number of color slots (2–64).\n"
            "Existing colors kept; new slots = white.",
            initialvalue=len(self.doc.palette),
            minvalue=2,
            maxvalue=64,
            parent=self.root,
        )
        if n:
            self.palette_count.set(n)
            self._on_palette_count_spin()

    # ----- canvas mapping (scrollable world coords) -----
    def _layout_metrics(self) -> Tuple[int, int, int, float]:
        """Returns ox, oy, cell_px in canvas scrollregion space."""
        pad = 8
        cell = max(MIN_CELL_PX, min(MAX_CELL_PX, int(self.cell_px)))
        return pad, pad, cell, 1.0

    def _canvas_xy(self, event) -> Tuple[float, float]:
        """Event → canvas world coords (respects scroll)."""
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def _event_to_cell(self, event) -> Optional[Tuple[int, int]]:
        ox, oy, cell, _ = self._layout_metrics()
        if cell < 1:
            return None
        cx, cy = self._canvas_xy(event)
        x = int((cx - ox) // cell)
        y = int((cy - oy) // cell)
        if 0 <= x < self.doc.width and 0 <= y < self.doc.height:
            return x, y
        return None

    def _event_to_cell_unclamped(self, event) -> Optional[Tuple[int, int]]:
        """Grid coords even outside the image (for moving selection off-screen)."""
        ox, oy, cell, _ = self._layout_metrics()
        if cell < 1:
            return None
        cx, cy = self._canvas_xy(event)
        x = int((cx - ox) // cell)
        y = int((cy - oy) // cell)
        return x, y

    def _line_select(self, x0: int, y0: int, x1: int, y1: int) -> None:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if 0 <= x0 < self.doc.width and 0 <= y0 < self.doc.height:
                self.sel_cells.add((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def _update_move_btn(self) -> None:
        if not hasattr(self, "move_btn"):
            return
        if self.moving:
            self.move_btn.configure(text="Place selection")
            self._style_btn(self.move_btn, active=True)
        else:
            n = len(self.sel_cells)
            self.move_btn.configure(text=f"Move selection ({n})" if n else "Move selection")
            self._style_btn(self.move_btn, active=False)

    def cmd_clear_selection(self) -> None:
        if self.moving and self.float_items:
            # Drop into void = discard float
            if not messagebox.askyesno(
                APP_NAME,
                "Discard floating pixels?",
                parent=self.root,
            ):
                return
        self.sel_cells = set()
        self.float_items = []
        self.moving = False
        self._sel_box_start = None
        self._sel_box_end = None
        self._update_move_btn()
        self._redraw()

    def cmd_toggle_move(self) -> None:
        if self.moving:
            self._place_float()
        else:
            self._lift_selection()

    def _lift_selection(self) -> None:
        if not self.sel_cells:
            messagebox.showinfo(APP_NAME, "Select pixels first (Box or Free).", parent=self.root)
            return
        # Only lift non-empty pixels; keep transparent holes
        xs = [p[0] for p in self.sel_cells]
        ys = [p[1] for p in self.sel_cells]
        min_x, min_y = min(xs), min(ys)
        items: List[Tuple[int, int, int]] = []
        for x, y in self.sel_cells:
            idx = self.doc.get_pixel(x, y)
            if idx == 0:
                continue
            items.append((x - min_x, y - min_y, idx))
            self.doc.set_pixel(x, y, 0)
        if not items:
            messagebox.showinfo(APP_NAME, "Selection is empty (only transparent).", parent=self.root)
            self.sel_cells = set()
            self._update_move_btn()
            self._redraw()
            return
        self.float_items = items
        self.float_ox = min_x
        self.float_oy = min_y
        self.sel_cells = set()
        self.moving = True
        self.doc.dirty = True
        self._update_move_btn()
        self._redraw()
        self._refresh_title()
        self.status.configure(text="Moving — drag to position, Place to drop")

    def _place_float(self) -> None:
        if not self.float_items:
            self.moving = False
            self._update_move_btn()
            return
        # Stamp; anything outside grid is discarded
        for lx, ly, idx in self.float_items:
            wx = self.float_ox + lx
            wy = self.float_oy + ly
            if 0 <= wx < self.doc.width and 0 <= wy < self.doc.height:
                self.doc.set_pixel(wx, wy, idx)
        self.float_items = []
        self.moving = False
        self.sel_cells = set()
        self.doc.dirty = True
        self._update_move_btn()
        self._redraw()
        self._refresh_title()
        self.status.configure(text="Placed (off-grid clipped)")

    def _apply_brush(self, cx: int, cy: int, idx: int) -> None:
        b = self.brush
        # center-ish for even sizes: top-left of brush footprint
        x0 = cx - (b // 2)
        y0 = cy - (b // 2)
        for dy in range(b):
            for dx in range(b):
                self.doc.set_pixel(x0 + dx, y0 + dy, idx)

    def _on_press(self, event) -> None:
        self.canvas.focus_set()
        # Alt+drag pans (also handled by Alt-Button bindings)
        if self._alt_held or (event.state & 0x20000):
            self._pan_start(event)
            return
        cell = self._event_to_cell(event)
        # Moving floating selection: drag from anywhere
        if self.moving and self.float_items:
            self._paint_down = True
            self._move_drag_last = self._event_to_cell_unclamped(event)
            return
        if cell is None:
            # Allow starting box select only on grid
            if self.tool.get() in ("sel_box", "sel_free"):
                return
            return
        self._paint_down = True
        self._last_cell = cell
        t = self.tool.get()
        if t == "sel_box":
            self._sel_box_start = cell
            self._sel_box_end = cell
            self._redraw()
            return
        if t == "sel_free":
            # Shift = add to selection; otherwise start fresh
            if not (event.state & 0x0001):
                self.sel_cells = set()
            self.sel_cells.add(cell)
            self._redraw()
            return
        self._stroke(cell[0], cell[1])

    def _on_drag(self, event) -> None:
        if self._panning or self._alt_held:
            self._pan_move(event)
            return
        if not self._paint_down:
            return
        if self.moving and self.float_items:
            cur = self._event_to_cell_unclamped(event)
            if cur is None or self._move_drag_last is None:
                return
            dx = cur[0] - self._move_drag_last[0]
            dy = cur[1] - self._move_drag_last[1]
            if dx or dy:
                self.float_ox += dx
                self.float_oy += dy
                self._move_drag_last = cur
                self._redraw()
            return
        cell = self._event_to_cell(event)
        t = self.tool.get()
        if t == "sel_box":
            if cell is not None and self._sel_box_start is not None:
                self._sel_box_end = cell
                self._redraw()
            return
        if t == "sel_free":
            if cell is not None and cell != self._last_cell:
                if self._last_cell:
                    self._line_select(self._last_cell[0], self._last_cell[1], cell[0], cell[1])
                else:
                    self.sel_cells.add(cell)
                self._last_cell = cell
                self._redraw()
            return
        if cell is None or cell == self._last_cell:
            return
        if self._last_cell:
            self._line_stroke(self._last_cell[0], self._last_cell[1], cell[0], cell[1])
        else:
            self._stroke(cell[0], cell[1])
        self._last_cell = cell

    def _on_release(self, event) -> None:
        if self._panning:
            self._pan_end(event)
            return
        t = self.tool.get()
        if t == "sel_box" and self._sel_box_start and self._sel_box_end:
            x0, y0 = self._sel_box_start
            x1, y1 = self._sel_box_end
            if x0 > x1:
                x0, x1 = x1, x0
            if y0 > y1:
                y0, y1 = y1, y0
            # Shift adds
            if not (event.state & 0x0001):
                self.sel_cells = set()
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    if 0 <= x < self.doc.width and 0 <= y < self.doc.height:
                        self.sel_cells.add((x, y))
            self._sel_box_start = None
            self._sel_box_end = None
            self._redraw()
        self._paint_down = False
        self._last_cell = None
        self._move_drag_last = None
        self._refresh_title()
        self._update_move_btn()

    def _on_rpress(self, event) -> None:
        # Right-click erase (if trackpad supports it)
        cell = self._event_to_cell(event)
        if cell:
            self._erase_stroke(cell[0], cell[1])
            self._last_cell = cell
            self._paint_down = True  # allow B3-Motion if available

    def _on_rdrag(self, event) -> None:
        cell = self._event_to_cell(event)
        if cell is None or cell == self._last_cell:
            return
        if self._last_cell:
            self._line_erase(self._last_cell[0], self._last_cell[1], cell[0], cell[1])
        else:
            self._erase_stroke(cell[0], cell[1])
        self._last_cell = cell

    def _on_motion(self, event) -> None:
        cell = self._event_to_cell(event)
        sp = " SPACE" if self._space_held else ""
        et = self._effective_tool()
        if cell:
            self.status.configure(
                text=f"{self.doc.width}×{self.doc.height}  |  {cell[0]},{cell[1]}  |  "
                f"{et}{sp}  |  brush {self.brush}×{self.brush}"
            )
        else:
            self.status.configure(text=f"{self.doc.width}×{self.doc.height}  |  {et}{sp}")

    def _erase_stroke(self, x: int, y: int) -> None:
        self._apply_brush(x, y, 0)
        self._redraw()

    def _line_erase(self, x0: int, y0: int, x1: int, y1: int) -> None:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._erase_stroke(x0, y0)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def _stroke(self, x: int, y: int) -> None:
        tool = self._effective_tool()
        if tool == "eye":
            self.color_idx = self.doc.get_pixel(x, y)
            self._rebuild_palette_swatches()
            return
        if tool == "fill":
            # Space+fill already maps to erase via _effective_tool
            self.doc.flood_fill(x, y, self.color_idx)
            self._redraw()
            return
        idx = 0 if tool == "erase" else self.color_idx
        self._apply_brush(x, y, idx)
        self._redraw()

    def _line_stroke(self, x0: int, y0: int, x1: int, y1: int) -> None:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._stroke(x0, y0)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def _on_resize(self, event) -> None:
        if event.widget is self.root:
            self.root.after_idle(self._redraw)

    def _redraw(self) -> None:
        if self._rebuild_ui_lock:
            return
        self.canvas.delete("all")
        ox, oy, cell, _ = self._layout_metrics()
        w, h = self.doc.width, self.doc.height
        total_w = ox * 2 + w * cell
        total_h = oy * 2 + h * cell
        self.canvas.configure(scrollregion=(0, 0, total_w, total_h))

        # Empty cells (index 0): solid canvas BG or checker — never confused with paint
        for y in range(h):
            for x in range(w):
                px = ox + x * cell
                py = oy + y * cell
                idx = self.doc.pixels[y][x]
                if idx == 0:
                    if self.use_checker.get():
                        c = Theme.CHECKER_A if (x + y) % 2 == 0 else Theme.CHECKER_B
                    else:
                        c = self.canvas_bg
                else:
                    idx = max(0, min(idx, len(self.doc.palette) - 1))
                    c = self.doc.palette[idx]
                self.canvas.create_rectangle(
                    px, py, px + cell, py + cell, fill=c, outline="", width=0
                )

        if self.show_grid.get() and cell >= 4:
            for x in range(w + 1):
                X = ox + x * cell
                self.canvas.create_line(X, oy, X, oy + h * cell, fill=Theme.GRID_LINE)
            for y in range(h + 1):
                Y = oy + y * cell
                self.canvas.create_line(ox, Y, ox + w * cell, Y, fill=Theme.GRID_LINE)

        # Selection overlay (marching-ish green outline)
        if self.sel_cells and not self.moving:
            for sx, sy in self.sel_cells:
                px = ox + sx * cell
                py = oy + sy * cell
                self.canvas.create_rectangle(
                    px, py, px + cell, py + cell,
                    outline=Theme.GREEN, width=max(1, cell // 8),
                )

        # Rubber-band box while dragging
        if self._sel_box_start and self._sel_box_end:
            x0, y0 = self._sel_box_start
            x1, y1 = self._sel_box_end
            if x0 > x1:
                x0, x1 = x1, x0
            if y0 > y1:
                y0, y1 = y1, y0
            self.canvas.create_rectangle(
                ox + x0 * cell, oy + y0 * cell,
                ox + (x1 + 1) * cell, oy + (y1 + 1) * cell,
                outline=Theme.GREEN, width=2, dash=(4, 2),
            )

        # Floating selection (can be off-grid)
        if self.moving and self.float_items:
            for lx, ly, idx in self.float_items:
                wx = self.float_ox + lx
                wy = self.float_oy + ly
                px = ox + wx * cell
                py = oy + wy * cell
                idx = max(0, min(idx, len(self.doc.palette) - 1))
                c = self.doc.palette[idx]
                self.canvas.create_rectangle(
                    px, py, px + cell, py + cell,
                    fill=c, outline=Theme.GREEN, width=1,
                )

        # outer border
        self.canvas.create_rectangle(
            ox, oy, ox + w * cell, oy + h * cell,
            outline=Theme.GREEN_DK, width=2,
        )

        self._draw_preview()
        self._update_info()
        self._update_move_btn()

    def _draw_preview(self) -> None:
        self.preview_canvas.delete("all")
        scale = max(1, min(128 // max(1, self.doc.width), 128 // max(1, self.doc.height)))
        img = Image.new("RGBA", (self.doc.width * scale, self.doc.height * scale), (0, 0, 0, 0))
        px = img.load()
        for y in range(self.doc.height):
            for x in range(self.doc.width):
                idx = self.doc.pixels[y][x]
                if idx == 0:
                    continue
                idx = max(0, min(idx, len(self.doc.palette) - 1))
                r, g, b = hex_to_rgb(self.doc.palette[idx])
                for dy in range(scale):
                    for dx in range(scale):
                        px[x * scale + dx, y * scale + dy] = (r, g, b, 255)
        # center in 128 box
        self._photo = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(64, 64, image=self._photo)

    def _update_info(self) -> None:
        p = self.doc.path or "(unsaved)"
        et = self._effective_tool()
        sp = " +Space" if self._space_held else ""
        self.info.configure(
            text=(
                f"{self.doc.width} × {self.doc.height}\n"
                f"zoom: {self.cell_px}px/cell\n"
                f"palette: {len(self.doc.palette)} slots\n"
                f"brush: {self.brush}×{self.brush}\n"
                f"tool: {et}{sp}\n"
                f"{'modified' if self.doc.dirty else 'clean'}\n\n"
                f"{Path(p).name if self.doc.path else p}"
            )
        )

    def _refresh_title(self) -> None:
        name = Path(self.doc.path).name if self.doc.path else "Untitled"
        star = "*" if self.doc.dirty else ""
        self.root.title(f"{star}{name} — {APP_NAME}")

    # ----- commands -----
    def _confirm_discard(self) -> bool:
        if not self.doc.dirty:
            return True
        return messagebox.askyesno(
            APP_NAME,
            "Discard unsaved changes?",
            parent=self.root,
        )

    def cmd_new(self) -> None:
        if not self._confirm_discard():
            return
        w = simpledialog.askinteger(
            "New", "Width (pixels):", initialvalue=DEFAULT_GRID_W,
            minvalue=1, maxvalue=256, parent=self.root,
        )
        if not w:
            return
        h = simpledialog.askinteger(
            "New", "Height (pixels):", initialvalue=DEFAULT_GRID_H,
            minvalue=1, maxvalue=256, parent=self.root,
        )
        if not h:
            return
        self.doc = PixelDocument(w, h, list(DEFAULT_PALETTE))
        self.color_idx = 1
        self._rebuild_palette_swatches()
        self._refresh_title()
        self._redraw()

    def cmd_resize(self) -> None:
        w = simpledialog.askinteger(
            "Resize", "New width:", initialvalue=self.doc.width,
            minvalue=1, maxvalue=256, parent=self.root,
        )
        if not w:
            return
        h = simpledialog.askinteger(
            "Resize", "New height:", initialvalue=self.doc.height,
            minvalue=1, maxvalue=256, parent=self.root,
        )
        if not h:
            return
        self.doc.resize(w, h, keep=True)
        self._refresh_title()
        self._redraw()

    def cmd_clear(self) -> None:
        if messagebox.askyesno(APP_NAME, "Clear all pixels?", parent=self.root):
            for y in range(self.doc.height):
                for x in range(self.doc.width):
                    self.doc.pixels[y][x] = 0
            self.doc.dirty = True
            self._redraw()
            self._refresh_title()

    def cmd_open(self) -> None:
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Open project",
            filetypes=[
                ("Pixel Painter", "*.ppix"),
                ("PNG image", "*.png"),
                ("All", "*.*"),
            ],
        )
        if path:
            self._open_path(path)

    def _open_path(self, path: str) -> None:
        try:
            p = Path(path)
            if p.suffix.lower() == ".ppix":
                self.doc = PixelDocument.load_ppix(path)
            elif p.suffix.lower() == ".png":
                self.doc = self._import_png(path)
            else:
                messagebox.showerror(APP_NAME, "Open .ppix or .png", parent=self.root)
                return
            self.color_idx = min(1, len(self.doc.palette) - 1)
            self.palette_count.set(len(self.doc.palette))
            self._rebuild_palette_swatches()
            self._rebuild_recent_menu()
            self._refresh_title()
            self._redraw()
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Open failed:\n{ex}", parent=self.root)

    def _import_png(self, path: str) -> PixelDocument:
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        if w > 256 or h > 256:
            raise ValueError("PNG larger than 256×256 — resize first")
        # Build palette from unique colors
        colors = {}
        palette = ["#000000"]  # 0 transparent / black
        px = img.load()
        pixels = [[0 for _ in range(w)] for _ in range(h)]
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a < 128:
                    pixels[y][x] = 0
                    continue
                key = (r, g, b)
                if key not in colors:
                    if len(palette) >= 64:
                        # nearest existing
                        best_i, best_d = 1, 1e9
                        for i, hexc in enumerate(palette):
                            if i == 0:
                                continue
                            rr, gg, bb = hex_to_rgb(hexc)
                            d = (rr - r) ** 2 + (gg - g) ** 2 + (bb - b) ** 2
                            if d < best_d:
                                best_d, best_i = d, i
                        colors[key] = best_i
                    else:
                        colors[key] = len(palette)
                        palette.append(rgb_to_hex(r, g, b))
                pixels[y][x] = colors[key]
        doc = PixelDocument(w, h, palette)
        doc.pixels = pixels
        doc.path = None
        doc.dirty = True
        add_recent(path)
        return doc

    def cmd_save(self) -> None:
        if self.doc.path and self.doc.path.lower().endswith(".ppix"):
            self.doc.save_ppix(self.doc.path)
            self._rebuild_recent_menu()
            self._refresh_title()
            self._update_info()
        else:
            self.cmd_save_as()

    def cmd_save_as(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save As",
            defaultextension=".ppix",
            filetypes=[("Pixel Painter project", "*.ppix")],
            initialfile="sprite.ppix",
        )
        if path:
            if not path.lower().endswith(".ppix"):
                path += ".ppix"
            self.doc.save_ppix(path)
            self._rebuild_recent_menu()
            self._refresh_title()
            self._update_info()

    def cmd_export_png(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export PNG",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            initialfile="sprite.png",
        )
        if not path:
            return
        scale = simpledialog.askinteger(
            "Export PNG",
            "Integer scale (1 = 1:1 pixel-perfect):",
            initialvalue=1,
            minvalue=1,
            maxvalue=64,
            parent=self.root,
        )
        if not scale:
            return
        try:
            self.doc.export_png(path, scale=scale, transparent_zero=True)
            self._rebuild_recent_menu()
            messagebox.showinfo(APP_NAME, f"Exported PNG ×{scale}\n{path}", parent=self.root)
        except Exception as ex:
            messagebox.showerror(APP_NAME, str(ex), parent=self.root)

    def cmd_export_c(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export C RGB565 header",
            defaultextension=".h",
            filetypes=[("C header", "*.h")],
            initialfile="sprite.h",
        )
        if not path:
            return
        name = simpledialog.askstring("Array name", "C identifier:", initialvalue="sprite", parent=self.root)
        if not name:
            return
        name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        try:
            self.doc.export_c_rgb565(path, array_name=name)
            messagebox.showinfo(APP_NAME, f"Exported RGB565 C array\n{path}", parent=self.root)
        except Exception as ex:
            messagebox.showerror(APP_NAME, str(ex), parent=self.root)

    def cmd_edit_color(self) -> None:
        """HSV color wheel + value slider — drag on the wheel to pick."""
        idx = self.color_idx
        cur = self.doc.palette[idx]
        r0, g0, b0 = hex_to_rgb(cur)
        h0, s0, v0 = rgb_to_hsv(r0, g0, b0)

        dlg = tk.Toplevel(self.root)
        dlg.title(f"Color wheel — slot {idx}")
        dlg.configure(bg=Theme.BG_PANEL)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.geometry("340x420")

        self._label(
            dlg,
            "Drag on the wheel  ·  Value slider  ·  Apply",
            bg=Theme.BG_PANEL,
            fg=Theme.FG_DIM,
        ).pack(pady=(8, 4))

        state = {"h": h0, "s": s0, "v": max(0.05, v0), "hex": cur}

        wheel_size = 220
        wheel_cv = tk.Canvas(
            dlg, width=wheel_size, height=wheel_size,
            bg=Theme.BG, highlightthickness=1, highlightbackground=Theme.BORDER,
            cursor="crosshair",
        )
        wheel_cv.pack(pady=4)

        prev = tk.Canvas(
            dlg, width=120, height=36, bg=cur,
            highlightthickness=2, highlightbackground=Theme.GREEN,
        )
        prev.pack(pady=6)
        hex_lab = self._label(dlg, cur, bg=Theme.BG_PANEL, font=("Consolas", 11))
        hex_lab.pack()

        val_var = tk.DoubleVar(value=state["v"] * 100)

        def rebuild_wheel() -> None:
            img = make_hsv_wheel(wheel_size, value=state["v"])
            self._wheel_photo = ImageTk.PhotoImage(img)
            wheel_cv.delete("all")
            wheel_cv.create_image(0, 0, anchor=tk.NW, image=self._wheel_photo)
            # marker
            cx = cy = wheel_size // 2
            radius = wheel_size // 2 - 2
            ang = state["h"] * 2 * math.pi - math.pi
            dist = state["s"] * radius
            mx = cx + math.cos(ang) * dist
            my = cy + math.sin(ang) * dist
            wheel_cv.create_oval(mx - 5, my - 5, mx + 5, my + 5, outline=Theme.FG, width=2)
            wheel_cv.create_oval(mx - 3, my - 3, mx + 3, my + 3, outline=Theme.BG, width=1)

        def update_preview() -> None:
            rr, gg, bb = hsv_to_rgb(state["h"], state["s"], state["v"])
            hx = rgb_to_hex(rr, gg, bb)
            state["hex"] = hx
            prev.configure(bg=hx)
            hex_lab.configure(text=hx)

        def pick_from_xy(x: int, y: int) -> None:
            cx = cy = wheel_size // 2
            radius = wheel_size // 2 - 2
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1:
                dist = 1
            sat = min(1.0, dist / radius)
            if dist > radius + 4:
                return
            ang = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
            state["h"] = ang
            state["s"] = sat
            rebuild_wheel()
            update_preview()

        def on_wheel_press(event) -> None:
            pick_from_xy(event.x, event.y)

        def on_wheel_drag(event) -> None:
            pick_from_xy(event.x, event.y)

        wheel_cv.bind("<ButtonPress-1>", on_wheel_press)
        wheel_cv.bind("<B1-Motion>", on_wheel_drag)

        self._label(dlg, "Brightness (Value)", bg=Theme.BG_PANEL, fg=Theme.FG_DIM).pack()
        val_scale = tk.Scale(
            dlg,
            from_=5,
            to=100,
            orient=tk.HORIZONTAL,
            variable=val_var,
            bg=Theme.BG_PANEL,
            fg=Theme.FG,
            troughcolor=Theme.BG_INPUT,
            highlightthickness=0,
            activebackground=Theme.GREEN,
            length=220,
            showvalue=True,
            command=lambda _=None: on_value(),
        )
        val_scale.pack()

        def on_value() -> None:
            state["v"] = max(0.05, float(val_var.get()) / 100.0)
            rebuild_wheel()
            update_preview()

        # Hex entry fallback
        ent = tk.Entry(dlg, bg=Theme.BG_INPUT, fg=Theme.FG, insertbackground=Theme.FG, width=12)
        ent.insert(0, cur)
        ent.pack(pady=4)

        def from_entry(*_):
            try:
                t = ent.get().strip()
                if not t.startswith("#"):
                    t = "#" + t
                rr, gg, bb = hex_to_rgb(t)
                hh, ss, vv = rgb_to_hsv(rr, gg, bb)
                state["h"], state["s"], state["v"] = hh, ss, max(0.05, vv)
                val_var.set(state["v"] * 100)
                rebuild_wheel()
                update_preview()
            except Exception:
                pass

        ent.bind("<Return>", from_entry)

        def apply() -> None:
            self.doc.palette[idx] = state["hex"]
            self.doc.dirty = True
            self._rebuild_palette_swatches()
            self._redraw()
            self._refresh_title()
            dlg.destroy()

        row = tk.Frame(dlg, bg=Theme.BG_PANEL)
        row.pack(pady=10)
        b1 = tk.Button(row, text="Apply", command=apply)
        self._style_btn(b1, active=True)
        b1.pack(side=tk.LEFT, padx=4)
        b2 = tk.Button(row, text="Screen pick", command=lambda: (dlg.destroy(), self.cmd_screen_pick("palette")))
        self._style_btn(b2)
        b2.pack(side=tk.LEFT, padx=4)
        b3 = tk.Button(row, text="Cancel", command=dlg.destroy)
        self._style_btn(b3)
        b3.pack(side=tk.LEFT, padx=4)

        rebuild_wheel()
        update_preview()

    def cmd_set_bg(self) -> None:
        """Type a hex / R G B for empty-cell background (editor only — not exported)."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Canvas background")
        dlg.configure(bg=Theme.BG_PANEL)
        dlg.transient(self.root)
        dlg.grab_set()
        self._label(
            dlg,
            "Color under empty pixels (index 0).\n"
            "Does not export — only for seeing paint vs empty.\n"
            "Use #rrggbb or R G B",
            bg=Theme.BG_PANEL,
            justify=tk.LEFT,
        ).pack(padx=12, pady=8)
        ent = tk.Entry(dlg, bg=Theme.BG_INPUT, fg=Theme.FG, insertbackground=Theme.FG, width=18)
        ent.insert(0, self.canvas_bg)
        ent.pack(padx=12)
        prev = tk.Canvas(
            dlg, width=100, height=36, bg=self.canvas_bg,
            highlightthickness=1, highlightbackground=Theme.BORDER,
        )
        prev.pack(pady=8)

        def preview(*_):
            try:
                t = ent.get().strip()
                if t.startswith("#"):
                    rr, gg, bb = hex_to_rgb(t)
                else:
                    parts = t.replace(",", " ").split()
                    rr, gg, bb = int(parts[0]), int(parts[1]), int(parts[2])
                prev.configure(bg=rgb_to_hex(rr, gg, bb))
            except Exception:
                pass

        ent.bind("<KeyRelease>", preview)

        def ok():
            try:
                t = ent.get().strip()
                if t.startswith("#"):
                    hx = t
                else:
                    parts = t.replace(",", " ").split()
                    hx = rgb_to_hex(int(parts[0]), int(parts[1]), int(parts[2]))
                hex_to_rgb(hx)
                self._set_canvas_bg(hx)
                dlg.destroy()
            except Exception:
                messagebox.showerror(APP_NAME, "Invalid color", parent=dlg)

        row = tk.Frame(dlg, bg=Theme.BG_PANEL)
        row.pack(pady=8)
        b1 = tk.Button(row, text="Apply", command=ok)
        self._style_btn(b1, active=True)
        b1.pack(side=tk.LEFT, padx=4)
        b2 = tk.Button(row, text="Pick from screen", command=lambda: (dlg.destroy(), self.cmd_screen_pick_bg()))
        self._style_btn(b2)
        b2.pack(side=tk.LEFT, padx=4)
        ent.focus_set()

    def cmd_screen_pick(self, target: str = "palette") -> None:
        """Screen eyedropper → always current palette slot (no popup)."""
        self._start_screen_pick("palette" if target == "ask" else target)

    def cmd_screen_pick_bg(self) -> None:
        """Screen eyedropper → canvas background only (from View menu)."""
        self._start_screen_pick("background")

    def _start_screen_pick(self, target: str) -> None:
        self._screen_pick_target = target
        # Close any previous overlay
        if self._screen_pick_overlay is not None:
            try:
                self._screen_pick_overlay.destroy()
            except Exception:
                pass

        # Iconify main window so we can click through to other apps visually
        # (overlay still sits on top — user clicks overlay which samples real desktop under it)
        try:
            self.root.iconify()
        except Exception:
            pass

        ov = tk.Toplevel(self.root)
        self._screen_pick_overlay = ov
        ov.title("Pick color — click anywhere, Esc cancel")
        ov.attributes("-fullscreen", True)
        ov.attributes("-topmost", True)
        # Slight tint so you know pick mode is on; still see desktop enough
        try:
            ov.attributes("-alpha", 0.25)
        except Exception:
            pass
        ov.configure(bg=Theme.GREEN_DK, cursor="crosshair")
        ov.focus_force()

        hint = tk.Label(
            ov,
            text="CLICK anywhere to sample color   ·   Esc cancel",
            bg=Theme.BG,
            fg=Theme.FG,
            font=("Segoe UI", 14),
        )
        hint.place(relx=0.5, rely=0.08, anchor=tk.CENTER)

        def sample_at_pointer() -> Optional[str]:
            try:
                x = ov.winfo_pointerx()
                y = ov.winfo_pointery()
                # Hide overlay so we sample the real desktop, not our tint
                ov.withdraw()
                ov.update_idletasks()
                ov.update()
                r, g, b = grab_screen_pixel(x, y)
                return rgb_to_hex(r, g, b)
            except Exception:
                return None

        def finish(hx: Optional[str]) -> None:
            try:
                ov.destroy()
            except Exception:
                pass
            self._screen_pick_overlay = None
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass
            if hx:
                self._apply_picked_color(hx, self._screen_pick_target)
                self.status.configure(text=f"Picked {hx} → {self._screen_pick_target}")

        def on_click(_event=None) -> None:
            hx = sample_at_pointer()
            finish(hx)

        def on_escape(_event=None) -> None:
            finish(None)

        ov.bind("<Button-1>", on_click)
        ov.bind("<Escape>", on_escape)

    def cmd_about(self) -> None:
        messagebox.showinfo(
            APP_NAME,
            (
                f"{APP_NAME}\n"
                f"{APP_TAGLINE}\n"
                "License: CC BY-NC-SA 4.0 (attribution, non-commercial).\n\n"
                "Project:  .ppix  (palette + indices)\n"
                "Export PNG: lossless, scale 1 = 1:1 pixels\n"
                "Export C: RGB565 arrays for embedded targets\n\n"
                "Index 0 = transparent on PNG / 0x0000 in C\n"
                "Canvas BG is editor-only (empty vs painted cells).\n\n"
                "Space+drag: erase while Paint (trackpad-friendly).\n"
                "Box/Free select → Move → drag → Place (clips off-grid).\n"
                "Pick→slot: screen color into current palette slot.\n"
                "View menu: canvas background color.\n\n"
                "Keys: 1-4 brush  B/E/F/I  R box  L free  M move/place\n"
                "  G grid  P pick  C wheel  Esc clear select  Space invert\n"
                "  Alt+drag / middle-drag = pan  ·  Ctrl+/- zoom"
            ),
            parent=self.root,
        )

    def _on_close(self) -> None:
        self._persist_view_config()
        if self.doc.dirty and not messagebox.askyesno(
            APP_NAME, "Quit without saving?", parent=self.root
        ):
            return
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    ensure_app_dir()
    app = PixelPainterApp()
    app.run()


if __name__ == "__main__":
    main()
