# PixelPainter

**PixelPainter** is a dark-mode pixel art editor for game assets (sprites, tiles, icons).  
Built for comfortable trackpad use, color-blind-friendly UI chrome, and a clean export path to PNG and embedded RGB565 C headers (ESP32 / M5GFX / similar).

| | |
|--|--|
| **Repo** | https://github.com/bootdsc/PixelPainter |
| **License** | [CC BY-NC-SA 4.0](LICENSE) — free to use, share, and modify **with attribution**; **not for sale** / commercial redistribution |
| **Default canvas** | **32×32** |
| **UI theme** | Dark gray / light gray / green only (no red/blue chrome) |
| **Portable app** | [Releases](https://github.com/bootdsc/PixelPainter/releases) → `PixelPainter.exe` |

---

## Quick start

### Windows portable EXE

Download from **[Releases](https://github.com/bootdsc/PixelPainter/releases)** (`PixelPainter.exe`).

Copy that single file anywhere. No Python install required.

### From source

```powershell
pip install -r requirements.txt
python pixel_painter.py
```

Requires **Python 3.10+** and **Pillow**.

---

## Features

### Drawing
- Tools: **Paint**, **Erase**, **Fill**, **Eyedrop** (on canvas)
- Brush sizes **1×1 … 4×4**
- **Space + drag** — erase while Paint is selected (trackpad-friendly; no right-click needed)
- Adjustable grid size (1–256 per side); default **32×32**

### Navigation (large grids)
- **Scrollbars** when the image is larger than the view
- **Alt + drag** (or middle-mouse drag) to **pan**
- **Ctrl + / Ctrl −** zoom (pixels per cell); **Ctrl+0** reset zoom

### Color
- **MS Paint–style** default palette + presets (grayscale, earth, complementary, warm/cool)
- **Palette slots**: set count; extras fill **white**
- **HSV color wheel** (drag) + brightness — key **C**
- **Screen pick → current palette slot** (no popup) — key **P**
- Canvas **background color** for empty cells (editor-only) — **View** menu

### Selection
- **Box** and **Free** select
- **Move selection** / **Place selection** (left panel)
  - Lift pixels, drag (even off-grid for alignment)
  - Place clips anything outside the canvas

### Files
- **`.ppix`** project (palette + indices) — Save / Save As / Recent
- **Export PNG** (integer scale, lossless; index 0 transparent)
- **Export C RGB565** `.h` for embedded firmware

---

## Keyboard map

| Key | Action |
|-----|--------|
| `1`–`4` | Brush size |
| `B` / `E` / `F` / `I` | Paint / Erase / Fill / Eyedrop |
| `R` / `L` | Box / Free select |
| `M` | Move / Place selection |
| `Space` (hold) | Invert paint↔erase while drawing |
| `Alt` + drag | Pan canvas |
| `Ctrl` + `+` / `-` | Zoom in / out |
| `Ctrl` + `0` | Reset zoom |
| `P` | Screen pick → palette slot |
| `C` | Color wheel |
| `G` | Toggle grid |
| `Esc` | Clear selection |
| `Ctrl+N` / `O` / `S` | New / Open / Save |

---

## Formats for games

| Format | Use |
|--------|-----|
| **`.ppix`** | Editable master (keep this) |
| **PNG ×1** | Lossless 1:1 pixels — share, git, intermediate |
| **C RGB565** | ESP32 / M5 / bare-metal blit arrays |

**Do not use JPEG** for pixel art.  
Index **0** = transparent on PNG / `0x0000` in C export.

---

## Project layout

```
pixel-painter/
  pixel_painter.py     # application source
  requirements.txt     # Pillow
  LICENSE              # CC BY-NC-SA 4.0
  README.md
  .gitignore
  dist/
    PixelPainter.exe   # portable Windows build
```

User settings/recent files live in `~/.pixel_painter/` (not in this repo).

---

## Rebuild the EXE (Windows)

```powershell
pip install pyinstaller pillow
python -m PyInstaller --noconfirm --onefile --windowed --name PixelPainter ^
  --distpath dist --workpath build --specpath . pixel_painter.py
```

Output: `dist/PixelPainter.exe`

---

## License (short)

**CC BY-NC-SA 4.0**

- ✅ Use, modify, share  
- ✅ Requires **attribution** (credit the project / author)  
- ✅ Derivatives under the **same license**  
- ❌ **No commercial use** (don’t sell the app or paid redistributions of it)

See [LICENSE](LICENSE) and https://creativecommons.org/licenses/by-nc-sa/4.0/

---

## Attribution example

If you ship a modified build or use substantial code:

> Includes work from **PixelPainter** by bootdsc, licensed under CC BY-NC-SA 4.0.

---

## Author

Created for personal game-dev tooling (Cardputer / ESP32 assets and general pixel work).  
Feedback and non-commercial forks welcome.
