"""API routing configuration."""
from fastapi import APIRouter

from app.api.v1 import auth, workflows, resumes

# Initialize the v1 router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(workflows.router)
api_router.include_router(resumes.router)
# Will add: students, resumes, analysis, matching, approvals, etc.
