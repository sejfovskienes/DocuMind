import sys
import numpy as np
from time import sleep
from pathlib import Path
import onnxruntime as ort
from functools import wraps
from datetime import datetime 
from sqlalchemy.orm import Session
from transformers import AutoTokenizer

from app.database import get_session
from app.models.worker_task import WorkerTask
from app.models.document_chunk import DocumentChunk
from app.services import document_chunk_service, task_service
from app.core.enum import worker_task_status, worker_task_type

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
        inputs = self.tokenizer(processing_text, return_tensors="np")
        outputs = self.model_session.run(None, {
            "input_ids": inputs["input_ids"],
            "attention_mask": inputs["attention_mask"],
        })
        logits = outputs[0]
        pred_ids = np.argmax(logits, axis=-1)[0]
        print("Unique predicted IDs:", set(pred_ids))
        print(f"Outputs shape:\n{outputs[0].shape}")
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        SPECIAL_TOKENS = {"<s>", "</s>", "<pad>"}
        entities = []
        current_word = ""
        current_label = "O"
        for token, pred_id in zip(tokens, pred_ids):
            label = self.label_map.get(pred_id, "O")
            if token in SPECIAL_TOKENS:
                continue
            if token.startswith("▁"):
                if current_word and current_label != "O":
                    entities.append(
                        {"word": current_word, 
                         "label": current_label})
                current_word = token[1:]  #--- remove ▁
                current_label = label
            else:
                current_word += token
                if label != "O":
                    current_label = label
        if current_word and current_label != "O":
            entities.append({"word": current_word, "label": current_label})
        return entities

    def ner_processing(self, 
                       db: Session, 
                       ner_task: WorkerTask) -> None:
        document_id = int(ner_task.payload["document_id"])
        document_chunks = document_chunk_service.get_chunks_by_document_id(db, document_id)
        entities = []
        for chunk in document_chunks:
            entities = self.extract_entities(chunk)
            print(f"ENTITIES FROM CHUNK WITH ID: {chunk.id}:\n{entities}\n")
        
    def ner_worker_loop(self) -> None:
        self.ner_worker_print("NER worker started and waiting for tasks...")
        db = get_session()
        try: 
            while True:
                ner_task = task_service.get_new_task(
                    db, 
                    task_type=worker_task_type.WorkerTaskType.ENTITY_EXTRACTION)
                if not ner_task:
                    db.close()
                    self.ner_worker_print("No tasks, worker going to sleep mode...")
                    sleep(1)
                    continue
                # self.ner_processing(ner_task)
                try:
                    task_service.update_worker_task(
                        db, 
                        ner_task, 
                        {"status": worker_task_status.WorkerTaskStatus.PROCESSING})
                    self.ner_processing(db, ner_task)
                except Exception as e:
                    task_service.update_worker_task(
                        db, 
                        ner_task, 
                        {"status": worker_task_status.WorkerTaskStatus.FAILED})
                    self.ner_worker_print(
                        f"An error occured while processing task with id:{id}, error message:{e}")
                finally:
                    task_service.update_worker_task(
                        db,
                        ner_task,
                        {"status": worker_task_status.WorkerTaskStatus.FINISHED, "finshed_at": datetime.utcnow()}
                    )
        except KeyboardInterrupt:
            self.ner_worker_print("Worker stopped.\n\n")
            self.ner_worker_print("="*55)
            sys.exit(0)
