import onnxruntime as ort

from app.services import processed_doc_service
from app.models.processed_document import ProcessedDocumentMetadata

class NERWorker:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(model_path)

    
    def extract_entities(document_metadata: ProcessedDocumentMetadata, text: str) -> dict[str, any]:
        #--- processing by the transformer
        result = {"key": "value"}
        processed_doc_service.update_document_metadata_object(document_metadata, result)
        pass 