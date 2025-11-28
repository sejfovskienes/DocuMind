import os
from art import * #noqa

from .ner_worker import NERWorker

def get_model_path() -> os.path:
    current_dir = os.path.dirname(__file__)
    model_path = os.path.join(current_dir, "..", "..", "core", "onnx", "xlm_roberta_ner.onnx")
    model_path = os.path.abspath(model_path)
    return model_path
    
def main() -> None:
    model_path = get_model_path()
    ner_worker = NERWorker(model_path)
    ner_worker.ner_worker_loop()

if "__name__==__main__":
    tprint("NER Worker") #noqa
    main()