from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database_extension import get_database_session
from app.models import User
from app.routes.auth_router import get_current_user
from app.schemas import DocumentMetadataSchema
from app.services import document_metadata_service, document_service

router = APIRouter(prefix="/process-document", tags=["Document-Metadata"])


@router.get("/get-document-metadata/{document_id}")
def get_document_metadata(
    document_id: int,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, DocumentMetadataSchema]:
    document_service.get_document_by_id(
        db,
        document_id,
        user_id=current_user.id,
    )
    metadata = document_metadata_service.get_document_metadata_by_document_id(
        db,
        document_id,
    )
    return {
        "Processed document metadata": DocumentMetadataSchema.model_validate(metadata)
    }
