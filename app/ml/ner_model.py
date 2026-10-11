from pathlib import Path
from typing import Any

from app.base.config import ModelConfig


class TransformersNERModel:
    """Lazy adapter for the active Hugging Face token classification model."""

    def __init__(
        self,
        model_name: str = ModelConfig.NER_TRANSFORMERS_MODEL_NAME,
        pipeline: Any | None = None,
    ):
        self.model_name = model_name
        self._pipeline = pipeline

    def _get_pipeline(self) -> Any:
        if self._pipeline is None:
            from transformers import (  # Heavy optional dependency
                AutoModelForTokenClassification,
                AutoTokenizer,
                pipeline,
            )

            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            self._pipeline = pipeline("ner", model=model, tokenizer=tokenizer)
        return self._pipeline

    def extract(self, text: str) -> list[dict[str, Any]]:
        entities = self._get_pipeline()(text)
        return [
            {**entity, "score": float(entity["score"])} if "score" in entity else entity
            for entity in entities
        ]


class ONNXNERModel:
    """Optional ONNX inference adapter retained for the bundled ONNX model."""

    label_map = {0: "O", 1: "PER", 2: "ORG", 3: "LOC", 4: "MISC"}

    def __init__(
        self,
        model_path: str | Path,
        tokenizer_name: str = ModelConfig.NER_TOKENIZER_MODEL_NAME,
        session: Any | None = None,
        tokenizer: Any | None = None,
    ):
        self.model_path = Path(model_path)
        self.tokenizer_name = tokenizer_name
        self._session = session
        self._tokenizer = tokenizer

    def _get_runtime(self) -> tuple[Any, Any]:
        if self._session is None:
            import onnxruntime

            self._session = onnxruntime.InferenceSession(str(self.model_path))
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
        return self._session, self._tokenizer

    def tokenize(self, text: str) -> dict[str, Any]:
        _, tokenizer = self._get_runtime()
        return tokenizer(text, return_tensors="np")

    def infer(self, inputs: dict[str, Any]) -> Any:
        import numpy as np

        session, _ = self._get_runtime()
        outputs = session.run(
            None,
            {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            },
        )
        return np.argmax(outputs[0], axis=-1)[0]

    def tokens(self, inputs: dict[str, Any]) -> Any:
        _, tokenizer = self._get_runtime()
        return tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

    def predict(self, text: str) -> tuple[Any, Any]:
        inputs = self.tokenize(text)
        return self.infer(inputs), self.tokens(inputs)
