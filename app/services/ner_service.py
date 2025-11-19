# from transformers import pipeline

# ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)

# def init_ner_pipeline() -> pipeline:
#     return pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)

# #--- TODO: add return type to the function below
# def extract_entities(text: str):
#     ner_pipeline = init_ner_pipeline()
#     results = ner_pipeline(text)
#     entities = [
#         {"entity": ent["entity_group", "word": ent["word"], "score": ent["score"]]} for ent in results
#     ]
#     return entities