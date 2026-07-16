"""
Projects API routes — /api/v1/projects/*
All endpoints require a valid JWT. Projects are scoped to the authenticated user.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aitester.api.dependencies import get_current_user, get_db
from aitester.core.exceptions import DatabaseError, RecordNotFoundError
from aitester.db.models.project import Project
from aitester.db.models.user import User
from aitester.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


# ─── Create Project ───────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    """Creates a project owned by the current user."""
    try:
        project = Project(
            name=project_in.name,
            description=project_in.description,
            owner_id=current_user.id,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
    except Exception as exc:
        await db.rollback()
        raise DatabaseError(f"Failed to create project: {exc}") from exc


# ─── List Projects ────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List all projects for the current user",
)
async def list_projects(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Project]:
    """Returns only projects owned by the authenticated user (row-level isolation)."""
    stmt = (
        select(Project)
        .where(Project.owner_id == current_user.id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ─── Get Project ──────────────────────────────────────────────────────────────

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a single project",
)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


# ─── Delete Project ───────────────────────────────────────────────────────────

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found.")
    await db.delete(project)
    await db.commit()


# ─── Upload OpenAPI Spec ──────────────────────────────────────────────────────

@router.post(
    "/{project_id}/upload-spec",
    response_model=ProjectResponse,
    summary="Upload an OpenAPI spec (YAML or JSON) to a project",
)
async def upload_spec(
    project_id: uuid.UUID,
    file: UploadFile = File(..., description="OpenAPI YAML or JSON file"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    """
    Parses the uploaded spec file and stores it as JSON in the project.
    Supports both YAML (.yaml/.yml) and JSON (.json) OpenAPI 3.x specs.
    """
    import json
    import yaml

    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found.")

    content = await file.read()
    filename = (file.filename or "").lower()

    try:
        if filename.endswith((".yaml", ".yml")):
            spec_dict = yaml.safe_load(content)
        else:
            spec_dict = json.loads(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse spec: {exc}",
        ) from exc

    project.openapi_spec = spec_dict
    await db.commit()
    await db.refresh(project)
    return project
