"""
CAD file format detection and DWG header parsing.
"""
import struct


def detect_dwg_version(filepath: str) -> str | None:
    """Read DWG file header to detect AutoCAD version."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(6)
        # DWG files start with "AC" + version bytes
        if header[:2] != b"AC":
            return None
        versions = {
            b"AC1021": "AutoCAD 2007-2009",
            b"AC1024": "AutoCAD 2010-2012",
            b"AC1027": "AutoCAD 2013-2017",
            b"AC1032": "AutoCAD 2018-2026",
        }
        return versions.get(header, f"Unknown (sig: {header.hex()})")
    except Exception:
        return None
