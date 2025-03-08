from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.services.template_service import TemplateService
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateResponse

router = APIRouter()

@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    db: Session = Depends(get_db)
):
    """List all prompt templates"""
    template_service = TemplateService(db)
    templates = template_service.get_templates()
    return templates

@router.post("/", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new prompt template"""
    template_service = TemplateService(db)
    new_template = template_service.create_template(template)
    return new_template

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific prompt template"""
    template_service = TemplateService(db)
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a prompt template"""
    template_service = TemplateService(db)
    updated_template = template_service.update_template(template_id, template)
    if not updated_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return updated_template

@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Delete a prompt template"""
    template_service = TemplateService(db)
    success = template_service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}

@router.post("/{template_id}/set-active")
async def set_active_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Set a template as the active template"""
    template_service = TemplateService(db)
    success = template_service.set_active_template(template_id, user_id="default")
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template set as active successfully"}