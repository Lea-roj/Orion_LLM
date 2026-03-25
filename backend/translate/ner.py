import re
import warnings
import math
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import spacy
import os
from colorama import init, Fore

from backend.translate.knowledge_base import KB

init()

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")
nlp = spacy.load("en_core_web_lg")

warnings.filterwarnings("ignore", category=UserWarning)


def extract_relations_from_model_output(text):
    relations = []
    relation, subject, object_ = '', '', ''
    text = text.strip()
    current_processed_token = 'x'

    text_replaced = text.replace("<s>", "").replace("<pad>", "").replace("</s>", "")

    for token in text_replaced.split():
        if token == "<triplet>":
            current_processed_token = 't'
            if relation != '':
                relations.append({
                    'head': subject.strip(),
                    'type': relation.strip(),
                    'tail': object_.strip()
                })
                relation = ''
            subject = ''
        elif token == "<subj>":
            current_processed_token = 's'
            if relation != '':
                relations.append({
                    'head': subject.strip(),
                    'type': relation.strip(),
                    'tail': object_.strip()
                })
            object_ = ''
        elif token == "<obj>":
            current_processed_token = 'o'
            relation = ''
        else:
            if current_processed_token == 't':
                subject += ' ' + token
            elif current_processed_token == 's':
                object_ += ' ' + token
            elif current_processed_token == 'o':
                relation += ' ' + token

    if subject != '' and relation != '' and object_ != '':
        relations.append({
            'head': subject.strip(),
            'type': relation.strip(),
            'tail': object_.strip()
        })
    return relations


def from_long_text_to_kb_using_nlp(input_text, span_l, overlap_l, max_l, l_penalty, num_beams, num_return_sequences):
    processed_text = nlp(input_text)
    number_of_spans = math.ceil((len(processed_text) - span_l) / (span_l - overlap_l)) + 1
    spans_boundaries = []

    start = 0
    for i in range(number_of_spans):
        span_start = max(start, 0)
        span_end = min(start + span_l, len(processed_text))
        spans_boundaries.append((span_start, span_end))
        start += span_l - overlap_l

    knowledge_base = KB()

    for span_start, span_end in spans_boundaries:
        span_text = processed_text[span_start:span_end].text
        doc = nlp(span_text)

        for ent in doc.ents:
            knowledge_base.add_entity({
                "title": ent.text,
                "category": ent.label_
            })

        model_inputs = tokenizer(
            span_text, return_tensors='pt', padding=True, truncation=True, max_length=512
        )

        generate_arguments = {
            "max_length": max_l,
            "length_penalty": l_penalty,
            "num_beams": num_beams,
            "num_return_sequences": num_return_sequences
        }

        generated_tokens = model.generate(**model_inputs, **generate_arguments)
        decoded_back_to_text = tokenizer.batch_decode(generated_tokens, skip_special_tokens=False)

        for sentence_prediction in decoded_back_to_text:
            relations = extract_relations_from_model_output(sentence_prediction)
            for relation in relations:
                if relation["head"] in span_text and relation["tail"] in span_text and relation["type"]:
                    relation["meta"] = {
                        "spans": [(span_start, span_end)]
                    }
                    knowledge_base.add_relation(relation)

    return knowledge_base


def rebel_on_long_text(text):
    chunks = re.split(r'(?<=[.!?])\s+', text)

    kb = KB()

    for chunk in chunks:
        if not chunk.strip():
            continue

        sub_kb = from_long_text_to_kb_using_nlp(
            chunk,
            span_l=150,
            overlap_l=10,
            max_l=512,
            l_penalty=1,
            num_beams=5,
            num_return_sequences=2
        )

        kb.entities.update(sub_kb.entities)
        kb.relations.extend(sub_kb.relations)

    return kb