# PixelPainter

Created by **Bootdsc** for all you Chooms to use, copy, and modify.

Dark-mode pixel art editor for game assets (sprites, tiles, icons). Trackpad-friendly, color-blind-friendly UI chrome (dark gray / light gray / green only — no red or blue highlights), with export to PNG and embedded RGB565 C headers.

| | |
|--|--|
| **Author** | Bootdsc |
| **License** | [CC BY-NC-SA 4.0](LICENSE) |
| **Default canvas** | **32×32** |
| **Source** | `pixel_painter.py` |
| **Windows build** | [Releases](https://github.com/bootdsc/PixelPainter/releases) |

---

## Download

**[Latest release](https://github.com/bootdsc/PixelPainter/releases)** includes:

- `PixelPainter.exe` — portable Windows app (no install)
- `pixel_painter.py` — full source script

---

## Run from source

```bash
pip install -r requirements.txt
python pixel_painter.py
```

Requires Python 3.10+ and Pillow.

---

## Features

### Drawing
- Paint, Erase, Fill, Eyedrop (on canvas)
- Brush sizes 1×1 … 4×4
- **Space + drag** — erase while Paint is selected (trackpad-friendly)
- Grid size 1–256 per side (default **32×32**)
- **Import & pixelate** (`Ctrl+I`) — open any photo/sprite, **block-size slider**,
  **max-colors** decimation (median-cut, no dither), **click-drag** to shift the
  sample grid so edges line up, then Apply
- **Replace drawn color** — remap every pixel of palette index A → index B  
  (also: editing a swatch with the **Wheel** recolors all pixels using that slot)

### Navigation
- **Scrollbars** when the image is larger than the window
- **Alt + drag** or middle-mouse drag to **pan**
- **Ctrl + / −** zoom (pixels per cell); **Ctrl+0** reset

### Color
- MS Paint–style default palette + presets
- Palette slot count (extras fill white)
- HSV color wheel — key **C**
- Screen pick → current palette slot — key **P** (no popup)
- Canvas background for empty cells — **View** menu (editor-only)

### Selection
- Box and Free select
- Move / Place (left panel): lift, drag off-grid for alignment, place (clips outside)

### Files
- `.ppix` project (Save / Save As / Recent)
- Export PNG (integer scale; index 0 transparent)
- Export C RGB565 `.h` for embedded firmware

---

## Keyboard map

| Key | Action |
|-----|--------|
| `1`–`4` | Brush size |
| `B` / `E` / `F` / `I` | Paint / Erase / Fill / Eyedrop |
| `R` / `L` | Box / Free select |
| `M` | Move / Place selection |
| `Space` (hold) | Invert paint↔erase while drawing |
| `Alt` + drag | Pan |
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
| `.ppix` | Editable master |
| PNG ×1 | Lossless 1:1 pixels |
| C RGB565 | Embedded blit arrays |

Index **0** = transparent on PNG / `0x0000` in C.

---

## Project layout

```
PixelPainter/
  pixel_painter.py    # application source
  requirements.txt    # Pillow
  LICENSE             # CC BY-NC-SA 4.0
  README.md
  .gitignore
```

User settings and recent-file list live in the user’s home directory under `.pixel_painter/` (created at runtime; not part of the repo).

---

## Rebuild Windows EXE

From this directory:

```bash
pip install pyinstaller pillow
python -m PyInstaller --noconfirm --onefile --windowed --name PixelPainter \
  --distpath dist --workpath build --specpath . pixel_painter.py
```

Output: `dist/PixelPainter.exe`

---

## License

**CC BY-NC-SA 4.0**

- ✅ Use, copy, modify, share  
- ✅ Give **attribution** to Bootdsc / PixelPainter  
- ✅ Keep derivatives under the **same license**  
- ❌ **No commercial use** (do not sell the app or paid redistributions)

See [LICENSE](LICENSE) and https://creativecommons.org/licenses/by-nc-sa/4.0/

### Attribution example

> PixelPainter — created by Bootdsc for all you Chooms to use, copy, and modify.  
> Licensed under CC BY-NC-SA 4.0.
