from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.base.extensions import ensure_upload_dir
from app.core.enum import WorkerTaskType
from app.database_extension import get_database_session
from app.models import User, WorkerTask
from app.schemas import DocumentSchema, DocumentUploadResponse, WorkerTaskSchema
from app.services import document_service, worker_task_service

from .auth_router import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upsert-file")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    filename = file.filename or "upload"
    upload_dir = ensure_upload_dir()
    file_path = upload_dir / f"{uuid4()}_{Path(filename).name}"
    try:
        await document_service.write_document_locally(file, str(file_path))
        document = document_service.create_document(
            db,
            current_user.id,
            filename=filename,
            file_path=str(file_path),
            commit=False,
        )
        task = WorkerTask(
            payload={"document_id": document.id},
            task_type=WorkerTaskType.DOCUMENT_PROCESSING,
        )
        worker_task_service.save_worker_task(db, task, commit=False)
        db.commit()
    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    db.refresh(document)
    db.refresh(task)

    return DocumentUploadResponse(
        message="Document uploaded successfully",
        document=DocumentSchema.model_validate(document),
        worker_task=WorkerTaskSchema.model_validate(task),
    )


@router.get("/get-document/{document_id}")
def get_document_by_id(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session),
) -> dict[str, DocumentSchema]:
    document = document_service.get_document_by_id(
        db,
        document_id,
        user_id=current_user.id,
    )
    return {f"file:{document_id} object": DocumentSchema.model_validate(document)}


@router.get("/delete-document/{document_id}")
def delete_file(
    document_id: int,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    document_service.delete_document_by_id(
        db,
        document_id,
        user_id=current_user.id,
    )
    return {
        "message": f"Document with id: {document_id} has been deleted successfully!"
    }
