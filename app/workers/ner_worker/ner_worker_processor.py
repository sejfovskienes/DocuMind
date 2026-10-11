from pathlib import Path

from app.base.config import ModelConfig

from .ner_worker import NERWorker


def get_model_path() -> Path:
    return Path(ModelConfig.ONNX_NER_MODEL_PATH)


def main() -> None:
    NERWorker(model_path=get_model_path()).ner_worker_loop()


if __name__ == "__main__":
    main()
