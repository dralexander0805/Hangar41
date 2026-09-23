"""The starting point for the export process, the start of the addon.
Its purpose is to read strings and break them into chunks, filtering out
comments and deprecated OBJ directives.

It also gives prints errors to the logger
"""

import collections
import itertools
import math
import pathlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from pprint import pprint
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import bmesh
import bpy
from mathutils import Euler, Vector

from io_xplane2blender.importer.xplane_imp_cmd_builder import (
    ATTR_STATE_DIRECTIVES,
    VT,
    ImpCommandBuilder,
)
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_constants import (
    ANIM_TYPE_HIDE,
    ANIM_TYPE_SHOW,
    ANIM_TYPE_TRANSFORM,
)
from io_xplane2blender.xplane_helpers import (
    ExportableRoot,
    floatToStr,
    logger,
    vec_b_to_x,
    vec_x_to_b,
)


class UnrecoverableParserError(Exception):
    """Raised when the .obj can't be imported. str(e) is a user-facing message."""

    pass


def import_obj(filepath: Union[pathlib.Path, str]) -> str:
    """
    Attempts to import an OBJ, mutating the blender data of the current scene.
    The importer may
    - finish the whole import, returning "FINISHED"
    - stop early with partial results, returning "CANCELLED".
    - Raise an UnrecoverableParserError showing no results can be trusted
    """
    filepath = pathlib.Path(filepath)
    try:
        # utf-8-sig strips a BOM if present. Some tools write non-UTF-8 bytes
        # into comments; replace them rather than refusing the whole file.
        lines = filepath.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError as e:
        msg = f"Could not read '{filepath}': {e.strerror or e}"
        logger.error(msg)
        raise UnrecoverableParserError(msg) from e

    header = [line.strip() for line in lines[:3]]
    if not (header[:1] in (["A"], ["I"]) and header[1:3] == ["800", "OBJ"]):
        found = " / ".join(repr(line) for line in header) or "an empty file"
        msg = (
            f"'{filepath.name}' is not an X-Plane OBJ8 file. The first three lines"
            f" must be 'I' (or 'A'), '800', 'OBJ', but found {found}."
            " Wavefront .obj files from other 3D programs are a different format"
            " and can't be imported with this importer."
        )
        logger.error(msg)
        raise UnrecoverableParserError(msg)

    builder = ImpCommandBuilder(filepath)
    pattern = re.compile("([^#]*)(#.*)?")

    def dataref_at(components: List[str], i: int, lineno: int, directive: str) -> str:
        """X-Plane accepts an animation with no dataref (it never moves); so do we"""
        try:
            return components[i]
        except IndexError:
            logger.warn(
                f"Line {lineno}: {directive} has no dataref, imported as 'none'"
            )
            return "none"

    name_hint = ""
    skip = False
    # Everything before POINT_COUNTS is the header
    in_header = True
    unsupported: Dict[str, int] = collections.Counter()
    # start=4 so lineno matches what a text editor shows
    for lineno, line in enumerate(map(str.strip, lines[3:]), start=4):
        to_parse, comment = re.match(pattern, line).groups()[0:2]
        try:
            if comment.startswith("# name_hint:"):
                name_hint = comment[12:].strip()
            elif comment.startswith(("# 1", "# 2", "# 3", "# 4")):
                name_hint = comment[2:].strip()
        except AttributeError:
            pass

        if not to_parse:
            continue
        else:
            directive, *components = to_parse.split()

        if directive == "SKIP":
            skip = not skip
        if directive == "STOP":
            break

        if skip:
            continue

        if in_header and directive in {"VT", "IDX", "IDX10", "TRIS", "ANIM_begin", "LINES"}:
            in_header = False  # POINT_COUNTS was missing

        try:
            # TODO: Rewrite using giant switch-ish table and functions so it is more neat
            # Need scanf solution
            # scan_int, scan_float, scan_vec2, scan_vec3tobl, scan_str, scan_enum (where it scans a limited number of choices and has a mapping of strings for it)
            """
            def scan_int(s_itr:iter_of_enum, default=None, error_msg=None):
                s = ""
                try:
                    i, c = next(s_itr)
                except StopIteration:
                    return "expected, str, found end of line"
                while c in "-0123456789":
                    s += c
                    c = next(s_itr)
                try:
                    return int(s)
                except ValueError:
                    if default is not None:
                        return default

            def scan_float(s_itr:iter)
                pass
            """

            # if fails we can fallback to default value and print warning or just print a logger warning that it is skipping
            # itr = enumerate()
            # def scan_(last=False, msg_missing=f"Could not convert parameter {lineno} _true, default=None)->value:
            # Throws parser error if needed
            # def _try to swallow all exceptions if the only thing that should happen is the line getting ignored on bad data. Otherwise we can go into more crazy exception hanlding cases
            if directive in {"GLOBAL_cockpit", "GLOBAL_cockpit_lit"}:
                builder.is_cockpit = True
            elif directive in {"TEXTURE", "TEXTURE_LIT", "TEXTURE_NORMAL"}:
                # A bare "TEXTURE" means untextured; nothing to keep
                if components:
                    named, found = _find_texture(filepath, components[0], directive)
                    builder.set_texture(directive, named, found)
            elif directive == "POINT_COUNTS":
                in_header = False
            elif in_header and directive in HEADER_STATE:
                builder.set_header_state(directive, components)
            elif in_header and directive not in {"A", "I"}:
                # Header lines the exporter has no setting for (TEXTURE_MODULATOR,
                # decals, GLOBAL_luminance, ...) are carried through verbatim
                builder.custom_header.append((directive, " ".join(components)))
            elif directive == "VT":
                components[:3] = vec_x_to_b(list(map(float, components[:3])))
                components[3:6] = vec_x_to_b(list(map(float, components[3:6])))
                components[6:8] = list(map(float, components[6:8]))
                builder.build_cmd(directive, *components[:8])
            elif directive == "IDX":
                try:
                    idx = int(*components[:1])
                    if idx < -1:
                        raise ValueError(
                            f"IDX on line {lineno}'s is less than 0"
                        )  # Also, must be less than POINT_COUNTS reports?  # TODO yes?
                except ValueError:
                    logger.warn(
                        f"Line {lineno}: IDX value '{' '.join(components)}' isn't a"
                        " valid vertex index, skipped"
                    )
                except IndexError:
                    logger.warn(f"Line {lineno}: IDX has no value, skipped")
                else:
                    builder.build_cmd(directive, idx)
            elif directive == "IDX10":
                # idx error etc
                builder.build_cmd(directive, *map(int, components[:11]))
            elif directive == "TRIS":
                start_idx = int(components[0])
                count = int(components[1])
                builder.build_cmd(directive, start_idx, count, name_hint=name_hint)
                name_hint = ""

            elif directive == "ANIM_begin":
                builder.build_cmd("ANIM_begin", name_hint=name_hint)
            elif directive == "ANIM_end":
                builder.build_cmd("ANIM_end")
            elif directive == "ANIM_trans_begin":
                dataref_path = dataref_at(components, 0, lineno, directive)
                builder.build_cmd("ANIM_trans_begin", dataref_path, name_hint=name_hint)
            elif directive == "ANIM_trans_key":
                value = float(components[0])
                location = vec_x_to_b(list(map(float, components[1:4])))
                builder.build_cmd(directive, value, location)
            elif directive == "ANIM_trans_end":
                pass
            elif directive in {"ANIM_hide", "ANIM_show"}:
                v1, v2 = map(float, components[:2])
                dataref_path = dataref_at(components, 2, lineno, directive)
                builder.build_cmd(directive, v1, v2, dataref_path)
            elif directive == "ANIM_rotate_begin":
                axis = vec_x_to_b(list(map(float, components[0:3])))
                dataref_path = dataref_at(components, 3, lineno, directive)
                builder.build_cmd(directive, axis, dataref_path, name_hint=name_hint)
            elif directive == "ANIM_rotate_key":
                value = float(components[0])
                degrees = float(components[1])
                builder.build_cmd(directive, value, degrees)
            elif directive == "ANIM_rotate_end":
                builder.build_cmd(directive)
            elif directive == "ANIM_keyframe_loop":
                loop = float(components[0])
                builder.build_cmd(directive, loop)
            elif directive == "ANIM_trans":
                xyz1 = vec_x_to_b(list(map(float, components[:3])))
                xyz2 = vec_x_to_b(list(map(float, components[3:6])))
                v1, v2 = (0, 0)
                path = "none"

                try:
                    v1 = float(components[6])
                    v2 = float(components[7])
                    path = components[8]
                except IndexError as e:
                    pass
                builder.build_cmd(directive, xyz1, xyz2, v1, v2, path, name_hint=name_hint)
            elif directive == "ANIM_rotate":
                dxyz = vec_x_to_b(list(map(float, components[:3])))
                r1, r2 = map(float, components[3:5])
                v1, v2 = (0, 0)
                path = "none"

                try:
                    v1 = float(components[5])
                    v2 = float(components[6])
                    path = components[7]
                except IndexError:
                    pass
                builder.build_cmd(
                    directive, dxyz, r1, r2, v1, v2, path, name_hint=name_hint
                )
            elif directive.startswith("ATTR_manip_") or directive in {
                "ATTR_axis_detented",
                "ATTR_axis_detent_range",
            }:
                if directive != "ATTR_manip_none":
                    # Manipulators only work in a cockpit object, and the
                    # exporter only writes them for the Cockpit type. Many
                    # cockpit OBJs have no GLOBAL_cockpit_lit to tell us.
                    builder.is_cockpit = True
                builder.build_cmd(directive, components)
            elif directive in ATTR_STATE_DIRECTIVES:
                builder.build_cmd(directive, components)
            else:
                unsupported[directive] += 1
        except UnrecoverableParserError:
            raise
        except (IndexError, ValueError, TypeError) as e:
            detail = (
                "a value is missing" if isinstance(e, IndexError) else str(e) or type(e).__name__
            )
            msg = (
                f"Line {lineno} of '{filepath.name}': couldn't import {directive}"
                f" ({detail}). Line was: '{line}'"
            )
            logger.error(msg)
            raise UnrecoverableParserError(msg) from e

    if unsupported:
        logger.warn(
            "Not imported, so these will be missing from an export: "
            + ", ".join(f"{d} x{n}" for d, n in unsupported.most_common())
        )

    builder.finalize_intermediate_blocks()
    return "FINISHED"


# Header directives that set the starting attribute state, or map to an
# exporter setting, rather than being carried through verbatim
HEADER_STATE = {
    "NORMAL_METALNESS",
    "BLEND_GLASS",
    "COCKPIT_REGION",
    "GLOBAL_specular",
    "GLOBAL_no_blend",
    "GLOBAL_shadow_blend",
    "GLOBAL_no_shadow",
}


def _find_texture(
    obj_path: Path, name: str, directive: str
) -> Tuple[Path, Optional[Path]]:
    """
    Returns the texture path as the OBJ names it (what an export should write)
    and a file that exists for Blender to display, or None. X-Plane loads the
    .dds when the named .png is missing (and vice versa), so we do too.
    """
    named = (obj_path.parent / Path(name)).resolve()
    candidates = [named] + [
        named.with_suffix(ext) for ext in (".dds", ".png") if ext != named.suffix.lower()
    ]
    found = next((p for p in candidates if p.exists()), None)
    if found is None:
        logger.warn(
            f"{directive} '{named}' not found (also tried .dds/.png). The export"
            " keeps the path, but Blender can't show it. Paths are relative to"
            " the .obj's folder"
        )
    return named, found
