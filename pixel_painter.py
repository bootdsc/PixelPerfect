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
    from PIL import Image, ImageTk, ImageGrab, ImageDraw
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
MAX_UNDO = 50


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
    n = max(2, min(256, n))
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


def empty_grid(w: int, h: int) -> List[List[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def copy_grid(pixels: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in pixels]


def snapshot_document(doc: "PixelDocument") -> dict:
    """Deep snapshot for undo (layers + palette + size)."""
    return {
        "width": doc.width,
        "height": doc.height,
        "palette": list(doc.palette),
        "active": doc.active,
        "layers": [
            {
                "name": ly.name,
                "visible": ly.visible,
                "pixels": copy_grid(ly.pixels),
            }
            for ly in doc.layers
        ],
    }


def restore_document(doc: "PixelDocument", snap: dict) -> None:
    """Restore document fields from a snapshot (in place)."""
    doc.width = int(snap["width"])
    doc.height = int(snap["height"])
    doc.palette = list(snap["palette"])
    doc.layers = []
    for ld in snap["layers"]:
        doc.layers.append(
            Layer(
                str(ld["name"]),
                doc.width,
                doc.height,
                copy_grid(ld["pixels"]),
                bool(ld.get("visible", True)),
            )
        )
    if not doc.layers:
        doc.layers = [Layer("Frame 1", doc.width, doc.height)]
    doc.active = int(snap.get("active", 0))
    doc.ensure_active()
    doc.dirty = True


def palette_index_to_rgba(
    palette: List[str], idx: int, transparent_zero: bool = True
) -> Tuple[int, int, int, int]:
    """Single place for index → RGBA (export / preview / canvas)."""
    if transparent_zero and idx == 0:
        return (0, 0, 0, 0)
    idx = max(0, min(idx, len(palette) - 1))
    r, g, b = hex_to_rgb(palette[idx])
    return (r, g, b, 255)


def render_grid_rgba(
    width: int,
    height: int,
    palette: List[str],
    index_at,
    scale: int = 1,
    transparent_zero: bool = True,
) -> Image.Image:
    """Shared nearest-neighbor RGBA render for PNG / preview / export paths."""
    scale = max(1, min(64, int(scale)))
    img = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    px = img.load()
    for y in range(height):
        for x in range(width):
            r, g, b, a = palette_index_to_rgba(
                palette, int(index_at(x, y)), transparent_zero
            )
            if a == 0:
                continue
            for dy in range(scale):
                for dx in range(scale):
                    px[x * scale + dx, y * scale + dy] = (r, g, b, a)
    return img


class Layer:
    """One frame / angle / clone — palette indices, same size as document."""

    __slots__ = ("name", "pixels", "visible")

    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        pixels: Optional[List[List[int]]] = None,
        visible: bool = True,
    ):
        self.name = name
        self.pixels = pixels if pixels is not None else empty_grid(width, height)
        self.visible = visible

    def clone(self, new_name: str) -> "Layer":
        return Layer(new_name, 0, 0, copy_grid(self.pixels), self.visible)


class PixelDocument:
    """
    Palette + layers (frames / angles / clones).
    Drawing hits the active layer. View/export composites visible layers
    bottom→top (index 0 = transparent).
    """

    def __init__(
        self,
        width: int = DEFAULT_GRID_W,
        height: int = DEFAULT_GRID_H,
        palette: Optional[List[str]] = None,
    ):
        self.width = max(1, min(256, width))
        self.height = max(1, min(256, height))
        self.palette = list(palette or DEFAULT_PALETTE)
        self.layers: List[Layer] = [Layer("Frame 1", self.width, self.height)]
        self.active = 0
        self.path: Optional[str] = None
        self.dirty = False

    @property
    def pixels(self) -> List[List[int]]:
        return self.layers[self.active].pixels

    @pixels.setter
    def pixels(self, value: List[List[int]]) -> None:
        self.layers[self.active].pixels = value

    def composite_index(self, x: int, y: int) -> int:
        for layer in reversed(self.layers):
            if not layer.visible:
                continue
            if 0 <= y < len(layer.pixels) and 0 <= x < len(layer.pixels[y]):
                idx = layer.pixels[y][x]
                if idx != 0:
                    return idx
        return 0

    def ensure_active(self) -> None:
        if not self.layers:
            self.layers = [Layer("Frame 1", self.width, self.height)]
        self.active = max(0, min(self.active, len(self.layers) - 1))

    def add_layer(self, name: Optional[str] = None, clone_active: bool = False) -> None:
        self.ensure_active()
        n = len(self.layers) + 1
        if clone_active:
            src = self.layers[self.active]
            layer = src.clone(name or f"Clone of {src.name}")
        else:
            layer = Layer(name or f"Frame {n}", self.width, self.height)
        self.layers.insert(self.active + 1, layer)
        self.active += 1
        self.dirty = True

    def delete_active_layer(self) -> bool:
        if len(self.layers) <= 1:
            return False
        del self.layers[self.active]
        self.active = min(self.active, len(self.layers) - 1)
        self.dirty = True
        return True

    def move_active_layer(self, delta: int) -> None:
        j = self.active + delta
        if j < 0 or j >= len(self.layers):
            return
        self.layers[self.active], self.layers[j] = self.layers[j], self.layers[self.active]
        self.active = j
        self.dirty = True

    def resize(self, w: int, h: int, keep: bool = True) -> None:
        w = max(1, min(256, w))
        h = max(1, min(256, h))
        for layer in self.layers:
            new_px = empty_grid(w, h)
            if keep:
                for y in range(min(h, self.height)):
                    for x in range(min(w, self.width)):
                        new_px[y][x] = layer.pixels[y][x]
            layer.pixels = new_px
        self.width, self.height = w, h
        self.dirty = True

    def scale_nearest(self, w: int, h: int) -> None:
        w = max(1, min(256, w))
        h = max(1, min(256, h))
        if w == self.width and h == self.height:
            return
        old_w, old_h = self.width, self.height
        for layer in self.layers:
            old = layer.pixels
            new_px = empty_grid(w, h)
            for y in range(h):
                sy = min(old_h - 1, (y * old_h) // h)
                for x in range(w):
                    sx = min(old_w - 1, (x * old_w) // w)
                    new_px[y][x] = old[sy][sx]
            layer.pixels = new_px
        self.width, self.height = w, h
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
            "version": 2,
            "width": self.width,
            "height": self.height,
            "palette": self.palette,
            "active": self.active,
            "layers": [
                {"name": ly.name, "visible": ly.visible, "pixels": ly.pixels}
                for ly in self.layers
            ],
            "pixels": self.pixels,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PixelDocument":
        doc = cls(data["width"], data["height"], data.get("palette"))
        layers_data = data.get("layers")
        if isinstance(layers_data, list) and layers_data:
            doc.layers = []
            for i, ld in enumerate(layers_data):
                if not isinstance(ld, dict):
                    continue
                px = ld.get("pixels") or empty_grid(doc.width, doc.height)
                name = str(ld.get("name") or f"Frame {i + 1}")
                vis = bool(ld.get("visible", True))
                doc.layers.append(Layer(name, doc.width, doc.height, px, vis))
            if not doc.layers:
                doc.layers = [Layer("Frame 1", doc.width, doc.height)]
            doc.active = int(data.get("active", 0))
            doc.ensure_active()
        else:
            px = data.get("pixels")
            if px is None:
                raise ValueError("Missing pixels")
            doc.layers = [Layer("Frame 1", doc.width, doc.height, px)]
            doc.active = 0
        for ly in doc.layers:
            if len(ly.pixels) != doc.height or any(len(r) != doc.width for r in ly.pixels):
                raise ValueError("Corrupt pixel grid in layer")
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
        img = render_grid_rgba(
            self.width,
            self.height,
            self.palette,
            self.composite_index,
            scale=scale,
            transparent_zero=transparent_zero,
        )
        img.save(path, "PNG")
        add_recent(path)

    def export_c_rgb565(self, path: str, array_name: str = "sprite") -> None:
        lines = [
            f"// Auto-generated by {APP_NAME} ({APP_AUTHOR})",
            f"// {self.width}x{self.height} RGB565 (composited layers)",
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
                idx = self.composite_index(x, y)
                if idx == 0:
                    row.append("0x0000")
                else:
                    r, g, b, _a = palette_index_to_rgba(self.palette, idx, False)
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
        self.root.minsize(720, 480)
        self.root.configure(bg=Theme.BG)
        # Start maximized (full desktop work area; still has title bar)
        try:
            self.root.state("zoomed")
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", True)
            except tk.TclError:
                sw = self.root.winfo_screenwidth()
                sh = self.root.winfo_screenheight()
                self.root.geometry(f"{sw}x{sh}+0+0")

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
        self._photo: Optional[ImageTk.PhotoImage] = None  # 1:1 side preview
        self._canvas_photo: Optional[ImageTk.PhotoImage] = None  # main view bitmap
        self._wheel_photo: Optional[ImageTk.PhotoImage] = None
        self._rebuild_ui_lock = False
        self._screen_pick_overlay: Optional[tk.Toplevel] = None
        self._screen_pick_target = "palette"
        # Display cache: avoid thousands of canvas rectangles + full layer walks
        self._comp_cache: Optional[List[List[int]]] = None
        self._redraw_job: Optional[str] = None
        self._redraw_preview = True

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

        # Undo / redo (max MAX_UNDO steps)
        self._undo_stack: List[dict] = []
        self._redo_stack: List[dict] = []
        self._hist_coalesce = False  # True while a multi-pixel stroke is open

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

    # ----- undo / redo -----
    def _hist_clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._hist_coalesce = False
        self._invalidate_composite()

    def _hist_push(self) -> None:
        """Save current document state before a mutating action."""
        self._undo_stack.append(snapshot_document(self.doc))
        while len(self._undo_stack) > MAX_UNDO:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _hist_push_once(self) -> None:
        """Push at most once until _hist_end_stroke (for paint strokes)."""
        if self._hist_coalesce:
            return
        self._hist_push()
        self._hist_coalesce = True

    def _hist_end_stroke(self) -> None:
        self._hist_coalesce = False

    def cmd_undo(self) -> None:
        if not self._undo_stack:
            self.status.configure(text="Nothing to undo")
            return
        self._hist_end_stroke()
        self._redo_stack.append(snapshot_document(self.doc))
        while len(self._redo_stack) > MAX_UNDO:
            self._redo_stack.pop(0)
        snap = self._undo_stack.pop()
        restore_document(self.doc, snap)
        self.sel_cells = set()
        self.float_items = []
        self.moving = False
        self._invalidate_composite()
        self.color_idx = min(self.color_idx, max(0, len(self.doc.palette) - 1))
        if self.color_idx == 0 and len(self.doc.palette) > 1:
            self.color_idx = 1
        self.palette_count.set(len(self.doc.palette))
        self._rebuild_palette_swatches()
        self._rebuild_layer_list()
        self._redraw(update_preview=True)
        self._refresh_title()
        self.status.configure(
            text=f"Undo  ·  {len(self._undo_stack)} left  ·  redo {len(self._redo_stack)}"
        )

    def cmd_redo(self) -> None:
        if not self._redo_stack:
            self.status.configure(text="Nothing to redo")
            return
        self._hist_end_stroke()
        self._undo_stack.append(snapshot_document(self.doc))
        while len(self._undo_stack) > MAX_UNDO:
            self._undo_stack.pop(0)
        snap = self._redo_stack.pop()
        restore_document(self.doc, snap)
        self.sel_cells = set()
        self.float_items = []
        self.moving = False
        self._invalidate_composite()
        self.color_idx = min(self.color_idx, max(0, len(self.doc.palette) - 1))
        if self.color_idx == 0 and len(self.doc.palette) > 1:
            self.color_idx = 1
        self.palette_count.set(len(self.doc.palette))
        self._rebuild_palette_swatches()
        self._rebuild_layer_list()
        self._redraw(update_preview=True)
        self._refresh_title()
        self.status.configure(
            text=f"Redo  ·  undo {len(self._undo_stack)}  ·  redo left {len(self._redo_stack)}"
        )

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root, bg=Theme.BG_PANEL, fg=Theme.FG, tearoff=0,
                          activebackground=Theme.GREEN_DK, activeforeground=Theme.FG)
        file_m = tk.Menu(menubar, tearoff=0, bg=Theme.BG_PANEL, fg=Theme.FG,
                         activebackground=Theme.GREEN_DK, activeforeground=Theme.FG)
        file_m.add_command(label="New…", command=self.cmd_new, accelerator="Ctrl+N")
        file_m.add_command(label="Open…", command=self.cmd_open, accelerator="Ctrl+O")
        file_m.add_command(label="Import & pixelate…", command=self.cmd_pixelate_import, accelerator="Ctrl+I")
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
        edit_m.add_command(label="Undo", command=self.cmd_undo, accelerator="Ctrl+Z")
        edit_m.add_command(label="Redo", command=self.cmd_redo, accelerator="Ctrl+Shift+Z")
        edit_m.add_separator()
        edit_m.add_command(label="Replace drawn color…", command=self.cmd_replace_color)
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
            to=256,
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
        b_rep = tk.Button(left, text="Replace all of color…", command=self.cmd_replace_color)
        self._style_btn(b_rep)
        b_rep.pack(fill=tk.X, padx=8, pady=(0, 4))

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

        # Right panel — scrollable so layers/buttons stay reachable in short windows
        right_shell = tk.Frame(body, bg=Theme.BG_PANEL, width=220)
        right_shell.pack(side=tk.RIGHT, fill=tk.Y)
        right_shell.pack_propagate(False)

        right_sb = tk.Scrollbar(
            right_shell,
            orient=tk.VERTICAL,
            bg=Theme.BG_PANEL,
            troughcolor=Theme.BG,
            activebackground=Theme.GREEN_DK,
        )
        right_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_canvas = tk.Canvas(
            right_shell,
            bg=Theme.BG_PANEL,
            highlightthickness=0,
            bd=0,
            width=200,
            yscrollcommand=right_sb.set,
        )
        self.right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_sb.configure(command=self.right_canvas.yview)

        right = tk.Frame(self.right_canvas, bg=Theme.BG_PANEL)
        self._right_window = self.right_canvas.create_window(
            (0, 0), window=right, anchor=tk.NW
        )

        def _right_inner_cfg(_event=None) -> None:
            self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))

        def _right_canvas_cfg(event) -> None:
            # Stretch inner frame to canvas width
            self.right_canvas.itemconfigure(self._right_window, width=max(1, event.width))

        right.bind("<Configure>", _right_inner_cfg)
        self.right_canvas.bind("<Configure>", _right_canvas_cfg)

        def _right_wheel(event) -> str:
            # Windows / Mac: event.delta; only when pointer is over the side panel
            delta = int(getattr(event, "delta", 0) or 0)
            if delta:
                self.right_canvas.yview_scroll(int(-1 * (delta / 120)), "units")
            return "break"

        def _right_wheel_linux(event) -> str:
            if getattr(event, "num", 0) == 4:
                self.right_canvas.yview_scroll(-3, "units")
            elif getattr(event, "num", 0) == 5:
                self.right_canvas.yview_scroll(3, "units")
            return "break"

        def _bind_right_wheel(_event=None) -> None:
            self.right_canvas.bind_all("<MouseWheel>", _right_wheel)
            self.right_canvas.bind_all("<Button-4>", _right_wheel_linux)
            self.right_canvas.bind_all("<Button-5>", _right_wheel_linux)

        def _unbind_right_wheel(_event=None) -> None:
            self.right_canvas.unbind_all("<MouseWheel>")
            self.right_canvas.unbind_all("<Button-4>")
            self.right_canvas.unbind_all("<Button-5>")
            # Keep Ctrl+wheel zoom on main canvas
            self.canvas.bind("<Control-MouseWheel>", self._on_zoom_wheel)

        for w in (right_shell, self.right_canvas, right):
            w.bind("<Enter>", _bind_right_wheel)
            w.bind("<Leave>", _unbind_right_wheel)

        self._label(right, "DOCUMENT", font=("Segoe UI", 9, "bold")).pack(pady=(10, 6))
        self.info = self._label(right, "", justify=tk.LEFT, fg=Theme.FG_DIM)
        self.info.pack(anchor=tk.W, padx=10)

        for text, cmd in [
            ("New grid…", self.cmd_new),
            ("Resize…", self.cmd_resize),
            ("Import & pixelate…", self.cmd_pixelate_import),
            ("Save As…", self.cmd_save_as),
            ("Export PNG…", self.cmd_export_png),
            ("Export C…", self.cmd_export_c),
        ]:
            b = tk.Button(right, text=text, command=cmd)
            self._style_btn(b)
            b.pack(fill=tk.X, padx=10, pady=3)

        self._label(right, "LAYERS / FRAMES", font=("Segoe UI", 9, "bold")).pack(
            pady=(14, 4)
        )
        self._label(
            right,
            "Clone for animation frames\nor side/angle views.\n"
            "Paint hits active only.\n"
            "View = all visible stacked.\n"
            "Scroll this panel if short.",
            fg=Theme.FG_DIM,
            justify=tk.LEFT,
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W, padx=10, pady=(0, 4))

        self.layer_list = tk.Listbox(
            right,
            height=8,
            bg=Theme.BG_INPUT,
            fg=Theme.FG,
            selectbackground=Theme.GREEN_DK,
            selectforeground=Theme.FG,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            activestyle="none",
            font=("Segoe UI", 9),
            exportselection=False,
        )
        self.layer_list.pack(fill=tk.X, padx=10, pady=2)
        self.layer_list.bind("<<ListboxSelect>>", self._on_layer_select)
        self.layer_list.bind("<Double-Button-1>", lambda e: self.cmd_rename_layer())

        lr = tk.Frame(right, bg=Theme.BG_PANEL)
        lr.pack(fill=tk.X, padx=10, pady=2)
        for text, cmd in [
            ("+ New", self.cmd_layer_new),
            ("Clone", self.cmd_layer_clone),
        ]:
            b = tk.Button(lr, text=text, command=cmd)
            self._style_btn(b)
            b.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        lr2 = tk.Frame(right, bg=Theme.BG_PANEL)
        lr2.pack(fill=tk.X, padx=10, pady=2)
        for text, cmd in [
            ("▲", lambda: self.cmd_layer_move(1)),
            ("▼", lambda: self.cmd_layer_move(-1)),
            ("👁", self.cmd_layer_toggle_vis),
            ("✕", self.cmd_layer_delete),
        ]:
            b = tk.Button(lr2, text=text, command=cmd, width=3)
            self._style_btn(b)
            b.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        b_ren = tk.Button(right, text="Rename…", command=self.cmd_rename_layer)
        self._style_btn(b_ren)
        b_ren.pack(fill=tk.X, padx=10, pady=2)

        self.preview_label = self._label(right, "1:1 preview", fg=Theme.FG_DIM)
        self.preview_label.pack(pady=(12, 4))
        self.preview_canvas = tk.Canvas(
            right, width=128, height=128, bg=Theme.CANVAS_BG, highlightthickness=1,
            highlightbackground=Theme.BORDER,
        )
        self.preview_canvas.pack(padx=10, pady=(0, 16))

        self._rebuild_palette_swatches()
        self._rebuild_layer_list()
        self._update_info()
        # Ensure scrollregion after first layout
        self.root.after(100, _right_inner_cfg)

    def _bind_keys(self) -> None:
        r = self.root
        r.bind("<Control-n>", lambda e: self.cmd_new())
        r.bind("<Control-o>", lambda e: self.cmd_open())
        r.bind("<Control-i>", lambda e: self.cmd_pixelate_import())
        r.bind("<Control-I>", lambda e: self.cmd_pixelate_import())
        r.bind("<Control-s>", lambda e: self.cmd_save())
        r.bind("<Control-S>", lambda e: self.cmd_save_as())
        r.bind("<Control-z>", lambda e: self.cmd_undo())
        r.bind("<Control-Z>", lambda e: self.cmd_undo())
        r.bind("<Control-Shift-z>", lambda e: self.cmd_redo())
        r.bind("<Control-Shift-Z>", lambda e: self.cmd_redo())
        r.bind("<Control-y>", lambda e: self.cmd_redo())  # common Windows redo
        r.bind("<Control-Y>", lambda e: self.cmd_redo())
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
        self._invalidate_composite()  # checker / empty fill may change
        self._redraw(update_preview=True)

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
            self._hist_push()
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
        n = max(2, min(256, n))
        self.palette_count.set(n)
        old_len = len(self.doc.palette)
        if n != old_len:
            self._hist_push()
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
        if self.doc.dirty or any(
            any(px != 0 for px in row)
            for ly in self.doc.layers
            for row in ly.pixels
        ):
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
        n = max(2, min(256, n))
        self._hist_push()
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
            "Number of color slots (2–256).\n"
            "Existing colors kept; new slots = white.",
            initialvalue=len(self.doc.palette),
            minvalue=2,
            maxvalue=256,
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
        self._hist_push()
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
        self._hist_push()
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
        # One history entry for whole stroke / fill
        if t in ("paint", "erase", "fill") or self._effective_tool() in (
            "paint",
            "erase",
            "fill",
        ):
            self._hist_push_once()
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
        self._hist_end_stroke()
        # Final paint of stroke includes 1:1 preview (skipped during drag for speed)
        self._schedule_redraw(preview=True)
        self._refresh_title()
        self._update_move_btn()

    def _on_rpress(self, event) -> None:
        # Right-click erase (if trackpad supports it)
        cell = self._event_to_cell(event)
        if cell:
            self._hist_push_once()
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

    def _erase_stroke(self, x: int, y: int, schedule: bool = True) -> None:
        self._apply_brush(x, y, 0)
        self._invalidate_composite()
        if schedule:
            self._schedule_redraw(preview=False)

    def _line_erase(self, x0: int, y0: int, x1: int, y1: int) -> None:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._erase_stroke(x0, y0, schedule=False)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        self._schedule_redraw(preview=False)

    def _stroke(self, x: int, y: int, schedule: bool = True) -> None:
        tool = self._effective_tool()
        if tool == "eye":
            self.color_idx = self.doc.get_pixel(x, y)
            self._rebuild_palette_swatches()
            return
        if tool == "fill":
            self.doc.flood_fill(x, y, self.color_idx)
            self._invalidate_composite()
            self._schedule_redraw(preview=True)
            return
        idx = 0 if tool == "erase" else self.color_idx
        self._apply_brush(x, y, idx)
        # Brush only dirties a small area — drop full composite cache for correctness
        # (rebuild is cheap at ≤256²; avoid walking layers per canvas rect)
        self._invalidate_composite()
        if schedule:
            self._schedule_redraw(preview=False)

    def _line_stroke(self, x0: int, y0: int, x1: int, y1: int) -> None:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._stroke(x0, y0, schedule=False)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        self._schedule_redraw(preview=False)

    def _on_resize(self, event) -> None:
        if event.widget is self.root:
            self._schedule_redraw(preview=True)

    def _invalidate_composite(self) -> None:
        self._comp_cache = None

    def _ensure_composite_cache(self) -> None:
        """Flat index grid for display — O(w*h*layers) once, not every canvas item."""
        w, h = self.doc.width, self.doc.height
        if (
            self._comp_cache is not None
            and len(self._comp_cache) == h
            and (h == 0 or len(self._comp_cache[0]) == w)
        ):
            return
        cache = empty_grid(w, h)
        for y in range(h):
            for x in range(w):
                cache[y][x] = self.doc.composite_index(x, y)
        self._comp_cache = cache

    def _touch_composite_cells(self, cells) -> None:
        """Refresh cache for a few cells after paint (cheap)."""
        if self._comp_cache is None:
            return
        w, h = self.doc.width, self.doc.height
        for x, y in cells:
            if 0 <= x < w and 0 <= y < h:
                self._comp_cache[y][x] = self.doc.composite_index(x, y)

    def _schedule_redraw(self, preview: bool = True) -> None:
        """Coalesce many paint events into one paint of the view."""
        if preview:
            self._redraw_preview = True
        if self._redraw_job is not None:
            return
        self._redraw_job = self.root.after_idle(self._flush_redraw)

    def _flush_redraw(self) -> None:
        self._redraw_job = None
        do_prev = self._redraw_preview
        self._redraw_preview = False
        self._redraw(update_preview=do_prev)

    def _build_view_bitmap(self, cell: int) -> Image.Image:
        """1× doc → RGB, then nearest scale by cell size (one PhotoImage for the canvas)."""
        self._ensure_composite_cache()
        assert self._comp_cache is not None
        w, h = self.doc.width, self.doc.height
        base = Image.new("RGB", (w, h))
        px = base.load()
        bg = hex_to_rgb(self.canvas_bg)
        ca = hex_to_rgb(Theme.CHECKER_A)
        cb = hex_to_rgb(Theme.CHECKER_B)
        checker = self.use_checker.get()
        pal = self.doc.palette
        n_pal = len(pal)
        for y in range(h):
            row = self._comp_cache[y]
            for x in range(w):
                idx = row[x]
                if idx == 0:
                    px[x, y] = ca if (checker and (x + y) % 2 == 0) else (
                        cb if checker else bg
                    )
                else:
                    if idx >= n_pal:
                        idx = n_pal - 1
                    px[x, y] = hex_to_rgb(pal[idx])
        if cell <= 1:
            return base
        return base.resize((w * cell, h * cell), Image.Resampling.NEAREST)

    def _redraw(self, update_preview: bool = True) -> None:
        if self._rebuild_ui_lock:
            return
        ox, oy, cell, _ = self._layout_metrics()
        w, h = self.doc.width, self.doc.height
        total_w = ox * 2 + w * cell
        total_h = oy * 2 + h * cell
        self.canvas.configure(scrollregion=(0, 0, total_w, total_h))
        self.canvas.delete("all")

        # Single bitmap instead of w*h create_rectangle calls
        try:
            view = self._build_view_bitmap(cell)
            self._canvas_photo = ImageTk.PhotoImage(view)
            self.canvas.create_image(
                ox, oy, image=self._canvas_photo, anchor=tk.NW, tags=("bmp",)
            )
        except Exception:
            # Fallback: solid bg
            self.canvas.create_rectangle(
                ox, oy, ox + w * cell, oy + h * cell, fill=self.canvas_bg, outline=""
            )

        if self.show_grid.get() and cell >= 4:
            for x in range(w + 1):
                X = ox + x * cell
                self.canvas.create_line(
                    X, oy, X, oy + h * cell, fill=Theme.GRID_LINE, tags=("grid",)
                )
            for y in range(h + 1):
                Y = oy + y * cell
                self.canvas.create_line(
                    ox, Y, ox + w * cell, Y, fill=Theme.GRID_LINE, tags=("grid",)
                )

        # Selection overlay
        if self.sel_cells and not self.moving:
            lw = max(1, cell // 8)
            for sx, sy in self.sel_cells:
                px = ox + sx * cell
                py = oy + sy * cell
                self.canvas.create_rectangle(
                    px, py, px + cell, py + cell,
                    outline=Theme.GREEN, width=lw, tags=("sel",),
                )

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
                outline=Theme.GREEN, width=2, dash=(4, 2), tags=("sel",),
            )

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
                    fill=c, outline=Theme.GREEN, width=1, tags=("float",),
                )

        self.canvas.create_rectangle(
            ox, oy, ox + w * cell, oy + h * cell,
            outline=Theme.GREEN_DK, width=2, tags=("border",),
        )

        if update_preview:
            self._draw_preview()
        self._update_info()
        self._update_move_btn()

    def _draw_preview(self) -> None:
        self.preview_canvas.delete("all")
        scale = max(1, min(128 // max(1, self.doc.width), 128 // max(1, self.doc.height)))
        self._ensure_composite_cache()

        def idx_at(x: int, y: int) -> int:
            assert self._comp_cache is not None
            return self._comp_cache[y][x]

        img = render_grid_rgba(
            self.doc.width,
            self.doc.height,
            self.doc.palette,
            idx_at,
            scale=scale,
        )
        self._photo = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(64, 64, image=self._photo)

    def _update_info(self) -> None:
        p = self.doc.path or "(unsaved)"
        et = self._effective_tool()
        sp = " +Space" if self._space_held else ""
        ly = self.doc.layers[self.doc.active].name if self.doc.layers else "?"
        self.info.configure(
            text=(
                f"{self.doc.width} × {self.doc.height}\n"
                f"zoom: {self.cell_px}px/cell\n"
                f"palette: {len(self.doc.palette)} slots\n"
                f"layers: {len(self.doc.layers)}\n"
                f"active: {ly}\n"
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
        self._hist_clear()
        self._rebuild_palette_swatches()
        self._rebuild_layer_list()
        self._refresh_title()
        self._redraw()

    def cmd_resize(self) -> None:
        w = simpledialog.askinteger(
            "Resize / scale", "New width:", initialvalue=self.doc.width,
            minvalue=1, maxvalue=256, parent=self.root,
        )
        if not w:
            return
        h = simpledialog.askinteger(
            "Resize / scale", "New height:", initialvalue=self.doc.height,
            minvalue=1, maxvalue=256, parent=self.root,
        )
        if not h:
            return
        # Default = scale the art (what people expect). Crop/pad is optional.
        scale = messagebox.askyesno(
            APP_NAME,
            "Scale the image to the new size? (nearest-neighbor)\n\n"
            "Yes = stretch/shrink the whole picture\n"
            "No  = only change canvas (crop or pad, top-left stays)",
            parent=self.root,
        )
        self._hist_push()
        if scale:
            self.doc.scale_nearest(w, h)
        else:
            self.doc.resize(w, h, keep=True)
        self.sel_cells = set()
        self.float_items = []
        self.moving = False
        self._refresh_title()
        self._redraw()

    def cmd_clear(self) -> None:
        if messagebox.askyesno(
            APP_NAME,
            "Clear the active layer?",
            parent=self.root,
        ):
            self._hist_push()
            for y in range(self.doc.height):
                for x in range(self.doc.width):
                    self.doc.pixels[y][x] = 0
            self.doc.dirty = True
            self._redraw()
            self._refresh_title()

    # ----- layers / frames -----
    def _rebuild_layer_list(self) -> None:
        if not hasattr(self, "layer_list"):
            return
        self.layer_list.delete(0, tk.END)
        # Show top layer first (like most editors)
        for i in range(len(self.doc.layers) - 1, -1, -1):
            ly = self.doc.layers[i]
            eye = "●" if ly.visible else "○"
            mark = "▶ " if i == self.doc.active else "  "
            self.layer_list.insert(tk.END, f"{mark}{eye} {ly.name}")
        # Select active in listbox (inverted index)
        ui = len(self.doc.layers) - 1 - self.doc.active
        if 0 <= ui < self.layer_list.size():
            self.layer_list.selection_clear(0, tk.END)
            self.layer_list.selection_set(ui)
            self.layer_list.see(ui)

    def _on_layer_select(self, _evt=None) -> None:
        sel = self.layer_list.curselection()
        if not sel:
            return
        ui = int(sel[0])
        idx = len(self.doc.layers) - 1 - ui
        if idx == self.doc.active:
            return
        self.doc.active = max(0, min(idx, len(self.doc.layers) - 1))
        self._rebuild_layer_list()
        self._redraw()

    def cmd_layer_new(self) -> None:
        self._hist_push()
        self.doc.add_layer(clone_active=False)
        self._invalidate_composite()
        self._rebuild_layer_list()
        self._redraw(update_preview=True)
        self._refresh_title()

    def cmd_layer_clone(self) -> None:
        self._hist_push()
        self.doc.add_layer(clone_active=True)
        self._invalidate_composite()
        self._rebuild_layer_list()
        self._redraw(update_preview=True)
        self._refresh_title()

    def cmd_layer_delete(self) -> None:
        if len(self.doc.layers) <= 1:
            messagebox.showinfo(APP_NAME, "Need at least one layer.", parent=self.root)
            return
        name = self.doc.layers[self.doc.active].name
        if not messagebox.askyesno(APP_NAME, f"Delete layer “{name}”?", parent=self.root):
            return
        self._hist_push()
        self.doc.delete_active_layer()
        self._invalidate_composite()
        self._rebuild_layer_list()
        self._redraw(update_preview=True)
        self._refresh_title()

    def cmd_layer_move(self, delta: int) -> None:
        # UI ▲ = higher in stack = +1 index in list (top of stack)
        self._hist_push()
        self.doc.move_active_layer(delta)
        self._invalidate_composite()
        self._rebuild_layer_list()
        self._redraw(update_preview=True)

    def cmd_layer_toggle_vis(self) -> None:
        self._hist_push()
        ly = self.doc.layers[self.doc.active]
        ly.visible = not ly.visible
        self.doc.dirty = True
        self._invalidate_composite()
        self._rebuild_layer_list()
        self._redraw(update_preview=True)
        self._refresh_title()

    def cmd_rename_layer(self) -> None:
        ly = self.doc.layers[self.doc.active]
        name = simpledialog.askstring(
            "Rename layer",
            "Name (e.g. walk_01, side, front):",
            initialvalue=ly.name,
            parent=self.root,
        )
        if name and name.strip():
            self._hist_push()
            ly.name = name.strip()
            self.doc.dirty = True
            self._rebuild_layer_list()
            self._update_info()
            self._refresh_title()

    def cmd_open(self) -> None:
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Open project or image",
            filetypes=[
                ("Images & projects", "*.ppix;*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp"),
                ("PixelPainter project", "*.ppix"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg;*.jpeg"),
                ("BMP", "*.bmp"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._open_path(path)

    def _open_path(self, path: str) -> None:
        try:
            p = Path(path)
            suf = p.suffix.lower()
            if suf == ".ppix":
                self.doc = PixelDocument.load_ppix(path)
            elif suf in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff"):
                img = Image.open(path).convert("RGBA")
                # Large photos → pixelate dialog (block size + grid align + colors)
                if img.width > 256 or img.height > 256:
                    messagebox.showinfo(
                        APP_NAME,
                        f"Image is {img.width}×{img.height}.\n"
                        "Opening Import & pixelate so you can downscale,\n"
                        "align the grid, and limit colors.",
                        parent=self.root,
                    )
                    self._open_pixelate_dialog(img, path)
                    return
                self.doc = self._rgba_image_to_doc(img, max_colors=256, quantize=True)
                self.doc.path = None
                self.doc.dirty = True
                add_recent(path)
            else:
                messagebox.showerror(
                    APP_NAME,
                    "Open a .ppix project or image (png/jpg/bmp/gif/webp).",
                    parent=self.root,
                )
                return
            self.color_idx = min(1, len(self.doc.palette) - 1)
            self.palette_count.set(len(self.doc.palette))
            self.sel_cells = set()
            self.float_items = []
            self.moving = False
            self._hist_clear()
            self._rebuild_palette_swatches()
            self._rebuild_layer_list()
            self._rebuild_recent_menu()
            self._refresh_title()
            self._redraw()
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Open failed:\n{ex}", parent=self.root)

    @staticmethod
    def _quantize_rgba(img: Image.Image, max_colors: int) -> Image.Image:
        """
        Decimate colors without the black/purple corruption from hand-reading
        adaptive P palettes. Always round-trip through quantize → RGB.
        Transparent pixels stay transparent; they are not baked as black.
        """
        img = img.convert("RGBA")
        w, h = img.size
        max_colors = max(1, min(256, int(max_colors)))
        src = img.load()
        alpha = img.split()[3]

        # Unique opaque colors — skip if already within budget
        opaque_keys: set = set()
        over = False
        for y in range(h):
            for x in range(w):
                r, g, b, a = src[x, y]
                if a >= 128:
                    opaque_keys.add((r & 0xFF, g & 0xFF, b & 0xFF))
                    if len(opaque_keys) > max_colors:
                        over = True
                        break
            if over:
                break
        if not over:
            return img

        # Composite opaque pixels only; leave transparent as mid-gray so black
        # does not dominate the adaptive palette (common purple/black bug).
        rgb = Image.new("RGB", (w, h), (128, 128, 128))
        rpx = rgb.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = src[x, y]
                if a >= 128:
                    rpx[x, y] = (r, g, b)

        try:
            q = rgb.quantize(
                colors=max_colors,
                method=Image.Quantize.MEDIANCUT,
                dither=Image.Dither.NONE,
            )
        except Exception:
            try:
                q = rgb.quantize(
                    colors=max_colors,
                    method=Image.Quantize.MAXCOVERAGE,
                    dither=Image.Dither.NONE,
                )
            except Exception:
                q = rgb.quantize(colors=max_colors, dither=Image.Dither.NONE)

        # Critical: let Pillow map palette indices → true RGB
        q_rgb = q.convert("RGB")
        qpx = q_rgb.load()
        apx = alpha.load()
        out = Image.new("RGBA", (w, h))
        opx = out.load()
        for y in range(h):
            for x in range(w):
                if apx[x, y] < 128:
                    opx[x, y] = (0, 0, 0, 0)
                else:
                    r, g, b = qpx[x, y]
                    opx[x, y] = (int(r), int(g), int(b), 255)
        return out

    def _rgba_image_to_doc(
        self, img: Image.Image, max_colors: int = 256, quantize: bool = True
    ) -> PixelDocument:
        """Convert RGBA PIL image into a PixelDocument (palette indices)."""
        img = img.convert("RGBA")
        if quantize:
            img = self._quantize_rgba(img, max_colors)
        w, h = img.size
        if w < 1 or h < 1:
            raise ValueError("Empty image")
        if w > 256 or h > 256:
            raise ValueError("Result larger than 256×256 — use Import & pixelate")
        colors: dict = {}
        palette = ["#000000"]  # 0 transparent / black
        px = img.load()
        pixels = [[0 for _ in range(w)] for _ in range(h)]
        # max opaque slots = max_colors; index 0 reserved (up to 257 entries)
        max_pal = max(2, min(257, int(max_colors) + 1))
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a < 128:
                    pixels[y][x] = 0
                    continue
                key = (r, g, b)
                if key not in colors:
                    if len(palette) >= max_pal:
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
        doc.layers = [Layer("Frame 1", w, h, pixels)]
        doc.active = 0
        return doc

    def cmd_replace_color(self) -> None:
        """
        Remap every drawn pixel of one palette index to another.
        (Editing a swatch with the wheel already recolors that index in-place.)
        """
        src = self.color_idx
        n = len(self.doc.palette)
        dlg = tk.Toplevel(self.root)
        dlg.title("Replace drawn color")
        dlg.configure(bg=Theme.BG_PANEL)
        dlg.transient(self.root)
        dlg.grab_set()
        self._label(
            dlg,
            "Remap all pixels of one palette slot to another.\n"
            "Tip: to recolor without remapping indices, just edit the\n"
            "slot with Wheel — every pixel using that slot updates.",
            bg=Theme.BG_PANEL,
            fg=Theme.FG_DIM,
            justify=tk.LEFT,
        ).pack(padx=12, pady=8)

        row = tk.Frame(dlg, bg=Theme.BG_PANEL)
        row.pack(padx=12, pady=4)
        self._label(row, "From index:", bg=Theme.BG_PANEL).pack(side=tk.LEFT)
        from_var = tk.IntVar(value=src)
        tk.Spinbox(
            row, from_=0, to=max(0, n - 1), width=5, textvariable=from_var,
            bg=Theme.BG_INPUT, fg=Theme.FG, buttonbackground=Theme.BG_PANEL,
            highlightthickness=1, highlightbackground=Theme.BORDER,
            insertbackground=Theme.FG,
        ).pack(side=tk.LEFT, padx=6)
        from_sw = tk.Canvas(row, width=28, height=22, bg=self.doc.palette[src],
                            highlightthickness=1, highlightbackground=Theme.BORDER)
        from_sw.pack(side=tk.LEFT, padx=4)

        row2 = tk.Frame(dlg, bg=Theme.BG_PANEL)
        row2.pack(padx=12, pady=4)
        self._label(row2, "To index:", bg=Theme.BG_PANEL).pack(side=tk.LEFT)
        to_default = 0 if src != 0 else min(1, n - 1)
        to_var = tk.IntVar(value=to_default)
        tk.Spinbox(
            row2, from_=0, to=max(0, n - 1), width=5, textvariable=to_var,
            bg=Theme.BG_INPUT, fg=Theme.FG, buttonbackground=Theme.BG_PANEL,
            highlightthickness=1, highlightbackground=Theme.BORDER,
            insertbackground=Theme.FG,
        ).pack(side=tk.LEFT, padx=6)
        to_sw = tk.Canvas(
            row2, width=28, height=22,
            bg=self.doc.palette[to_default],
            highlightthickness=1, highlightbackground=Theme.BORDER,
        )
        to_sw.pack(side=tk.LEFT, padx=4)

        count_lab = self._label(dlg, "", bg=Theme.BG_PANEL, fg=Theme.GREEN)
        count_lab.pack(pady=4)

        def sync_swatches(*_):
            try:
                fi = int(from_var.get())
                ti = int(to_var.get())
                fi = max(0, min(n - 1, fi))
                ti = max(0, min(n - 1, ti))
                from_sw.configure(bg=self.doc.palette[fi])
                to_sw.configure(bg=self.doc.palette[ti])
                cnt = sum(1 for row in self.doc.pixels for v in row if v == fi)
                count_lab.configure(text=f"{cnt} pixels use index {fi}")
            except Exception:
                pass

        from_var.trace_add("write", sync_swatches)
        to_var.trace_add("write", sync_swatches)
        sync_swatches()

        def do_replace():
            try:
                fi = max(0, min(n - 1, int(from_var.get())))
                ti = max(0, min(n - 1, int(to_var.get())))
            except Exception:
                return
            if fi == ti:
                dlg.destroy()
                return
            self._hist_push()
            changed = 0
            for y in range(self.doc.height):
                for x in range(self.doc.width):
                    if self.doc.pixels[y][x] == fi:
                        self.doc.pixels[y][x] = ti
                        changed += 1
            if changed:
                self.doc.dirty = True
                self._redraw()
                self._refresh_title()
            dlg.destroy()
            self.status.configure(text=f"Replaced {changed} pixels: {fi} → {ti}")

        br = tk.Frame(dlg, bg=Theme.BG_PANEL)
        br.pack(pady=10)
        b1 = tk.Button(br, text="Replace all", command=do_replace)
        self._style_btn(b1, active=True)
        b1.pack(side=tk.LEFT, padx=4)
        b2 = tk.Button(br, text="Cancel", command=dlg.destroy)
        self._style_btn(b2)
        b2.pack(side=tk.LEFT, padx=4)

    # ------------------------------------------------------------------
    # Import & pixelate (resolution scaler + draggable sample grid)
    # ------------------------------------------------------------------
    def cmd_pixelate_import(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Import image to pixelate",
            filetypes=[
                ("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp"),
                ("All", "*.*"),
            ],
        )
        if not path:
            return
        try:
            src = Image.open(path).convert("RGBA")
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Could not open image:\n{ex}", parent=self.root)
            return
        if src.width < 2 or src.height < 2:
            messagebox.showerror(APP_NAME, "Image too small.", parent=self.root)
            return
        self._open_pixelate_dialog(src, path)

    def _open_pixelate_dialog(self, src: Image.Image, source_path: str) -> None:
        """
        Live pixelation:
          - LEFT: original image with movable green sample grid (drag to shift)
          - RIGHT: pixelated result preview
          - Block size slider + max colors (adaptive quantize)
        """
        dlg = tk.Toplevel(self.root)
        dlg.title("Import & pixelate — align grid, then Apply")
        dlg.configure(bg=Theme.BG_PANEL)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.geometry("900x620")
        dlg.minsize(700, 480)

        sw, sh = src.size
        # Default ~48px-wide output (game-asset friendly)
        default_out_w = max(8, min(128, min(sw, 48)))
        default_block = max(1, sw // default_out_w)
        st = {
            "block": default_block,
            "ox": 0,
            "oy": 0,
            "drag": None,
            "photo_src": None,
            "photo_out": None,
            "view_scale": 1.0,
            "refreshing": False,
            "refresh_job": None,
            "src_copy": src.copy(),  # stable for resize
        }

        self._label(
            dlg,
            "LEFT = original + GREEN GRID (drag to shift).  "
            "RIGHT = result.  Use Output width/height (real pixel count), not abstract block size.",
            bg=Theme.BG_PANEL,
            fg=Theme.FG,
            wraplength=860,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=10, pady=(8, 4))

        size_banner = self._label(
            dlg, "Output: — × — px", bg=Theme.BG_PANEL, fg=Theme.GREEN,
            font=("Segoe UI", 14, "bold"),
        )
        size_banner.pack(anchor=tk.W, padx=10, pady=(0, 2))
        info = self._label(dlg, "", bg=Theme.BG_PANEL, fg=Theme.FG_DIM)
        info.pack(anchor=tk.W, padx=10)

        # Two preview panes
        panes = tk.Frame(dlg, bg=Theme.BG_PANEL)
        panes.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(1, weight=1)
        panes.rowconfigure(1, weight=1)

        self._label(panes, "SOURCE + GRID (drag here to shift)", bg=Theme.BG_PANEL, fg=Theme.FG_DIM).grid(
            row=0, column=0, sticky="w"
        )
        self._label(panes, "PIXELATED RESULT", bg=Theme.BG_PANEL, fg=Theme.FG_DIM).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )

        src_cv = tk.Canvas(
            panes, bg=Theme.CANVAS_BG, highlightthickness=1,
            highlightbackground=Theme.GREEN, cursor="fleur",
        )
        src_cv.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        out_cv = tk.Canvas(
            panes, bg=Theme.CANVAS_BG, highlightthickness=1,
            highlightbackground=Theme.BORDER, cursor="arrow",
        )
        out_cv.grid(row=1, column=1, sticky="nsew", padx=(4, 0))

        ctrl = tk.Frame(dlg, bg=Theme.BG_PANEL)
        ctrl.pack(fill=tk.X, padx=10, pady=4)
        ctrl2 = tk.Frame(dlg, bg=Theme.BG_PANEL)
        ctrl2.pack(fill=tk.X, padx=10, pady=2)
        ctrl3 = tk.Frame(dlg, bg=Theme.BG_PANEL)
        ctrl3.pack(fill=tk.X, padx=10, pady=2)

        # Primary control = desired output WIDTH in pixels (height follows aspect via block)
        max_out_w = min(256, sw)
        min_out_w = 4
        out_w_var = tk.IntVar(value=min(max_out_w, max(min_out_w, default_out_w)))
        colors_var = tk.IntVar(value=16)
        # Internal block derived from width; kept for grid math
        st["block"] = max(1, sw // max(1, out_w_var.get()))

        def current_block() -> int:
            tw = max(min_out_w, min(max_out_w, int(out_w_var.get())))
            # block so output width ≈ tw: ow = (sw - ox) // b  ≈ tw
            ox = int(st["ox"])
            b = max(1, (sw - (ox % max(1, st["block"]))) // tw)
            # Prefer simple: b = sw // tw (phase still works)
            b = max(1, sw // tw)
            return min(128, b)

        def out_dims(b: int, ox: int, oy: int) -> Tuple[int, int]:
            b = max(1, b)
            ox, oy = ox % b, oy % b
            ow = max(1, (sw - ox) // b)
            oh = max(1, (sh - oy) // b)
            return ow, oh

        def pixelate() -> Image.Image:
            b = current_block()
            st["block"] = b
            ox, oy = int(st["ox"]) % b, int(st["oy"]) % b
            ow, oh = out_dims(b, ox, oy)
            crop = st["src_copy"].crop((ox, oy, ox + ow * b, oy + oh * b))
            small = crop.resize((ow, oh), Image.Resampling.BOX)
            mc = max(1, min(256, int(colors_var.get())))
            return PixelPainterApp._quantize_rgba(small, mc)

        def schedule_refresh(_event=None) -> None:
            # Debounce Configure storms (was causing RecursionError)
            job = st.get("refresh_job")
            if job is not None:
                try:
                    dlg.after_cancel(job)
                except Exception:
                    pass
            st["refresh_job"] = dlg.after(40, refresh)

        def refresh() -> None:
            if st.get("refreshing"):
                return
            st["refreshing"] = True
            st["refresh_job"] = None
            try:
                b = current_block()
                st["block"] = b
                st["ox"] = int(st["ox"]) % b
                st["oy"] = int(st["oy"]) % b
                try:
                    mc = max(1, min(256, int(colors_var.get())))
                    colors_var.set(mc)
                except Exception:
                    mc = 16
                    colors_var.set(16)

                ow, oh = out_dims(b, st["ox"], st["oy"])
                size_banner.configure(text=f"Output: {ow} × {oh} pixels")

                # --- LEFT: source + grid (safe resize via RGB copy) ---
                src_cv.update_idletasks()
                cw = max(120, int(src_cv.winfo_width() or 400))
                ch = max(120, int(src_cv.winfo_height() or 360))
                if cw < 20 or ch < 20:
                    return
                vs = min(cw / sw, ch / sh)
                vs = max(0.05, min(vs, 8.0))
                st["view_scale"] = vs
                dw, dh = max(1, int(sw * vs)), max(1, int(sh * vs))
                # Avoid Pillow RGBA premultiply path quirks: resize RGB + paste alpha
                base = st["src_copy"]
                rgb = base.convert("RGB").resize((dw, dh), Image.Resampling.BILINEAR)
                alpha = base.split()[3].resize((dw, dh), Image.Resampling.BILINEAR)
                disp = rgb.convert("RGBA")
                disp.putalpha(alpha)
                draw = ImageDraw.Draw(disp)
                step = max(1.0, b * vs)
                off_x = (st["ox"] % b) * vs
                off_y = (st["oy"] % b) * vs
                x = off_x
                while x < dw + 1:
                    xi = int(round(x))
                    draw.line([(xi, 0), (xi, dh - 1)], fill=(92, 184, 92), width=1)
                    x += step
                y = off_y
                while y < dh + 1:
                    yi = int(round(y))
                    draw.line([(0, yi), (dw - 1, yi)], fill=(92, 184, 92), width=1)
                    y += step
                oxi, oyi = int(round(off_x)), int(round(off_y))
                draw.line([(oxi - 6, oyi), (oxi + 6, oyi)], fill=(200, 230, 200), width=2)
                draw.line([(oxi, oyi - 6), (oxi, oyi + 6)], fill=(200, 230, 200), width=2)

                st["photo_src"] = ImageTk.PhotoImage(disp)
                src_cv.delete("all")
                src_cv.create_image(cw // 2, ch // 2, image=st["photo_src"], anchor=tk.CENTER)
                src_cv.create_text(
                    8, 8, anchor=tk.NW, fill="#c8c8c8",
                    text="DRAG green grid to align",
                    font=("Segoe UI", 9),
                )

                # --- RIGHT: pixelated result ---
                small = pixelate()
                st["preview_img"] = small
                ow, oh = small.size
                out_cv.update_idletasks()
                ocw = max(120, int(out_cv.winfo_width() or 400))
                och = max(120, int(out_cv.winfo_height() or 360))
                oscale = min(ocw / max(1, ow), och / max(1, oh), 24)
                oscale = max(1, int(oscale))
                big = small.resize((ow * oscale, oh * oscale), Image.Resampling.NEAREST)
                if oscale >= 3:
                    d2 = ImageDraw.Draw(big)
                    for gx in range(0, big.width + 1, oscale):
                        d2.line([(gx, 0), (gx, big.height - 1)], fill=(60, 60, 60))
                    for gy in range(0, big.height + 1, oscale):
                        d2.line([(0, gy), (big.width - 1, gy)], fill=(60, 60, 60))
                st["photo_out"] = ImageTk.PhotoImage(big)
                out_cv.delete("all")
                out_cv.create_image(ocw // 2, och // 2, image=st["photo_out"], anchor=tk.CENTER)
                out_cv.create_text(
                    8, 8, anchor=tk.NW, fill="#5cb85c",
                    text=f"{ow} × {oh} px",
                    font=("Segoe UI", 11, "bold"),
                )

                uniq = set()
                spx = small.load()
                for yy in range(oh):
                    for xx in range(ow):
                        r, g, b, a = spx[xx, yy]
                        if a >= 128:
                            uniq.add((r, g, b))
                warn = ""
                if ow > 256 or oh > 256:
                    warn = "  ·  TOO BIG — lower Output width"
                info.configure(
                    text=(
                        f"Source {sw}×{sh}  ·  sample step {b}px  ·  "
                        f"grid shift ({st['ox']},{st['oy']})  ·  "
                        f"colors ≤{mc} (using {len(uniq)}){warn}"
                    )
                )
            except Exception as ex:
                info.configure(text=f"Preview error: {ex}")
            finally:
                st["refreshing"] = False

        def on_width_change(_=None) -> None:
            try:
                tw = max(min_out_w, min(max_out_w, int(out_w_var.get())))
            except Exception:
                tw = default_out_w
            out_w_var.set(tw)
            b = max(1, sw // tw)
            st["block"] = b
            st["ox"] %= b
            st["oy"] %= b
            schedule_refresh()

        self._label(ctrl, "Output width (pixels)", bg=Theme.BG_PANEL).pack(side=tk.LEFT)
        tk.Scale(
            ctrl, from_=min_out_w, to=max_out_w, orient=tk.HORIZONTAL, variable=out_w_var,
            command=on_width_change, bg=Theme.BG_PANEL, fg=Theme.FG,
            troughcolor=Theme.BG_INPUT, highlightthickness=0,
            activebackground=Theme.GREEN, length=360, showvalue=True,
        ).pack(side=tk.LEFT, padx=8)
        self._label(
            ctrl, "← sets how many pixels wide the result is",
            bg=Theme.BG_PANEL, fg=Theme.FG_DIM,
        ).pack(side=tk.LEFT)

        self._label(ctrl2, "Max colors", bg=Theme.BG_PANEL).pack(side=tk.LEFT)
        tk.Scale(
            ctrl2, from_=1, to=256, orient=tk.HORIZONTAL, variable=colors_var,
            command=lambda _=None: schedule_refresh(), bg=Theme.BG_PANEL, fg=Theme.FG,
            troughcolor=Theme.BG_INPUT, highlightthickness=0,
            activebackground=Theme.GREEN, length=320, showvalue=True,
        ).pack(side=tk.LEFT, padx=8)

        self._label(ctrl3, "Shift grid:", bg=Theme.BG_PANEL, fg=Theme.GREEN).pack(side=tk.LEFT)
        def nudge(dx: int, dy: int) -> None:
            b = max(1, sw // max(1, int(out_w_var.get())))
            st["ox"] = (st["ox"] + dx) % b
            st["oy"] = (st["oy"] + dy) % b
            schedule_refresh()

        for lab, dx, dy in [
            ("←1", -1, 0), ("→1", 1, 0), ("↑1", 0, -1), ("↓1", 0, 1),
            ("←4", -4, 0), ("→4", 4, 0), ("↑4", 0, -4), ("↓4", 0, 4),
        ]:
            bb = tk.Button(ctrl3, text=lab, command=lambda a=dx, c=dy: nudge(a, c), width=4)
            self._style_btn(bb)
            bb.pack(side=tk.LEFT, padx=1)

        def on_press(e) -> None:
            st["drag"] = (e.x, e.y, st["ox"], st["oy"])

        def on_drag(e) -> None:
            if not st["drag"]:
                return
            x0, y0, ox0, oy0 = st["drag"]
            b = max(1, sw // max(1, int(out_w_var.get())))
            vs = max(0.05, st["view_scale"])
            dx = int(round((e.x - x0) / vs))
            dy = int(round((e.y - y0) / vs))
            st["ox"] = (ox0 + dx) % b
            st["oy"] = (oy0 + dy) % b
            schedule_refresh()

        def on_release(_e=None) -> None:
            st["drag"] = None

        src_cv.bind("<ButtonPress-1>", on_press)
        src_cv.bind("<B1-Motion>", on_drag)
        src_cv.bind("<ButtonRelease-1>", on_release)
        src_cv.bind("<Configure>", schedule_refresh)
        out_cv.bind("<Configure>", schedule_refresh)

        btn_row = tk.Frame(dlg, bg=Theme.BG_PANEL)
        btn_row.pack(fill=tk.X, padx=10, pady=(4, 10))

        def apply() -> None:
            small = pixelate()
            ow, oh = small.size
            if ow > 256 or oh > 256:
                messagebox.showerror(
                    APP_NAME,
                    f"Result is {ow}×{oh}. Max canvas is 256×256 — lower Output width.",
                    parent=dlg,
                )
                return
            if not self._confirm_discard():
                return
            try:
                mc = max(1, min(256, int(colors_var.get())))
                self.doc = self._rgba_image_to_doc(small, max_colors=mc, quantize=False)
                self.doc.path = None
                self.doc.dirty = True
                self.color_idx = min(1, len(self.doc.palette) - 1)
                self.palette_count.set(len(self.doc.palette))
                self.sel_cells = set()
                self.float_items = []
                self.moving = False
                self._hist_clear()
                add_recent(source_path)
                self._rebuild_palette_swatches()
                self._rebuild_layer_list()
                self._rebuild_recent_menu()
                self._refresh_title()
                self._redraw()
                dlg.destroy()
            except Exception as ex:
                messagebox.showerror(APP_NAME, str(ex), parent=dlg)

        b_apply = tk.Button(btn_row, text="Apply to canvas", command=apply)
        self._style_btn(b_apply, active=True)
        b_apply.pack(side=tk.LEFT, padx=4)
        b_cancel = tk.Button(btn_row, text="Cancel", command=dlg.destroy)
        self._style_btn(b_cancel)
        b_cancel.pack(side=tk.LEFT, padx=4)
        self._label(
            btn_row,
            "Drag LEFT pane (green grid) until edges look right, then Apply.",
            bg=Theme.BG_PANEL,
            fg=Theme.FG_DIM,
        ).pack(side=tk.RIGHT, padx=8)

        dlg.after(120, schedule_refresh)

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
            self._hist_push()
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
                "Project:  .ppix v2  (palette + layers + indices)\n"
                "Export PNG/C: composites visible layers\n\n"
                "Index 0 = transparent on PNG / 0x0000 in C\n"
                "Layers / Frames (right panel):\n"
                "  New blank · Clone active · rename double-click\n"
                "  ▲▼ stack order · 👁 visibility · paint = active only\n"
                "  Use clones for animation frames / side views.\n\n"
                "Import & pixelate (Ctrl+I): grid align + max colors\n"
                "  (color quantize fixed — no more black/purple mess)\n\n"
                "Keys: 1-4 brush  B/E/F/I  R box  L free  M move/place\n"
                "  Ctrl+Z undo  ·  Ctrl+Shift+Z redo (50 steps)\n"
                "  G grid  P pick  C wheel  Esc clear select  Space invert\n"
                "  Alt+drag pan  ·  Ctrl+/- zoom"
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
