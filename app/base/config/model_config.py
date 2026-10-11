from typing import ClassVar


class ModelConfig:
    """Model settings for DocuMind."""

    EMBEDDING_MODEL_NAME: ClassVar[str] = "all-mpnet-base-v2"
    EMBEDDING_VECTOR_SIZE: ClassVar[int] = 768
    NER_TRANSFORMERS_MODEL_NAME: ClassVar[str] = "dslim/bert-base-NER"
    ONNX_NER_MODEL_PATH: ClassVar[str] = "app/core/onnx/xlm_roberta_ner.onnx"
    NER_TOKENIZER_MODEL_NAME: ClassVar[str] = "xlm-roberta-base"
