"""File upload and parsing endpoints."""

import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Any

from config import settings
from parsers.file_detector import FileDetector
from parsers.kicad_parser import KiCadParser
from parsers.altium_parser import AltiumParser
from parsers.easyeda_parser import EasyEDAParser
from parsers.eagle_parser import EagleParser
from parsers.gerber_parser import GerberParser
from parsers.bom_parser import BomParser
from parsers.pdf_parser import PdfParser

router = APIRouter(prefix="/api/parse", tags=["parsers"])

# Parser instances
kicad_parser = KiCadParser()
altium_parser = AltiumParser()
easyeda_parser = EasyEDAParser()
eagle_parser = EagleParser()
gerber_parser = GerberParser()
bom_parser = BomParser()
pdf_parser = PdfParser()


@router.post("/upload")
async def upload_and_parse(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload and auto-detect + parse an EDA file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # Detect format
    fmt = FileDetector.detect(file.filename, data)

    # Parse based on detected format
    result: dict[str, Any] = {"filename": file.filename, "detected_format": fmt, "size_bytes": len(data)}

    try:
        if fmt in ("kicad_sch", "kicad_schematic", "kicad_pcb"):
            text = data.decode("utf-8", errors="ignore")
            result["parsed"] = kicad_parser.parse(text, file.filename)

        elif fmt in ("altium_schematic", "altium_pcb", "altium_project", "ole2"):
            result["parsed"] = altium_parser.parse(data, file.filename)

        elif fmt == "easyeda_json":
            result["parsed"] = easyeda_parser.parse(data, file.filename)

        elif fmt in ("eagle_schematic", "eagle_board", "eagle_xml"):
            text = data.decode("utf-8", errors="ignore")
            result["parsed"] = eagle_parser.parse(text, file.filename)

        elif fmt in ("gerber", "gerber_drill"):
            text = data.decode("ascii", errors="ignore")
            result["parsed"] = gerber_parser.parse(text, file.filename)

        elif fmt in ("bom_csv", "bom_excel"):
            result["parsed"] = bom_parser.parse(data, file.filename)

        elif fmt == "pdf":
            result["parsed"] = pdf_parser.parse(data, file.filename)

        else:
            result["parsed"] = {"error": f"Unsupported format: {fmt}"}

    except Exception as e:
        result["parsed"] = {"error": str(e)}

    # Optionally save the file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(data)
    result["saved_path"] = save_path

    return result


@router.post("/bom")
async def upload_bom(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload and parse a BoM (Excel/CSV) file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    result = bom_parser.parse(data, file.filename)
    return result


@router.get("/formats")
async def list_supported_formats():
    """List all supported file formats."""
    return {
        "formats": FileDetector.supported_formats(),
        "total": len(FileDetector.supported_formats()),
    }
