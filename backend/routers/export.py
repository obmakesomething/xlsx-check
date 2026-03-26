"""Export endpoints for generating output files."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database.connection import get_db
from services.project_service import ProjectService
from services.component_service import ComponentService
from services.export_service import ExportService

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/bom/excel/{project_id}")
async def export_bom_excel(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export project BoM as Excel file."""
    project_svc = ProjectService(db)
    project = await project_svc.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

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
        for c in project.components
    ]

    excel_bytes = ExportService.export_bom_excel(components, project.name)

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{project.name}_BOM.xlsx"'},
    )


@router.get("/bom/csv/{project_id}")
async def export_bom_csv(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export project BoM as CSV file."""
    project_svc = ProjectService(db)
    project = await project_svc.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

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
        for c in project.components
    ]

    csv_text = ExportService.export_bom_csv(components)

    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{project.name}_BOM.csv"'},
    )


@router.get("/kicad/symbols/{project_id}")
async def export_kicad_symbols(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export project components as a KiCad symbol library."""
    project_svc = ProjectService(db)
    project = await project_svc.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    components = [
        {
            "ref_designator": c.ref_designator,
            "part_number": c.part_number,
            "description": c.description,
            "package": c.package,
            "lcsc_code": c.lcsc_code,
        }
        for c in project.components
    ]

    lib_name = project.name.replace(" ", "_").lower()
    kicad_content = ExportService.export_kicad_symbol_lib(components, lib_name)

    return Response(
        content=kicad_content.encode("utf-8"),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{lib_name}.kicad_sym"'},
    )


@router.get("/project/json/{project_id}")
async def export_project_json(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export full project data as JSON."""
    project_svc = ProjectService(db)
    project = await project_svc.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "spec": project.spec,
        "status": project.status,
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
                "properties": c.properties,
            }
            for c in project.components
        ],
    }

    json_text = ExportService.export_project_json(project_data)

    return Response(
        content=json_text.encode("utf-8"),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{project.name}_export.json"'},
    )
