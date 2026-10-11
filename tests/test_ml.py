import unittest

from app.ml import ONNXNERModel, SentenceTransformerEmbeddingModel, TransformersNERModel


class ModelAdapterTests(unittest.TestCase):
    def test_embedding_model_accepts_injected_backend(self):
        backend = type("Backend", (), {"encode": lambda self, _text: [0.1, 0.2]})()
        model = SentenceTransformerEmbeddingModel(model=backend)

        self.assertEqual(model.embed("text"), [0.1, 0.2])

    def test_ner_model_accepts_injected_pipeline(self):
        def pipeline(text):
            return [{"word": text, "entity": "ORG"}]

        model = TransformersNERModel(pipeline=pipeline)

        self.assertEqual(model.extract("Acme"), [{"word": "Acme", "entity": "ORG"}])

    def test_onnx_adapter_accepts_injected_runtime_without_loading(self):
        session = object()
        tokenizer = object()
        model = ONNXNERModel("unused.onnx", session=session, tokenizer=tokenizer)

        self.assertEqual(model._get_runtime(), (session, tokenizer))
