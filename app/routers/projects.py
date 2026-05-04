from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Project, Client
from app.schemas.project import ProjectCreate, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectOut])
def list_projects(client_id: int = None, client_name: str = None, db: Session = Depends(get_db)):
    q = db.query(Project)
    if client_id:
        q = q.filter(Project.client_id == client_id)
    if client_name:
        client = db.query(Client).filter(Client.name == client_name).first()
        if client:
            q = q.filter(Project.client_id == client.id)
        else:
            return []
    return q.order_by(Project.name).all()

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.name == payload.client_name).first()
    if not client:
        client = Client(name=payload.client_name, location="Unknown")
        db.add(client)
        db.commit()
        db.refresh(client)
        
    project = Project(name=payload.name, client_id=client.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    db.delete(project)
    db.commit()
