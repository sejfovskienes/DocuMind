import numpy as np
from pathlib import Path
import onnxruntime as ort
from functools import wraps
from datetime import datetime
from transformers import AutoTokenizer

# from app.services import processed_doc_service
# from app.models.processed_document import ProcessedDocumentMetadata

def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
            return instances[cls]
    return get_instance

class NERTask:
    def __init__(self, processing_text: str):
        self.text = processing_text
        self.enqueue_time = datetime.utcnow()

# @singleton
class NERWorker:
    def __init__(self, model_path: str | Path):
        self.model_session = ort.InferenceSession(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
        self.label_map = {0: "O", 1: "PER", 2: "ORG", 3: "LOC", 4: "MISC"} 
    
    def extract_entities(self, processing_text: str):
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
        