from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from app.core.database import SessionDep
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.dependencies.auth import get_access_token_required, get_user_from_access_token

router = APIRouter(prefix="/projects", tags=["Projects"])

def check_scope(required_scope: str):
    def _check(token_data: Annotated[dict, Depends(get_access_token_required)]):
        scopes = token_data.get("scope", "").split()
        if required_scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {required_scope}"
            )
        return token_data
    return _check

@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_user_from_access_token)],
    _: Annotated[dict, Depends(check_scope("create"))]
):
    project = Project(**project_in.model_dump(), user_id=current_user.id)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.get("/", response_model=List[ProjectRead])
def read_projects(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_user_from_access_token)],
    _: Annotated[dict, Depends(check_scope("read"))]
):
    projects = session.exec(select(Project).where(Project.user_id == current_user.id)).all()
    return projects

@router.get("/{project_id}", response_model=ProjectRead)
def read_project(
    project_id: str,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_user_from_access_token)],
    _: Annotated[dict, Depends(check_scope("read"))]
):
    project = session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_user_from_access_token)],
    _: Annotated[dict, Depends(check_scope("update"))]
):
    project = session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = project_in.model_dump(exclude_unset=True)
    for key, value in project_data.items():
        setattr(project, key, value)
    
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_user_from_access_token)],
    _: Annotated[dict, Depends(check_scope("delete"))]
):
    project = session.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    session.delete(project)
    session.commit()
    return {"ok": True}
