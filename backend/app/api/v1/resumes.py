"""API router for resume uploading and parsing."""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_student, get_db
from app.models.user import Student
from app.models.profile import Resume, StudentProfile
from app.services.file_storage import save_upload_file
from app.agents.graph import agent_runner
from app.agents.state import PlacementState

router = APIRouter(prefix="/resumes", tags=["Resumes"])


class ResumeUploadResponse(BaseModel):
    resume_id: uuid.UUID
    status: str
    message: str


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume, securely store it, and dispatch the LangGraph Resume Agent.
    """
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed."
        )

    # 1. Read & Securely Store
    contents = await file.read()
    try:
        file_path, file_hash, file_size = await save_upload_file(
            file_content=contents,
            original_filename=file.filename,
            content_type=file.content_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Database Record
    db_resume = Resume(
        student_id=student.id,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        file_hash=file_hash,
        status="processing"
    )
    db.add(db_resume)
    await db.commit()
    await db.refresh(db_resume)

    # 3. Trigger Resume Agent directly (Since we are testing the agent in Lab 2)
    # Normally this is triggered by the coordinator via /workflows/start.
    initial_state = {
        "student_id": str(student.id),
        "run_id": str(uuid.uuid4()),
        "consent_validated": True, # Hardcoded for Lab 2 isolation testing
        "resume_data": {
            "file_path": file_path,
            "mime_type": file.content_type,
        },
        "current_step": "init",
    }
    
    # We invoke the subgraph directly for immediate feedback in this lab
    thread = {"configurable": {"thread_id": str(db_resume.id)}}
    try:
         # In a real scenario we'd use Celery for async execution, but we'll wait for it here
         final_state = agent_runner.invoke(initial_state, config=thread)
    except Exception as e:
        db_resume.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"LLM Processing failed: {str(e)}")

    if "errors" in final_state and final_state["errors"]:
        db_resume.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Agent Error: {final_state['errors']}")

    # 4. Save extracted profile
    profile_data = final_state.get("student_profile", {})
    if profile_data:
        db_resume.status = "parsed"
        
        # Upsert Student Profile
        db_profile = StudentProfile(
            student_id=student.id,
            resume_id=db_resume.id,
            summary=profile_data.get("summary", ""),
            status="draft"
        )
        db.add(db_profile)
        # In a full implementation, we'd iterate and save the skills/projects DB models as well!
        
        await db.commit()
        
    return {
        "resume_id": db_resume.id,
        "status": "success",
        "message": "Resume uploaded and successfully parsed by the Agent."
    }
