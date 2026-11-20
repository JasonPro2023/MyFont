# MyFont

**MyFont** is a lightweight, offline desktop application written in Python that converts hand-drawn or raster character images into installable TrueType fonts.

Supported image formats include `.png`, `.jpg`, `.jpeg`, and `.bmp`.

## Features

- Character grid for `A-Z`, `a-z`, `0-9`, punctuation, and symbols
- Support for custom Unicode characters
- Batch import from a folder
- Automatic image-to-glyph contour tracing
- Proportional canvas scaling
- Automatic inner-hole and contour handling
- Export as a `.ttf` TrueType font
- Runs completely offline
- Available on Windows, macOS, and Linux

## Preparing Character Images

1. Create a square image, such as `500 x 500` pixels.
2. Use a solid, high-contrast background and foreground.
3. Keep every character centered consistently.
4. Place the characters on the same baseline.
5. Export every character as `.png`, `.jpg`, `.jpeg`, or `.bmp`.

The default baseline is **20% from the bottom**. Use this setting to provide room for descenders such as `g`, `j`, `p`, `q`, and `y`.

Enable **Proportional Canvas Scaling** when characters share the same canvas dimensions.

## Using the Application

### 1. Start the application

```bash
python main.py
```

### 2. Configure the font

Enter a font name and adjust:

- **Baseline (% from bottom)** - the reference point shared by the character images
- **Proportional Canvas Scaling** - preserves character proportions relative to the complete canvas

Use **Edit Font Metadata** to customize the font's unique identifier, full name,
version, and PostScript name. These fields are saved as name table IDs 3–6;
the PostScript name must use up to 63 ASCII letters, numbers, periods,
underscores, or hyphens. Reset to defaults to regenerate values from the font name.

### 3. Map character images

Use the character grid to assign an image to a character:

- Click a `+` button to select an image.
- Right-click a mapped character to remove it.
- Use **Clear All** to remove every mapping.
- Use **Add Custom Character** to add a Unicode character.

The default grid includes:

- Uppercase letters
- Lowercase letters
- Numbers
- Punctuation
- Common symbols

### 4. Batch import

Click **Batch Import Folder** and select a folder containing character images.

Supported filename formats include:

- `A.png`
- `a.png`
- `upper_A.png`
- `lower_a.png`
- `0041.png` for Unicode character `U+0041`, which is `A`
- `00F1.png` for Unicode character `U+00F1`, which is `ñ`

For example:

```text
characters/
├── upper_A.png
├── lower_a.png
├── 0042.png
├── 0030.png
└── 00F1.png
```

### 5. Generate the font

Click **Generate & Save .TTF Font**, enter or confirm a font name, and select an output location.

A mapped character is exported as a TrueType glyph. The app also generates a space glyph and a fallback glyph.

## Installation from Source

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/MyFont.git
cd MyFont
```

Replace the repository URL with the actual repository address.

### 2. Create a virtual environment

#### Windows

```powershell
python -m venv libs
libs\Scripts\activate
```

#### macOS and Linux

```bash
python3 -m venv libs
source libs/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run MyFont

```bash
python main.py
```

## Building a Standalone Application

PyInstaller is included in `requirements.txt`.

### Cross-platform build

Activate the virtual environment and run:

```bash
python build.py
```

The build script creates:

- Windows: `dist\MinimalFontGenerator.exe`
- macOS: `dist\MinimalFontGenerator.app`
- Linux: `dist\MinimalFontGenerator`

The Windows and Linux builds are single-file executables. The macOS build is an application bundle.

## Installing the Generated Font

### Windows

1. Double-click the `.ttf` file.
2. Select **Install**.

### macOS

1. Double-click the `.ttf` file.
2. Open it in Font Book.
3. Select **Install Font**.

### Linux

Copy the font into the local fonts directory:

```bash
mkdir -p ~/.local/share/fonts
cp MyHandwriting.ttf ~/.local/share/fonts/
fc-cache -f -v
```

## Project Structure

```text
MyFont/
├── main.py
├── build.py
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── image_tracer.py
│   └── font_compiler.py
└── libs/
```

- `main.py` - Tkinter interface and character mapping
- `build.py` - Cross-platform PyInstaller build automation
- `core/image_tracer.py` - OpenCV contour extraction and scaling
- `core/font_compiler.py` - FontTools TrueType font assembly
- `requirements.txt` - Python dependencies
- `libs/` - Optional local virtual environment directory

## Dependencies

- Pillow
- OpenCV
- NumPy
- FontTools
- PyInstaller
