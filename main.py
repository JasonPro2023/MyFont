import os
import string
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from core.font_compiler import compile_ttf, default_font_metadata

# Default character set displayed in the grid
DEFAULT_CHARS = (
    list(string.ascii_uppercase)
    + list(string.ascii_lowercase)
    + list(string.digits)
    + list(".,!?;:-_'\"()/@&#+=")
)


class FontMakerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minimal Font Generator")
        self.geometry("820x640")
        self.minsize(680, 500)

        # State: { 'A': '/path/to/A.png', ... }
        self.char_map = {}
        self.thumbnails = {}  # Keep references so Tkinter doesn't garbage-collect images
        self.slot_widgets = {}
        self.font_metadata_overrides = {}

        self._build_ui()

    def _build_ui(self):
        # --- Top Configuration Bar ---
        top_frame = ttk.Frame(self, padding=12)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Font Name:").grid(row=0, column=0, sticky=tk.W)
        self.font_name_var = tk.StringVar(value="MyHandwriting")
        ttk.Entry(top_frame, textvariable=self.font_name_var, width=20).grid(
            row=0, column=1, padx=(5, 15)
        )

        ttk.Label(top_frame, text="Baseline (% from bottom):").grid(
            row=0, column=2, sticky=tk.W
        )
        self.baseline_var = tk.IntVar(value=20)
        ttk.Spinbox(
            top_frame, from_=0, to=50, textvariable=self.baseline_var, width=5
        ).grid(row=0, column=3, padx=(5, 15))

        self.canvas_scale_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            top_frame,
            text="Proportional Canvas Scaling",
            variable=self.canvas_scale_var,
        ).grid(row=0, column=4, sticky=tk.W)

        # --- Action Toolbar ---
        action_frame = ttk.Frame(self, padding=(12, 0, 12, 10))
        action_frame.pack(fill=tk.X)

        ttk.Button(
            action_frame, text="Batch Import Folder...", command=self.batch_import
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            action_frame, text="Add Custom Character...", command=self.add_custom_char
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            action_frame, text="Clear All", command=self.clear_all
        ).pack(side=tk.LEFT)

        self.status_label = ttk.Label(action_frame, text="0 characters mapped")
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))

        # --- Scrollable Character Grid ---
        container = ttk.Frame(self, padding=(12, 0, 12, 0))
        container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            container, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.grid_frame = ttk.Frame(self.canvas)

        self.grid_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mousewheel scrolling
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        self.chars = list(DEFAULT_CHARS)
        self._populate_grid()

        # --- Bottom Export Bar ---
        bottom_frame = ttk.Frame(self, padding=12)
        bottom_frame.pack(fill=tk.X)

        export_btn = ttk.Button(
            bottom_frame,
            text="Generate & Save .TTF Font",
            command=self.export_font,
        )
        export_btn.pack(side=tk.RIGHT, ipadx=12, ipady=4)

        ttk.Button(
            bottom_frame,
            text="Edit Font Metadata...",
            command=self.edit_font_metadata,
        ).pack(side=tk.LEFT)

    def edit_font_metadata(self):
        family_name = self.font_name_var.get().strip() or "CustomFont"
        defaults = default_font_metadata(family_name)
        fields = (
            ("uniqueFontIdentifier", "Unique font identifier (Name ID 3):"),
            ("fullName", "Full name (Name ID 4):"),
            ("version", "Version (Name ID 5):"),
            ("psName", "PostScript name (Name ID 6):"),
        )

        dialog = tk.Toplevel(self)
        dialog.title("Font Metadata")
        dialog.transient(self)
        dialog.resizable(False, False)

        field_frame = ttk.Frame(dialog, padding=(12, 12, 12, 4))
        field_frame.pack(fill=tk.BOTH, expand=True)
        values = {}
        for row, (key, label) in enumerate(fields):
            ttk.Label(field_frame, text=label).grid(
                row=row, column=0, sticky=tk.W, padx=(0, 10), pady=4
            )
            value = tk.StringVar(
                value=self.font_metadata_overrides.get(key, defaults[key])
            )
            values[key] = value
            ttk.Entry(field_frame, textvariable=value, width=48).grid(
                row=row, column=1, sticky=tk.EW, pady=4
            )

        ttk.Label(
            field_frame,
            text="PostScript names allow up to 63 ASCII letters, numbers, ., _, or -.",
        ).grid(row=len(fields), column=0, columnspan=2, sticky=tk.W, pady=(4, 8))

        button_frame = ttk.Frame(dialog, padding=(12, 4, 12, 12))
        button_frame.pack(fill=tk.X)

        def reset_to_defaults():
            for key, value in values.items():
                value.set(defaults[key])

        def save_metadata():
            metadata = {key: value.get().strip() for key, value in values.items()}
            for key, value in metadata.items():
                if not value:
                    messagebox.showerror(
                        "Invalid Metadata",
                        f"{dict(fields)[key]} cannot be empty.",
                        parent=dialog,
                    )
                    return

            postscript_name = metadata["psName"]
            allowed_characters = (
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
            )
            if len(postscript_name) > 63 or any(
                character not in allowed_characters for character in postscript_name
            ):
                messagebox.showerror(
                    "Invalid PostScript Name",
                    "Use at most 63 ASCII letters, numbers, periods, underscores, "
                    "or hyphens.",
                    parent=dialog,
                )
                return

            self.font_metadata_overrides = {
                key: value
                for key, value in metadata.items()
                if value != defaults[key]
            }
            dialog.destroy()

        ttk.Button(
            button_frame, text="Reset to Defaults", command=reset_to_defaults
        ).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(
            side=tk.RIGHT, padx=(8, 0)
        )
        ttk.Button(button_frame, text="Save", command=save_metadata).pack(
            side=tk.RIGHT
        )

        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.grab_set()
        dialog.focus_set()

    def _populate_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.slot_widgets.clear()

        cols = 8
        for idx, char in enumerate(self.chars):
            r, c = divmod(idx, cols)
            card = ttk.Frame(self.grid_frame, relief=tk.RIDGE, borderwidth=1, padding=4)
            card.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

            lbl_char = ttk.Label(
                card, text=char, font=("Segoe UI", 11, "bold"), anchor="center"
            )
            lbl_char.pack(fill=tk.X)

            img_btn = tk.Button(
                card,
                text="+",
                width=7,
                height=3,
                bg="#f4f4f4",
                relief=tk.FLAT,
                command=lambda ch=char: self.select_image_for_char(ch),
            )
            img_btn.pack(pady=2)

            # Right-click to clear single slot
            img_btn.bind(
                "<Button-3>", lambda e, ch=char: self.clear_single_char(ch)
            )

            self.slot_widgets[char] = img_btn
            if char in self.char_map:
                self._update_slot_preview(char, self.char_map[char])

    def _update_slot_preview(self, char, path):
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((52, 52), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.thumbnails[char] = photo

            btn = self.slot_widgets[char]
            btn.config(image=photo, text="", width=56, height=56, bg="#e3f2fd")
        except Exception:
            pass

    def select_image_for_char(self, char):
        path = filedialog.askopenfilename(
            title=f"Select image for '{char}'",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")],
        )
        if path:
            self.char_map[char] = path
            self._update_slot_preview(char, path)
            self._update_status()

    def clear_single_char(self, char):
        if char in self.char_map:
            del self.char_map[char]
            self.thumbnails.pop(char, None)
            btn = self.slot_widgets[char]
            btn.config(image="", text="+", width=7, height=3, bg="#f4f4f4")
            self._update_status()

    def clear_all(self):
        self.char_map.clear()
        self.thumbnails.clear()
        self._populate_grid()
        self._update_status()

    def add_custom_char(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Character")
        dialog.geometry("260x110")
        dialog.resizable(False, False)

        ttk.Label(dialog, text="Enter single character (e.g. ñ, €, á):").pack(
            pady=(12, 4)
        )
        entry = ttk.Entry(dialog, width=10, justify="center", font=("Segoe UI", 12))
        entry.pack()
        entry.focus()

        def confirm():
            val = entry.get()
            if len(val) == 1 and val not in self.chars:
                self.chars.append(val)
                self._populate_grid()
            dialog.destroy()

        ttk.Button(dialog, text="Add", command=confirm).pack(pady=8)

    def batch_import(self):
        """
        Matches filenames inside a folder to characters:
        - Exact single character: 'A.png', 'a.png', '0.png'
        - Prefixed: 'upper_A.png', 'lower_a.png'
        - Hex Unicode: '0041.png' -> 'A'
        """
        folder = filedialog.askdirectory(title="Select Folder with Character Images")
        if not folder:
            return

        valid_exts = {".png", ".jpg", ".jpeg", ".bmp"}
        matched = 0

        for fname in os.listdir(folder):
            stem, ext = os.path.splitext(fname)
            if ext.lower() not in valid_exts:
                continue

            target_char = None
            if len(stem) == 1:
                target_char = stem
            elif stem.startswith(("upper_", "lower_")) and len(stem) == 7:
                target_char = stem[-1]
            elif len(stem) == 4:
                try:
                    target_char = chr(int(stem, 16))
                except ValueError:
                    pass

            if target_char:
                if target_char not in self.chars:
                    self.chars.append(target_char)
                self.char_map[target_char] = os.path.join(folder, fname)
                matched += 1

        self._populate_grid()
        self._update_status()
        messagebox.showinfo("Batch Import", f"Matched {matched} character images.")

    def _update_status(self):
        self.status_label.config(text=f"{len(self.char_map)} characters mapped")

    def export_font(self):
        if not self.char_map:
            messagebox.showwarning("No Glyphs", "Please map at least one character image first.")
            return

        font_name = self.font_name_var.get().strip() or "CustomFont"
        output_path = filedialog.asksaveasfilename(
            title="Save TrueType Font",
            defaultextension=".ttf",
            initialfile=f"{font_name}.ttf",
            filetypes=[("TrueType Font", "*.ttf")],
        )
        if not output_path:
            return

        try:
            count = compile_ttf(
                char_image_map=self.char_map,
                output_path=output_path,
                family_name=font_name,
                baseline_ratio=self.baseline_var.get() / 100.0,
                use_canvas_scale=self.canvas_scale_var.get(),
                font_metadata=self.font_metadata_overrides,
            )
            messagebox.showinfo(
                "Success",
                f"Exported '{os.path.basename(output_path)}' with {count} glyphs!",
            )
        except Exception as e:
            messagebox.showerror("Compilation Error", str(e))


if __name__ == "__main__":
    app = FontMakerApp()
    app.mainloop()