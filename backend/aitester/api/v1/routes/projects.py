"""
Projects API routes — /api/v1/projects/*
All endpoints require a valid JWT. Projects are scoped to the authenticated user.
"""

from datetime import UTC, datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from aitester.api.dependencies import get_current_user
from aitester.db.models import Project, User
from aitester.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_owned_project(project_id: str, current_user: User) -> Project:
    try:
        project = await Project.get(PydanticObjectId(project_id))
    except Exception:
        project = None
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


# ─── Create ───────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
) -> Project:
    """Creates a project owned by the current user."""
    project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=current_user.id,
    )
    await project.insert()
    return project


# ─── List ─────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List all projects for the current user",
)
async def list_projects(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
) -> list[Project]:
    """Returns only projects owned by the authenticated user."""
    return await (
        Project.find(Project.owner_id == current_user.id)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )


# ─── Get Single ───────────────────────────────────────────────────────────────

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a single project",
)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
) -> Project:
    return await _get_owned_project(project_id, current_user)


# ─── Delete ───────────────────────────────────────────────────────────────────

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    project = await _get_owned_project(project_id, current_user)
    await project.delete()


# ─── Upload OpenAPI Spec ──────────────────────────────────────────────────────

@router.post(
    "/{project_id}/upload-spec",
    response_model=ProjectResponse,
    summary="Upload an OpenAPI spec (YAML or JSON) to a project",
)
async def upload_spec(
    project_id: str,
    file: UploadFile = File(..., description="OpenAPI YAML or JSON file"),
    current_user: User = Depends(get_current_user),
) -> Project:
    """Parses the spec file and stores it as a document field on the project."""
    import json
    import yaml

    project = await _get_owned_project(project_id, current_user)
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
    project.updated_at = datetime.now(UTC)
    await project.save()
    return project
