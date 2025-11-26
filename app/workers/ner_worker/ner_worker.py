import numpy as np
from time import sleep
from pathlib import Path
import onnxruntime as ort
from functools import wraps
# from datetime import datetime
from transformers import AutoTokenizer

# from app.services import processed_doc_service
# from app.models.processed_document import DocumentMetadata
from app.database import get_session
from app.models.worker_task import WorkerTask
from app.models.document_chunk import DocumentChunk
from app.services import task_service, document_chunk_service

def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
            return instances[cls]
    return get_instance

@singleton
class NERWorker:
    def __init__(self, model_path: str | Path):
        self.model_session = ort.InferenceSession(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
        self.label_map = {0: "O", 1: "PER", 2: "ORG", 3: "LOC", 4: "MISC"} 
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        del self.embedding_model
        del self.tokenizer

    def ner_worker_print(self, text: str) -> None:
        print("\033[93m {}\033[00m".format(text))
    
    def convert_text_to_tokens(self, chunk: DocumentChunk):
        self.ner_worker_print("Converting to tokens...")
        return self.tokenizer(chunk.text, return_tensors="np")
    
    def extract_named_entities(self, inputs):
        self.ner_worker_print("Running model...")
        outputs = self.model_session.run(None, {
            "input_ids": inputs["input_ids"], 
            "attention_mask": inputs["attention_mask"]})
        logits = outputs[0]
        pred_ids = np.argmax(logits, axis=-1)[0]
        return pred_ids
    
    def convert_ids_to_tokens(self, pred_ids, inputs):
        return self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    
    def extract_entities(self, chunk: DocumentChunk):
        processing_text = chunk.text
        print("Converting to tokens...")
        inputs = self.tokenizer(processing_text, return_tensors="np")
        print("Running model...")
        outputs = self.model_session.run(None, {
            "input_ids": inputs["input_ids"], 
            "attention_mask": inputs["attention_mask"]})
        logits = outputs[0]
        pred_ids = np.argmax(logits, axis=-1)[0]
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        entities = []
        for token, pred_id in zip(tokens, pred_ids):
            label = self.label_map.get(pred_id, "O")
            if label != "O":
                entities.append({"token": token, "label": label})
        return entities
    
    def ner_processing(self, ner_task: WorkerTask) -> None:
        document_id = int(ner_task.payload["document_id"])
        document_chunks = document_chunk_service.get_chunks_by_document_id(document_id)
        entities = []
        for chunk in document_chunks:
            entities = self.extract_entities(chunk)
            print(f"ENTITIES FROM CHUNK WITH ID: {chunk.id}:\n{entities}\n\n")
        
    def ner_worker_loop(self) -> None:
        self.ner_worker_print("NER worker started and waiting for tasks...")
        db = get_session()
        while True:
            ner_task = task_service.get_new_task(db, task_type="ner_task")
            if not ner_task:
                db.close()
                self.ner_worker_print("No tasks, worker going to sleep mode.")
                sleep(1)
                continue
            self.ner_processing(ner_task)

            try:
                task_service.update_worker_task(db, ner_task, {"status": "processing"})
                self.extract_named_entities_by_chunk()
            except Exception as e:
                task_service.update_worker_task(db, ner_task, {"status": "failed"})
                self.ner_worker_print(
                    f"An error occured while processing task with id:{id}, error message:{e}")

