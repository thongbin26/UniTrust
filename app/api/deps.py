from fastapi import Request
from typing import Generator
from app.verification.service import VerificationService
from app.verification.repository import OfficialStructuredRepository
import sqlite3

def get_verification_service(request: Request) -> VerificationService:
    return request.app.state.verification_service

def get_structured_repository(request: Request) -> OfficialStructuredRepository:
    return request.app.state.repository

def get_db_connection():
    from app.db.database import get_connection
    with get_connection() as conn:
        yield conn
