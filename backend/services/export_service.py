"""
내보내기(Export) 서비스.

프로젝트 BOM Excel 파일 생성, 프로젝트 JSON 보고서 생성,
KiCad 심볼 라이브러리 생성 등을 처리한다.
openpyxl / pandas 를 사용하여 Excel 파일을 생성한다.
"""

from __future__ import annotations
import io
import json
import logging
import pathlib
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database.models import Project, Component, CircuitBlock, DesignHistory

logger = logging.getLogger(__name__)

# 내보내기 디렉토리
_EXPORT_DIR = pathlib.Path(getattr(settings, "EXPORT_DIR", "./exports"))


class ExportService:
    """Generate export files from project data."""

    @staticmethod
    def export_bom_excel(components: list[dict[str, Any]], project_name: str = "Project") -> bytes:
        """Export BoM as Excel file."""
        columns = [
            "ref_designator", "part_number", "manufacturer", "description",
            "package", "quantity", "unit_price", "lcsc_code", "category",
        ]

        rows = []
        for comp in components:
            row = {col: comp.get(col, "") for col in columns}
            rows.append(row)

        df = pd.DataFrame(rows, columns=columns)

        # Rename to friendlier headers
        header_map = {
            "ref_designator": "Reference",
            "part_number": "Part Number",
            "manufacturer": "Manufacturer",
            "description": "Description",
            "package": "Package",
            "quantity": "Qty",
            "unit_price": "Unit Price ($)",
            "lcsc_code": "LCSC Code",
            "category": "Category",
        }
        df = df.rename(columns=header_map)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="BOM", index=False)

            # Auto-adjust column widths
            ws = writer.sheets["BOM"]
            for i, col in enumerate(df.columns, 1):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                ws.column_dimensions[chr(64 + i) if i <= 26 else "A"].width = min(max_len, 50)

        return buffer.getvalue()

    @staticmethod
    def export_bom_csv(components: list[dict[str, Any]]) -> str:
        """Export BoM as CSV string."""
        columns = [
            "ref_designator", "part_number", "manufacturer", "description",
            "package", "quantity", "unit_price", "lcsc_code", "category",
        ]

        rows = []
        for comp in components:
            row = {col: comp.get(col, "") for col in columns}
            rows.append(row)

        df = pd.DataFrame(rows, columns=columns)
        return df.to_csv(index=False)

    @staticmethod
    def export_kicad_symbol_lib(components: list[dict[str, Any]], lib_name: str = "project") -> str:
        """Generate a basic KiCad symbol library file (.kicad_sym) from component list."""
        lines = [
            f'(kicad_symbol_lib (version 20211014) (generator led_copilot)',
        ]

        for comp in components:
            ref = comp.get("ref_designator", "U?")
            value = comp.get("part_number", comp.get("description", "Unknown"))
            prefix = ref.rstrip("0123456789") if ref else "U"

            symbol_name = f"{lib_name}:{value}".replace(" ", "_")
            lines.append(f'  (symbol "{symbol_name}" (in_bom yes) (on_board yes)')
            lines.append(f'    (property "Reference" "{prefix}" (at 0 1.27 0)')
            lines.append(f'      (effects (font (size 1.27 1.27))))')
            lines.append(f'    (property "Value" "{value}" (at 0 -1.27 0)')
            lines.append(f'      (effects (font (size 1.27 1.27))))')
            lines.append(f'    (property "Footprint" "{comp.get("package", "")}" (at 0 -3.81 0)')
            lines.append(f'      (effects (font (size 1.27 1.27)) hide))')
            lines.append(f'    (property "Datasheet" "" (at 0 0 0)')
            lines.append(f'      (effects (font (size 1.27 1.27)) hide))')
            lines.append(f'    (property "LCSC" "{comp.get("lcsc_code", "")}" (at 0 0 0)')
            lines.append(f'      (effects (font (size 1.27 1.27)) hide))')
            lines.append(f'    (symbol "{symbol_name}_0_1"')
            lines.append(f'      (rectangle (start -2.54 2.54) (end 2.54 -2.54)')
            lines.append(f'        (stroke (width 0) (type default))')
            lines.append(f'        (fill (type background))))')
            lines.append(f'  )')

        lines.append(")")
        return "\n".join(lines)

    @staticmethod
    def export_project_json(project: dict[str, Any]) -> str:
        """Export full project data as JSON."""
        return json.dumps(project, ensure_ascii=False, indent=2, default=str)

    # ------------------------------------------------------------------
    # DB 연동 내보내기 (project_id 기반)
    # ------------------------------------------------------------------

    @classmethod
    async def export_bom_excel_from_db(
        cls,
        db: AsyncSession,
        project_id: int,
    ) -> Optional[io.BytesIO]:
        """
        프로젝트 ID 로 DB 에서 부품을 조회하여 BOM Excel 을 생성한다.

        Returns
        -------
        io.BytesIO | None  프로젝트가 없으면 None
        """
        stmt = (
            select(Project)
            .options(selectinload(Project.components))
            .where(Project.id == project_id)
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if project is None:
            logger.warning("BOM 내보내기 실패 - 프로젝트 미존재: id=%s", project_id)
            return None

        # ORM 객체 → dict 변환
        components = [
            {
                "ref_designator": c.ref_designator,
                "part_number": c.part_number,
                "manufacturer": c.manufacturer,
                "description": c.description,
                "package": c.package,
                "quantity": c.quantity,
                "unit_price": c.unit_price,
                "lcsc_code": c.lcsc_code,
                "category": c.category,
            }
            for c in sorted(project.components, key=lambda x: x.ref_designator or "")
        ]

        excel_bytes = cls.export_bom_excel(components, project_name=project.name)

        output = io.BytesIO(excel_bytes)
        output.seek(0)
        logger.info("BOM Excel 생성 완료: project_id=%s, components=%d", project_id, len(components))
        return output

    @classmethod
    async def export_project_report_from_db(
        cls,
        db: AsyncSession,
        project_id: int,
    ) -> Optional[dict[str, Any]]:
        """
        프로젝트 ID 로 DB 에서 모든 데이터를 조회하여 JSON 보고서를 생성한다.

        Returns
        -------
        dict | None  프로젝트가 없으면 None
        """
        stmt = (
            select(Project)
            .options(
                selectinload(Project.components),
                selectinload(Project.circuit_blocks),
                selectinload(Project.design_history),
            )
            .where(Project.id == project_id)
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if project is None:
            logger.warning("보고서 내보내기 실패 - 프로젝트 미존재: id=%s", project_id)
            return None

        # BOM 비용 계산
        total_cost = sum(
            (c.unit_price or 0.0) * (c.quantity or 1)
            for c in project.components
        )

        # 카테고리별 부품 수 집계
        category_counts: dict[str, int] = {}
        for c in project.components:
            cat = c.category or "Uncategorized"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        report: dict[str, Any] = {
            "report_type": "project_full_report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "LED AI Copilot Export Service",

            # 프로젝트 기본 정보
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "spec": project.spec or {},
                "status": project.status,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            },

            # BOM 요약
            "bom_summary": {
                "total_components": len(project.components),
                "total_cost": round(total_cost, 4),
                "category_breakdown": category_counts,
            },

            # 부품 목록
            "components": [
                {
                    "ref_designator": c.ref_designator,
                    "part_number": c.part_number,
                    "manufacturer": c.manufacturer,
                    "description": c.description,
                    "package": c.package,
                    "quantity": c.quantity,
                    "unit_price": c.unit_price,
                    "lcsc_code": c.lcsc_code,
                    "category": c.category,
                    "properties": c.properties or {},
                }
                for c in sorted(project.components, key=lambda x: x.ref_designator or "")
            ],

            # 회로 블록
            "circuit_blocks": [
                {
                    "name": b.name,
                    "block_type": b.block_type,
                    "description": b.description,
                    "components": b.components or [],
                }
                for b in project.circuit_blocks
            ],

            # 설계 이력
            "design_history": [
                {
                    "action": h.action,
                    "details": h.details or {},
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in sorted(
                    project.design_history,
                    key=lambda x: x.created_at or datetime.min.replace(tzinfo=timezone.utc),
                )
            ],
        }

        logger.info("프로젝트 보고서 생성 완료: project_id=%s", project_id)
        return report


# ---------------------------------------------------------------------------
# 모듈 수준 편의 함수
# ---------------------------------------------------------------------------

async def export_bom_excel(db: AsyncSession, project_id: int) -> Optional[io.BytesIO]:
    """BOM Excel 내보내기 편의 함수 (project_id 기반)."""
    return await ExportService.export_bom_excel_from_db(db, project_id)


async def export_project_report(db: AsyncSession, project_id: int) -> Optional[dict[str, Any]]:
    """프로젝트 JSON 보고서 내보내기 편의 함수."""
    return await ExportService.export_project_report_from_db(db, project_id)
