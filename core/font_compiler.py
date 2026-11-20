from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from core.image_tracer import trace_image_to_contours


def default_font_metadata(family_name, style_name="Regular"):
    postscript_name = "".join(
        character
        for character in f"{family_name}-{style_name}"
        if character in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
    )[:63] or "CustomFont-Regular"
    return {
        "uniqueFontIdentifier": f"{postscript_name}; Version 1.0",
        "fullName": f"{family_name} {style_name}",
        "version": "Version 1.0",
        "psName": postscript_name,
    }


def compile_ttf(
    char_image_map,
    output_path,
    family_name="CustomFont",
    style_name="Regular",
    baseline_ratio=0.20,
    use_canvas_scale=True,
    space_width=320,
    font_metadata=None,
):
    """
    Compiles a dictionary of {character: image_path} into a .ttf file.
    """
    units_per_em = 1000
    ascender = int(units_per_em * (1.0 - baseline_ratio))
    descender = -int(units_per_em * baseline_ratio)

    fb = FontBuilder(units_per_em, isTTF=True)

    glyph_order = [".notdef", "space"]
    cmap = {32: "space"}
    glyphs = {}
    metrics = {
        ".notdef": (500, 50),
        "space": (space_width, 0),
    }

    # Draw a simple hollow box for .notdef (missing character glyph)
    notdef_pen = TTGlyphPen(None)
    notdef_pen.moveTo((50, 0))
    notdef_pen.lineTo((50, 700))
    notdef_pen.lineTo((450, 700))
    notdef_pen.lineTo((450, 0))
    notdef_pen.closePath()
    notdef_pen.moveTo((100, 50))
    notdef_pen.lineTo((400, 50))
    notdef_pen.lineTo((400, 650))
    notdef_pen.lineTo((100, 650))
    notdef_pen.closePath()
    glyphs[".notdef"] = notdef_pen.glyph()

    # Empty space glyph
    glyphs["space"] = TTGlyphPen(None).glyph()

    # Process mapped characters sorted by Unicode codepoint
    for char in sorted(char_image_map.keys(), key=ord):
        img_path = char_image_map[char]
        codepoint = ord(char)
        g_name = f"uni{codepoint:04X}"

        contours, adv_width, lsb = trace_image_to_contours(
            img_path,
            units_per_em=units_per_em,
            baseline_ratio=baseline_ratio,
            use_canvas_scale=use_canvas_scale,
        )

        pen = TTGlyphPen(None)
        for contour in contours:
            pen.moveTo(contour[0])
            for pt in contour[1:]:
                pen.lineTo(pt)
            pen.closePath()

        glyph_order.append(g_name)
        cmap[codepoint] = g_name
        glyphs[g_name] = pen.glyph()
        metrics[g_name] = (adv_width, lsb)

    # Assemble font tables
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascender, descent=descender)
    name_records = default_font_metadata(family_name, style_name)
    if font_metadata:
        name_records.update(font_metadata)

    required_records = ("uniqueFontIdentifier", "fullName", "version", "psName")
    for record in required_records:
        value = name_records[record]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{record} must not be empty.")

    postscript_name = name_records["psName"]
    allowed_postscript_characters = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
    )
    if len(postscript_name) > 63 or any(
        character not in allowed_postscript_characters
        for character in postscript_name
    ):
        raise ValueError(
            "PostScript name must be at most 63 characters and use only "
            "ASCII letters, numbers, periods, underscores, or hyphens."
        )

    fb.setupNameTable(
        {
            "familyName": family_name,
            "styleName": style_name,
            **name_records,
        }
    )
    fb.setupOS2(
        sTypoAscender=ascender,
        sTypoDescender=descender,
        usWinAscent=ascender,
        usWinDescent=abs(descender),
    )
    fb.setupPost()

    fb.save(output_path)
    return len(char_image_map)