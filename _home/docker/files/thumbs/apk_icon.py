"""Launcher icons from APK files, for gokapi-thumbs.

Reads the APK as a ZIP through a seekable reader (partial HTTP requests in the service),
so only the central directory, the manifest, resources.arsc, and the icon's own files are
fetched. Resolves the manifest's `android:icon` / `android:roundIcon` through
resources.arsc and draws it:

- a bitmap icon (PNG/WebP): the highest-density one;
- an adaptive icon: background and foreground layers (colors, bitmaps, VectorDrawables,
  insets, gradients) are written as one SVG, rendered with resvg, cropped to the 72 dp
  viewport, and masked to a rounded square.

No androguard: this file parses binary XML (AXML) and the resource table itself.
"""

from __future__ import annotations

import base64
import io
import math
import re
import struct
import subprocess
import zipfile
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw

RES_STRING_POOL = 0x0001
RES_TABLE = 0x0002
RES_XML = 0x0003
RES_XML_START_ELEMENT = 0x0102
RES_XML_END_ELEMENT = 0x0103
RES_XML_RESOURCE_MAP = 0x0180
RES_TABLE_PACKAGE = 0x0200
RES_TABLE_TYPE = 0x0201

TYPE_NULL = 0x00
TYPE_REFERENCE = 0x01
TYPE_ATTRIBUTE = 0x02
TYPE_STRING = 0x03
TYPE_FLOAT = 0x04
TYPE_DIMENSION = 0x05
TYPE_FRACTION = 0x06
TYPE_INT_DEC = 0x10
TYPE_INT_HEX = 0x11
TYPE_INT_BOOLEAN = 0x12
TYPE_FIRST_COLOR = 0x1C
TYPE_LAST_COLOR = 0x1F

ANDROID_NS = "http://schemas.android.com/apk/res/android"
# Attribute IDs for the names this module reads, for files whose attribute names were stripped.
ANDROID_ATTRS = {
    0x01010002: "icon", 0x0101052C: "roundIcon", 0x01010199: "drawable", 0x010101A5: "color",
    0x01010159: "width", 0x01010155: "height", 0x01010402: "viewportWidth", 0x01010403: "viewportHeight",
    0x01010404: "fillColor", 0x01010405: "pathData", 0x01010406: "strokeColor", 0x01010407: "strokeWidth",
    0x0101051E: "fillType", 0x0101040B: "strokeLineCap", 0x0101040C: "strokeLineJoin",
    0x01010326: "rotation", 0x010101B5: "pivotX", 0x010101B6: "pivotY", 0x01010324: "scaleX",
    0x01010325: "scaleY", 0x01010320: "translateX", 0x01010321: "translateY", 0x0101031F: "alpha",
    0x010104B5: "inset", 0x010101B7: "insetLeft", 0x010101B8: "insetRight", 0x010101B9: "insetTop",
    0x010101BA: "insetBottom", 0x0101019D: "startColor", 0x0101019E: "endColor",
    0x0101020B: "centerColor", 0x010101A1: "type", 0x010101A0: "gradientRadius",
    0x010101A2: "centerX", 0x010101A3: "centerY", 0x01010510: "startX", 0x01010511: "startY",
    0x01010512: "endX", 0x01010513: "endY", 0x01010514: "offset", 0x010101FE: "tileMode",
    0x010104CC: "fillAlpha", 0x010104CB: "strokeAlpha", 0x01010409: "trimPathStart", 0x0101040A: "trimPathEnd",
    0x01010110: "name",
}
DENSITY_ANY = 0xFFFE
DENSITY_NONE = 0xFFFF
MAX_DEPTH = 8


class IconError(Exception):
    pass


def _u8(b, o):
    return b[o]


def _u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def _u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


# String pools ------------------------------------------------------------------------------


def _string_pool(data: bytes, start: int) -> list[str]:
    header_size, size = _u16(data, start + 2), _u32(data, start + 4)
    count, flags, strings_start = _u32(data, start + 8), _u32(data, start + 16), _u32(data, start + 20)
    utf8 = bool(flags & 0x100)
    offsets = struct.unpack_from(f"<{count}I", data, start + header_size)
    base = start + strings_start
    out = []
    for off in offsets:
        p = base + off
        try:
            if utf8:
                n = data[p]
                p += 2 if n & 0x80 else 1
                n = data[p]
                if n & 0x80:
                    n = ((n & 0x7F) << 8) | data[p + 1]
                    p += 2
                else:
                    p += 1
                out.append(data[p:p + n].decode("utf-8", errors="replace"))
            else:
                n = _u16(data, p)
                p += 2
                if n & 0x8000:
                    n = ((n & 0x7FFF) << 16) | _u16(data, p)
                    p += 2
                out.append(data[p:p + n * 2].decode("utf-16-le", errors="replace"))
        except (IndexError, struct.error):
            out.append("")
    if start + size > len(data):
        raise IconError("string pool past the end")
    return out


# Typed values ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Value:
    type: int
    data: int
    string: str | None = None

    @property
    def is_color(self):
        return TYPE_FIRST_COLOR <= self.type <= TYPE_LAST_COLOR

    def number(self, default: float = 0.0) -> float:
        if self.type == TYPE_FLOAT:
            return struct.unpack("<f", struct.pack("<I", self.data))[0]
        if self.type in (TYPE_INT_DEC, TYPE_INT_HEX):
            return float(struct.unpack("<i", struct.pack("<I", self.data))[0])
        if self.type in (TYPE_DIMENSION, TYPE_FRACTION):
            return _complex(self.data)
        if self.type == TYPE_STRING and self.string is not None:
            try:
                return float(re.sub(r"[a-z%]+$", "", self.string.strip()))
            except ValueError:
                return default
        return default


def _complex(data: int) -> float:
    """Android's complexToFloat: a 24-bit signed mantissa scaled by one of four radixes."""
    mantissa = struct.unpack("<i", struct.pack("<I", data & 0xFFFFFF00))[0]
    radix = (data >> 4) & 0x3
    return mantissa * (1.0 / (1 << 8)) * (1.0, 1.0 / (1 << 7), 1.0 / (1 << 15), 1.0 / (1 << 23))[radix]


# Binary XML --------------------------------------------------------------------------------


@dataclass
class Element:
    name: str
    attrs: dict[str, Value]
    children: list["Element"] = field(default_factory=list)


def parse_axml(data: bytes) -> Element:
    if len(data) < 8 or _u16(data, 0) != RES_XML:
        raise IconError("not binary XML")
    strings: list[str] = []
    res_map: list[int] = []
    root = Element("#document", {})
    stack = [root]
    p = _u16(data, 2)
    end = min(len(data), _u32(data, 4))
    while p + 8 <= end:
        ctype, hsize, csize = _u16(data, p), _u16(data, p + 2), _u32(data, p + 4)
        if csize < 8:
            break
        if ctype == RES_STRING_POOL:
            strings = _string_pool(data, p)
        elif ctype == RES_XML_RESOURCE_MAP:
            res_map = list(struct.unpack_from(f"<{(csize - hsize) // 4}I", data, p + hsize))
        elif ctype == RES_XML_START_ELEMENT:
            ext = p + hsize
            name_idx = _u32(data, ext + 4)
            attr_start, attr_size, attr_count = _u16(data, ext + 8), _u16(data, ext + 10), _u16(data, ext + 12)
            attrs: dict[str, Value] = {}
            for i in range(attr_count):
                a = ext + attr_start + i * attr_size
                a_name, raw = _u32(data, a + 4), _u32(data, a + 8)
                vtype, vdata = data[a + 15], _u32(data, a + 16)
                name = strings[a_name] if a_name < len(strings) else ""
                if a_name < len(res_map) and res_map[a_name] in ANDROID_ATTRS:
                    name = ANDROID_ATTRS[res_map[a_name]]
                elif ":" in name:
                    name = name.split(":", 1)[1]
                raw_str = strings[raw] if raw != 0xFFFFFFFF and raw < len(strings) else None
                if vtype == TYPE_STRING and vdata < len(strings):
                    raw_str = strings[vdata]
                attrs[name] = Value(vtype, vdata, raw_str)
            element = Element(strings[name_idx] if name_idx < len(strings) else "", attrs)
            stack[-1].children.append(element)
            stack.append(element)
        elif ctype == RES_XML_END_ELEMENT:
            if len(stack) > 1:
                stack.pop()
        p += csize
    if not root.children:
        raise IconError("empty XML")
    return root.children[0]


def find(element: Element, name: str) -> Element | None:
    if element.name == name:
        return element
    for child in element.children:
        found = find(child, name)
        if found:
            return found
    return None


# Resource table ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    density: int
    sdk: int
    language: bytes
    night: bool
    other: bool  # any qualifier this module doesn't rank (screen size, orientation, ...)


@dataclass
class ResourceTable:
    strings: list[str]
    # (package, type, entry) -> [(config, value)]
    entries: dict[tuple[int, int, int], list[tuple[Config, Value]]]

    @staticmethod
    def parse(data: bytes) -> "ResourceTable":
        if _u16(data, 0) != RES_TABLE:
            raise IconError("not a resource table")
        table = ResourceTable([], {})
        p = _u16(data, 2)
        while p + 8 <= len(data):
            ctype, csize = _u16(data, p), _u32(data, p + 4)
            if csize < 8:
                break
            if ctype == RES_STRING_POOL and not table.strings:
                table.strings = _string_pool(data, p)
            elif ctype == RES_TABLE_PACKAGE:
                table._package(data, p, csize)
            p += csize
        return table

    def _package(self, data: bytes, start: int, size: int) -> None:
        package_id = _u32(data, start + 8)
        p = start + _u16(data, start + 2)
        end = start + size
        while p + 8 <= end:
            ctype, hsize, csize = _u16(data, p), _u16(data, p + 2), _u32(data, p + 4)
            if csize < 8:
                break
            if ctype == RES_TABLE_TYPE:
                self._type(data, p, hsize, csize, package_id)
            p += csize

    def _type(self, data: bytes, p: int, hsize: int, csize: int, package_id: int) -> None:
        type_id, flags = data[p + 8], data[p + 9]
        count, entries_start = _u32(data, p + 12), _u32(data, p + 16)
        cfg = p + 20
        cfg_size = _u32(data, cfg)

        def byte(o):
            return data[cfg + o] if o < cfg_size else 0

        def short(o):
            return _u16(data, cfg + o) if o + 2 <= cfg_size else 0

        language = bytes(data[cfg + 8:cfg + 10]) if cfg_size >= 10 else b"\0\0"
        night = (byte(33) & 0x30) == 0x20
        other = any((byte(12), byte(13), byte(16), byte(17), byte(18), short(20), short(22), byte(32) & 0x0F,
                     short(34), short(36), short(38), byte(33) & 0x0F)) or short(4) or short(6) or bytes(data[cfg + 10:cfg + 12]) != b"\0\0"
        config = Config(short(14), short(24), language, night, bool(other))
        offsets_at = p + hsize
        sparse, offset16 = bool(flags & 0x01), bool(flags & 0x02)
        if sparse:
            pairs = [(_u16(data, offsets_at + i * 4), _u16(data, offsets_at + i * 4 + 2) * 4) for i in range(count)]
        elif offset16:
            pairs = [(i, o * 4) for i in range(count) if (o := _u16(data, offsets_at + i * 2)) != 0xFFFF]
        else:
            pairs = [(i, o) for i in range(count) if (o := _u32(data, offsets_at + i * 4)) != 0xFFFFFFFF]
        base = p + entries_start
        for index, offset in pairs:
            e = base + offset
            if e + 8 > p + csize:
                continue
            esize, eflags = _u16(data, e), _u16(data, e + 2)
            if eflags & 0x08:  # compact entry: the type is in the high byte of the flags
                value = Value(eflags >> 8, _u32(data, e + 4))
            elif eflags & 0x01:  # complex (bag): styles, arrays; not used for icons
                continue
            else:
                v = e + esize
                value = Value(data[v + 3], _u32(data, v + 4))
            if value.type == TYPE_STRING and value.data < len(self.strings):
                value = Value(value.type, value.data, self.strings[value.data])
            self.entries.setdefault((package_id, type_id, index), []).append((config, value))

    def candidates(self, res_id: int) -> list[tuple[Config, Value]]:
        return self.entries.get(((res_id >> 24) & 0xFF, (res_id >> 16) & 0xFF, res_id & 0xFFFF), [])

    def best(self, res_id: int) -> list[Value]:
        """Values for [res_id], best first: default locale, day, then adaptive (anydpi)
        before the densest bitmap."""
        ranked = []
        for config, value in self.candidates(res_id):
            if config.language != b"\0\0" or config.other:
                continue
            density = config.density
            rank = (0 if config.night else 1,
                    2 if density == DENSITY_ANY else 1 if density not in (0, DENSITY_NONE) else 0,
                    density if density not in (DENSITY_ANY, DENSITY_NONE) else 0,
                    config.sdk)
            ranked.append((rank, value))
        if not ranked:
            ranked = [((0,), v) for _, v in self.candidates(res_id)]
        return [v for _, v in sorted(ranked, key=lambda r: r[0], reverse=True)]


# Drawing -----------------------------------------------------------------------------------


def _argb(value: int) -> tuple[str, float]:
    a, r, g, b = (value >> 24) & 0xFF, (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}", a / 255


def _color_value(v: Value) -> int:
    """A color Value's ARGB, filling in alpha for the #RGB and #RRGGBB types."""
    if v.type in (0x1D, 0x1F):  # TYPE_INT_COLOR_RGB8 / RGB4
        return 0xFF000000 | v.data
    return v.data


class IconRenderer:
    def __init__(self, apk: zipfile.ZipFile, table: ResourceTable):
        self.apk = apk
        self.table = table
        self.names = set(apk.namelist())
        self._defs: list[str] = []
        self._ids = 0

    def _id(self) -> str:
        self._ids += 1
        return f"g{self._ids}"

    def read(self, path: str, limit: int = 8 * 1024 * 1024) -> bytes:
        if path not in self.names:
            raise IconError(f"{path} missing")
        info = self.apk.getinfo(path)
        if info.file_size > limit:
            raise IconError(f"{path} too large")
        return self.apk.read(path)

    # Resource resolution

    def resolve(self, value: Value, depth: int = 0) -> list[Value]:
        """Follows references to the concrete values a resource can take, best first."""
        if depth > MAX_DEPTH:
            return []
        if value.type == TYPE_REFERENCE:
            out = []
            for v in self.table.best(value.data):
                out.extend(self.resolve(v, depth + 1))
            return out
        return [value]

    def color(self, value: Value | None, depth: int = 0):
        """(svg paint, opacity) for a color attribute, or None. Paint may be a gradient url."""
        if value is None or depth > MAX_DEPTH:
            return None
        for v in self.resolve(value):
            if v.is_color:
                return _argb(_color_value(v))
            if v.type == TYPE_STRING and v.string:
                if v.string.startswith("#"):
                    return _argb(_parse_hex(v.string))
                if v.string.endswith(".xml"):
                    try:
                        element = parse_axml(self.read(v.string))
                    except IconError:
                        continue
                    paint = self._complex_color(element)
                    if paint:
                        return paint
        return None

    def _complex_color(self, element: Element):
        if element.name == "gradient":
            return self._gradient(element)
        if element.name == "selector":
            # A ColorStateList: its default item, the last one without states, or the first.
            for item in reversed(element.children):
                c = self.color(item.attrs.get("color"))
                if c:
                    alpha = item.attrs.get("alpha")
                    return (c[0], c[1] * (alpha.number(1.0) if alpha else 1.0))
        return None

    def _gradient(self, g: Element):
        a = g.attrs
        stops = []
        for item in g.children:
            if item.name == "item":
                c = self.color(item.attrs.get("color"))
                if c:
                    stops.append((item.attrs["offset"].number(0) if "offset" in item.attrs else 0, c))
        if not stops:
            for offset, key in ((0.0, "startColor"), (0.5, "centerColor"), (1.0, "endColor")):
                c = self.color(a.get(key))
                if c:
                    stops.append((offset, c))
        if not stops:
            return None
        kind = int(a["type"].number(0)) if "type" in a else 0
        gid = self._id()
        stop_xml = "".join(f'<stop offset="{o:.4f}" stop-color="{c}" stop-opacity="{op:.4f}"/>' for o, (c, op) in stops)
        if kind == 1:  # radial
            cx, cy = a["centerX"].number(0) if "centerX" in a else 0, a["centerY"].number(0) if "centerY" in a else 0
            r = a["gradientRadius"].number(1) if "gradientRadius" in a else 1
            self._defs.append(f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="{r}">{stop_xml}</radialGradient>')
        elif kind == 0:  # linear
            coords = [a[k].number(0) if k in a else 0 for k in ("startX", "startY", "endX", "endY")]
            self._defs.append('<linearGradient id="{}" gradientUnits="userSpaceOnUse" x1="{}" y1="{}" x2="{}" y2="{}">{}</linearGradient>'.format(gid, *coords, stop_xml))
        else:  # sweep: no SVG equivalent, use the first color
            return stops[0][1]
        return (f"url(#{gid})", 1.0)

    # Layers

    def layer(self, value: Value | None, depth: int = 0) -> str:
        """SVG content filling a 108 x 108 box for a drawable attribute."""
        if value is None or depth > MAX_DEPTH:
            return ""
        c = self.color(value) if value.type != TYPE_REFERENCE or not self._is_file(value) else None
        if c:
            return f'<rect width="108" height="108" fill="{c[0]}" fill-opacity="{c[1]:.4f}"/>'
        for v in self.resolve(value):
            if v.is_color:
                fill, opacity = _argb(_color_value(v))
                return f'<rect width="108" height="108" fill="{fill}" fill-opacity="{opacity:.4f}"/>'
            if v.type != TYPE_STRING or not v.string:
                continue
            path = v.string
            if path.endswith(".xml"):
                try:
                    return self.drawable(parse_axml(self.read(path)), depth + 1)
                except IconError:
                    continue
            if path.lower().endswith((".png", ".webp", ".jpg")):
                return self._bitmap(path)
        return ""

    def _is_file(self, value: Value) -> bool:
        return any(v.type == TYPE_STRING for v in self.resolve(value))

    def _bitmap(self, path: str) -> str:
        data = self.read(path)
        with Image.open(io.BytesIO(data)) as img:
            img.load()
            out = io.BytesIO()
            img.convert("RGBA").save(out, "PNG")
        uri = "data:image/png;base64," + base64.b64encode(out.getvalue()).decode()
        return f'<image width="108" height="108" preserveAspectRatio="none" href="{uri}"/>'

    def drawable(self, element: Element, depth: int) -> str:
        name = element.name
        if name == "vector":
            return self._vector(element)
        if name in ("inset",):
            a = element.attrs
            base = a["inset"].number(0) if "inset" in a else 0
            left, top, right, bottom = (a[k].number(base) if k in a else base for k in ("insetLeft", "insetTop", "insetRight", "insetBottom"))
            # Fractions are of the layer; dimensions are dp of the 108 dp layer.
            unit = 108 if "inset" in a and a["inset"].type == TYPE_FRACTION else 1
            left, top, right, bottom = left * unit, top * unit, right * unit, bottom * unit
            inner = self.layer(a.get("drawable"), depth + 1) or "".join(self.drawable(c, depth + 1) for c in element.children)
            w, h = max(0.0, 108 - left - right), max(0.0, 108 - top - bottom)
            return f'<svg x="{left}" y="{top}" width="{w}" height="{h}" viewBox="0 0 108 108" preserveAspectRatio="none">{inner}</svg>'
        if name == "layer-list":
            return "".join(self.layer(item.attrs.get("drawable"), depth + 1) or "".join(self.drawable(c, depth + 1) for c in item.children)
                           for item in element.children if item.name == "item")
        if name == "bitmap":
            src = element.attrs.get("src")
            return self.layer(src, depth + 1) if src else ""
        if name == "shape":
            fill = next((c for c in element.children if c.name == "solid"), None)
            c = self.color(fill.attrs.get("color")) if fill else None
            return f'<rect width="108" height="108" fill="{c[0]}" fill-opacity="{c[1]:.4f}"/>' if c else ""
        if name == "color":
            c = self.color(element.attrs.get("color"))
            return f'<rect width="108" height="108" fill="{c[0]}" fill-opacity="{c[1]:.4f}"/>' if c else ""
        return ""

    def _vector(self, v: Element) -> str:
        a = v.attrs
        vw = a["viewportWidth"].number(108) if "viewportWidth" in a else 108
        vh = a["viewportHeight"].number(108) if "viewportHeight" in a else 108
        body = "".join(self._vector_child(c) for c in v.children)
        alpha = a["alpha"].number(1) if "alpha" in a else 1
        return (f'<svg width="108" height="108" viewBox="0 0 {vw} {vh}" preserveAspectRatio="none">'
                f'<g opacity="{alpha:.4f}">{body}</g></svg>')

    def _vector_child(self, e: Element) -> str:
        a = e.attrs
        if e.name == "group":
            def n(key, default):
                return a[key].number(default) if key in a else default
            px, py = n("pivotX", 0), n("pivotY", 0)
            transform = (f'translate({n("translateX", 0) + px} {n("translateY", 0) + py}) rotate({n("rotation", 0)}) '
                         f'scale({n("scaleX", 1)} {n("scaleY", 1)}) translate({-px} {-py})')
            clip = ""
            inner = []
            for child in e.children:
                if child.name == "clip-path" and "pathData" in child.attrs:
                    cid = self._id()
                    self._defs.append(f'<clipPath id="{cid}"><path d="{escape(child.attrs["pathData"].string or "")}"/></clipPath>')
                    clip = cid
                else:
                    inner.append(self._vector_child(child))
            body = "".join(inner)
            if clip:
                body = f'<g clip-path="url(#{clip})">{body}</g>'
            return f'<g transform="{transform}">{body}</g>'
        if e.name == "clip-path":
            return ""
        if e.name != "path" or "pathData" not in a or not a["pathData"].string:
            return ""
        attrs = [f'd="{escape(a["pathData"].string, {chr(34): "&quot;"})}"']
        fill = self.color(a.get("fillColor"))
        fill_alpha = a["fillAlpha"].number(1) if "fillAlpha" in a else 1
        if fill:
            attrs.append(f'fill="{fill[0]}" fill-opacity="{fill[1] * fill_alpha:.4f}"')
        else:
            attrs.append('fill="none"')
        if "fillType" in a and int(a["fillType"].number(0)) == 1:
            attrs.append('fill-rule="evenodd"')
        stroke = self.color(a.get("strokeColor"))
        width = a["strokeWidth"].number(0) if "strokeWidth" in a else 0
        if stroke and width > 0:
            stroke_alpha = a["strokeAlpha"].number(1) if "strokeAlpha" in a else 1
            attrs.append(f'stroke="{stroke[0]}" stroke-opacity="{stroke[1] * stroke_alpha:.4f}" stroke-width="{width}"')
            caps = {0: "butt", 1: "round", 2: "square"}
            joins = {0: "miter", 1: "round", 2: "bevel"}
            if "strokeLineCap" in a:
                attrs.append(f'stroke-linecap="{caps.get(int(a["strokeLineCap"].number(0)), "butt")}"')
            if "strokeLineJoin" in a:
                attrs.append(f'stroke-linejoin="{joins.get(int(a["strokeLineJoin"].number(0)), "miter")}"')
        return f'<path {" ".join(attrs)}/>'

    def svg(self, background: str, foreground: str) -> str:
        defs = f"<defs>{''.join(self._defs)}</defs>" if self._defs else ""
        # The launcher shows the middle 72 dp of the 108 dp layers.
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="256" height="256" viewBox="18 18 72 72">{defs}{background}{foreground}</svg>')


def _parse_hex(text: str) -> int:
    h = text.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    value = int(h, 16)
    return value | 0xFF000000 if len(h) == 6 else value


def rounded_mask(img: Image.Image, radius: float = 0.24) -> Image.Image:
    size = img.size[0]
    scale = 4
    mask = Image.new("L", (size * scale, size * scale), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * scale - 1, size * scale - 1), radius=size * scale * radius, fill=255)
    mask = mask.resize(img.size, Image.Resampling.LANCZOS)
    out = img.convert("RGBA")
    alpha = Image.composite(out.getchannel("A"), Image.new("L", img.size, 0), mask)
    out.putalpha(alpha)
    return out


def render_svg(svg: str, size: int = 256, timeout: int = 30) -> Image.Image:
    result = subprocess.run(["resvg", "--width", str(size), "--height", str(size), "-", "-c"],
                            input=svg.encode(), capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0 or not result.stdout:
        raise IconError(f"resvg failed: {result.stderr[:200].decode(errors='replace')}")
    with Image.open(io.BytesIO(result.stdout)) as img:
        img.load()
        return img.convert("RGBA")


def apk_icon(fileobj) -> Image.Image | None:
    """The APK's launcher icon as a 256 px RGBA image, or None when it has none."""
    try:
        apk = zipfile.ZipFile(fileobj)
    except zipfile.BadZipFile:
        return None
    names = set(apk.namelist())
    if "AndroidManifest.xml" not in names or "resources.arsc" not in names:
        return None
    manifest = parse_axml(apk.read("AndroidManifest.xml"))
    application = find(manifest, "application")
    if application is None:
        return None
    table = ResourceTable.parse(apk.read("resources.arsc"))
    renderer = IconRenderer(apk, table)
    for key in ("icon", "roundIcon"):
        ref = application.attrs.get(key)
        if ref is None:
            continue
        for value in renderer.resolve(ref):
            if value.type != TYPE_STRING or not value.string:
                continue
            path = value.string
            try:
                if path.endswith(".xml"):
                    element = parse_axml(renderer.read(path))
                    if element.name in ("adaptive-icon",):
                        bg = next((c for c in element.children if c.name == "background"), None)
                        fg = next((c for c in element.children if c.name == "foreground"), None)

                        def content(layer):
                            if layer is None:
                                return ""
                            if "drawable" in layer.attrs:
                                return renderer.layer(layer.attrs["drawable"])
                            return "".join(renderer.drawable(c, 1) for c in layer.children)

                        svg = renderer.svg(content(bg), content(fg))
                        return rounded_mask(render_svg(svg))
                    # A plain drawable as the icon (a vector or a layer list), drawn full size.
                    body = renderer.drawable(element, 1)
                    if body:
                        svg = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                               f'width="256" height="256" viewBox="0 0 108 108">'
                               f'{"<defs>" + "".join(renderer._defs) + "</defs>" if renderer._defs else ""}{body}</svg>')
                        return render_svg(svg)
                elif path.lower().endswith((".png", ".webp", ".jpg")):
                    with Image.open(io.BytesIO(renderer.read(path))) as img:
                        img.load()
                        return img.convert("RGBA")
            except (IconError, OSError, struct.error, IndexError, KeyError, ValueError):
                continue
    return None
