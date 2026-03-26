"""파일 업로드 및 파싱 라우터."""

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import Component, Project
from database.schemas import ComponentOut

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="업로드할 EDA/BoM 파일"),
    project_id: Optional[int] = Query(None, description="연결할 프로젝트 ID"),
    db: AsyncSession = Depends(get_db),
):
    """EDA/BoM 파일을 업로드하고 자동으로 포맷을 감지하여 파싱합니다."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    # 프로젝트 존재 확인
    if project_id is not None:
        from sqlalchemy import select
        proj_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        if not proj_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    # 파일 읽기
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    # 포맷 감지
    try:
        from parsers.file_detector import FileDetector
        detected_format = FileDetector.detect(file.filename, contents)
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="파일 감지 모듈을 로드할 수 없습니다.",
        )

    if detected_format == "unknown":
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 파일 형식입니다: {file.filename}",
        )

    # 임시 파일 저장 후 파싱
    try:
        from parsers.file_detector import get_parser
        parser = get_parser(detected_format)
    except ImportError:
        parser = None

    if parser is None:
        return {
            "filename": file.filename,
            "format": detected_format,
            "parsed": False,
            "message": f"'{detected_format}' 포맷의 파서가 아직 구현되지 않았습니다.",
            "data": {},
        }

    # 임시 파일에 저장하여 파싱
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        if hasattr(parser, "parse_file"):
            parsed_data = parser.parse_file(tmp_path)
        elif hasattr(parser, "parse"):
            parsed_data = parser.parse(tmp_path)
        else:
            parsed_data = {"raw_size": len(contents)}
    except Exception as e:
        logger.error("파일 파싱 실패: %s", e, exc_info=True)
        raise HTTPException(
            status_code=422,
            detail=f"파일 파싱 중 오류가 발생했습니다: {str(e)}",
        )
    finally:
        os.unlink(tmp_path)

    # 프로젝트에 부품 자동 저장 (BOM 파싱 결과인 경우)
    saved_count = 0
    if project_id is not None and detected_format in ("bom_excel", "bom_csv"):
        components_data = parsed_data.get("components", [])
        if isinstance(components_data, list):
            for comp_dict in components_data:
                if isinstance(comp_dict, dict):
                    component = Component(
                        project_id=project_id,
                        ref_designator=comp_dict.get("ref_designator", ""),
                        part_number=comp_dict.get("part_number", ""),
                        manufacturer=comp_dict.get("manufacturer", ""),
                        description=comp_dict.get("description", ""),
                        package=comp_dict.get("package", ""),
                        quantity=comp_dict.get("quantity", 1),
                        unit_price=comp_dict.get("unit_price", 0.0),
                        lcsc_code=comp_dict.get("lcsc_code", ""),
                        category=comp_dict.get("category", ""),
                        properties=comp_dict.get("properties", {}),
                    )
                    db.add(component)
                    saved_count += 1
            if saved_count > 0:
                await db.flush()

    return {
        "filename": file.filename,
        "format": detected_format,
        "parsed": True,
        "data": parsed_data,
        "saved_components": saved_count,
        "project_id": project_id,
    }


@router.post("/bom")
async def parse_bom(
    file: UploadFile = File(..., description="BoM 파일 (Excel/CSV)"),
    project_id: Optional[int] = Query(None, description="연결할 프로젝트 ID"),
    db: AsyncSession = Depends(get_db),
):
    """BoM 파일(Excel/CSV)을 업로드하고 파싱합니다."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(
            status_code=415,
            detail="지원하지 않는 BoM 형식입니다. .xlsx, .xls, .csv 파일만 지원합니다.",
        )

    # 프로젝트 존재 확인
    if project_id is not None:
        from sqlalchemy import select
        proj_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        if not proj_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    # 파서 로드
    try:
        from parsers.file_detector import get_parser
        fmt = "bom_excel" if ext in (".xlsx", ".xls") else "bom_csv"
        parser = get_parser(fmt)
    except ImportError:
        parser = None

    if parser is None:
        raise HTTPException(
            status_code=501,
            detail="BoM 파서 모듈이 아직 구현되지 않았습니다.",
        )

    suffix = ext
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        if hasattr(parser, "parse_file"):
            parsed_data = parser.parse_file(tmp_path)
        elif hasattr(parser, "parse"):
            parsed_data = parser.parse(tmp_path)
        else:
            raise HTTPException(status_code=501, detail="BoM 파서에 parse 메서드가 없습니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("BoM 파싱 실패: %s", e, exc_info=True)
        raise HTTPException(
            status_code=422,
            detail=f"BoM 파싱 중 오류가 발생했습니다: {str(e)}",
        )
    finally:
        os.unlink(tmp_path)

    # 프로젝트에 부품 저장
    saved_count = 0
    if project_id is not None:
        components_data = parsed_data.get("components", [])
        if isinstance(components_data, list):
            for comp_dict in components_data:
                if isinstance(comp_dict, dict):
                    component = Component(
                        project_id=project_id,
                        ref_designator=comp_dict.get("ref_designator", ""),
                        part_number=comp_dict.get("part_number", ""),
                        manufacturer=comp_dict.get("manufacturer", ""),
                        description=comp_dict.get("description", ""),
                        package=comp_dict.get("package", ""),
                        quantity=comp_dict.get("quantity", 1),
                        unit_price=comp_dict.get("unit_price", 0.0),
                        lcsc_code=comp_dict.get("lcsc_code", ""),
                        category=comp_dict.get("category", ""),
                        properties=comp_dict.get("properties", {}),
                    )
                    db.add(component)
                    saved_count += 1
            if saved_count > 0:
                await db.flush()

    return {
        "filename": file.filename,
        "format": fmt,
        "parsed": True,
        "data": parsed_data,
        "saved_components": saved_count,
        "project_id": project_id,
    }


@router.get("/formats")
async def list_supported_formats():
    """지원하는 파일 형식 목록을 반환합니다."""
    try:
        from parsers.file_detector import list_supported_formats
        formats = list_supported_formats()
    except ImportError:
        # 파일 감지 모듈 없이 하드코딩 폴백
        formats = [
            {"format": "kicad_sch", "description": "KiCad Schematic (.kicad_sch)"},
            {"format": "kicad_pcb", "description": "KiCad PCB Layout (.kicad_pcb)"},
            {"format": "altium_sch", "description": "Altium Schematic (.SchDoc)"},
            {"format": "altium_pcb", "description": "Altium PCB (.PcbDoc)"},
            {"format": "eagle_sch", "description": "Eagle Schematic (.sch)"},
            {"format": "eagle_brd", "description": "Eagle Board (.brd)"},
            {"format": "easyeda", "description": "EasyEDA JSON Project (.json)"},
            {"format": "gerber", "description": "Gerber RS-274X (.gbr, .gtl, .gbl, etc.)"},
            {"format": "bom_excel", "description": "BoM Excel (.xlsx, .xls)"},
            {"format": "bom_csv", "description": "BoM CSV (.csv)"},
            {"format": "pdf", "description": "PDF Document (.pdf)"},
        ]

    return {"formats": formats, "total": len(formats)}
