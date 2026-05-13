from fastapi import APIRouter
from backend.api.schemas import ExtractGraphRequest, GraphResponse, NodeResponse, EdgeResponse
from backend.translate.ollama_service import ollama_extract_kg, KB
from backend.translate.translate import translate_long_text, read_docx
from fastapi import UploadFile, File
import tempfile
import os
from fastapi.responses import FileResponse

from backend.utils.pdf_reader import read_pdf
import json
from backend.db.database import SessionLocal
from backend.db.models import Document
import uuid
from backend.translate.translate import save_pdf
from fastapi import HTTPException
from fastapi import BackgroundTasks
from langdetect import detect

router = APIRouter()
os.makedirs("translated_pdf", exist_ok=True)

def split_text(text, max_chars=2000, overlap=400):
    chunks = []
    i = 0

    while i < len(text):
        chunk = text[i:i + max_chars]
        chunks.append(chunk)

        i += max_chars - overlap

    return chunks

import hashlib

def stable_id(name):
    return hashlib.md5(name.encode()).hexdigest()[:8]


def relation_key(r):
    return (
        r["source"].lower().strip(),
        r["target"].lower().strip(),
        r["relation"].lower().strip()
    )


@router.post("/extract-graph", response_model=GraphResponse)
def extract_graph(request: ExtractGraphRequest):
    translated = translate_long_text(request.text)

    chunks = split_text(translated, max_chars=2000)

    entity_map = {}
    relations = []
    relation_set = set()

    for chunk in chunks:
        if not chunk.strip():
            continue

        context_entities = list(entity_map.keys())[-50:]

        kb_chunk = ollama_extract_kg(
            chunk,
            context=context_entities
        )

        for e in kb_chunk.entities:
            key = e["name"].lower().strip()
            if key not in entity_map:
                entity_map[key] = e

        for r in kb_chunk.relations:
            key = relation_key(r)
            if key not in relation_set:
                relation_set.add(key)
                relations.append(r)

    kb = KB(list(entity_map.values()), relations)

    nodes = [
        NodeResponse(
            id=f"{e['id']}_{stable_id(e['name'])}",
            label=e["name"],
            type=e.get("type"),
            source="ollama",
            mentions=find_mentions(translated, e["name"])
        )
        for e in kb.entities
    ]

    name_to_id = {
        e["name"].lower().strip(): f"{e['id']}_{stable_id(e['name'])}"
        for e in kb.entities
    }

    edges = [
        {
            "head": name_to_id.get(r["source"].lower().strip()),
            "tail": name_to_id.get(r["target"].lower().strip()),
            "type": r["relation"],
            "confidence": 1.0
        }
        for r in kb.relations
        if r["source"].lower().strip() in name_to_id and r["target"].lower().strip() in name_to_id
    ]

    return GraphResponse(nodes=nodes, edges=edges)

@router.get("/documents")
def list_documents():
    db = SessionLocal()
    docs = db.query(Document).all()
    db.close()

    return [
        {
            "id": d.id,
            "filename": d.filename,
            "status": d.status,
            "translated_pdf": d.translated_pdf
        }
        for d in docs
    ]


@router.get("/documents/{doc_id}")
def get_document(doc_id: int):
    import json

    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == doc_id).first()
    db.close()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return json.loads(doc.graph_json)


@router.get("/download/{filename}")
def download_file(filename: str):
    path = f"translated_pdf/{filename}"
    return FileResponse(path, media_type='application/pdf', filename=filename)


@router.post("/extract-graph-from-file")
async def extract_graph_from_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    db = SessionLocal()

    doc = Document(
        filename=file.filename,
        content="",
        graph_json="{}",
        status="TRANSLATING"
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.close()

    background_tasks.add_task(process_file_job, doc.id, tmp_path, suffix)

    return {"id": doc.id, "status": "TRANSLATING"}


def process_file_job(doc_id, tmp_path, suffix):
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == doc_id).first()

    if suffix == ".docx":
        paragraphs = read_docx(tmp_path)
        text = "\n".join(paragraphs)
    elif suffix == ".pdf":
        text = read_pdf(tmp_path)
    else:
        return

    doc.content = text
    db.commit()

    translated = translate_long_text(text)

    pdf_name = f"translation_{uuid.uuid4().hex}.pdf"
    pdf_path = f"translated_pdf/{pdf_name}"

    save_pdf(translated.split("\n"), pdf_path)

    doc.translated_pdf = pdf_name
    db.commit()

    process_chunks_and_build_graph(doc, translated, pdf_name, db)
    db.close()
    os.remove(tmp_path)


@router.get("/documents/{doc_id}/status")
def get_status(doc_id: int):
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == doc_id).first()
    db.close()

    if not doc:
        raise HTTPException(404)

    return {
        "status": doc.status,
        "translated_pdf": doc.translated_pdf,
        "processed_chunks": doc.processed_chunks,
        "total_chunks": doc.total_chunks,
        "graph": json.loads(doc.graph_json) if doc.graph_json else None
    }

@router.post("/extract-graph-from-text")
async def extract_graph_from_text(
    request: ExtractGraphRequest,
    background_tasks: BackgroundTasks
):
    db = SessionLocal()

    doc = Document(
        filename="pasted_text",
        content="",
        graph_json="{}",
        status="TRANSLATING"
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.close()

    background_tasks.add_task(process_text_job, doc.id, request.text)

    return {"id": doc.id, "status": "TRANSLATING"}


def process_text_job(doc_id, text):
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == doc_id).first()

    doc.content = text
    db.commit()

    try:
        lang = detect(text)
    except:
        lang = "unknown"

    translated = translate_long_text(text) if lang == "sl" else text

    pdf_name = f"translation_{uuid.uuid4().hex}.pdf"
    pdf_path = f"translated_pdf/{pdf_name}"

    save_pdf(translated.split("\n"), pdf_path)

    doc.translated_pdf = pdf_name
    db.commit()

    process_chunks_and_build_graph(doc, translated, pdf_name, db)
    db.close()


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int):
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == doc_id).first()

    if not doc:
        db.close()
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.translated_pdf:
        pdf_path = f"translated_pdf/{doc.translated_pdf}"
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    db.delete(doc)
    db.commit()
    db.close()

    return {"message": "Deleted"}


def process_chunks_and_build_graph(doc, translated, pdf_name, db):
    try:
        chunks = split_text(translated, max_chars=2000)

        doc.total_chunks = len(chunks)
        doc.processed_chunks = 0
        doc.status = "NER"
        db.commit()

        entity_map = {}
        relations = []
        relation_set = set()

        for i, chunk in enumerate(chunks, start=1):

            doc.processed_chunks = i - 1
            db.commit()

            if not chunk.strip():
                continue

            context_entities = list(entity_map.keys())[-50:]

            kb_chunk = ollama_extract_kg(
                chunk,
                context=context_entities
            )

            # merge entities
            for e in kb_chunk.entities:
                key = e["name"].lower().strip()
                if key not in entity_map:
                    entity_map[key] = e

            # merge relations
            for r in kb_chunk.relations:
                key = relation_key(r)
                if key not in relation_set:
                    relation_set.add(key)
                    relations.append(r)

            # update progress
            doc.processed_chunks = i
            db.commit()

            update_graph(doc, entity_map, relations, pdf_name, db, translated)

        doc.status = "DONE"
        db.commit()
    except Exception as e:
        doc.status = "FAILED"
        db.commit()
        print("ERROR:", e)


def update_graph(doc, entity_map, relations, pdf_name, db, translated):
    nodes = [
        {
            "id": f"{e['id']}_{stable_id(e['name'])}",
            "label": e["name"],
            "type": e.get("type"),
            "source": "ollama",
            "mentions": find_mentions(translated, e["name"])
        }
        for e in entity_map.values()
    ]

    name_to_id = {
        e["name"].lower().strip(): f"{e['id']}_{stable_id(e['name'])}"
        for e in entity_map.values()
    }

    edges = [
        {
            "head": name_to_id.get(r["source"].lower().strip()),
            "tail": name_to_id.get(r["target"].lower().strip()),
            "type": r["relation"],
            "confidence": 1.0
        }
        for r in relations
        if r["source"].lower().strip() in name_to_id
        and r["target"].lower().strip() in name_to_id
    ]

    doc.graph_json = json.dumps({
        "nodes": nodes,
        "edges": edges,
        "filename": doc.filename,
        "translated_pdf": pdf_name
    })

    db.commit()


def find_mentions(text: str, entity_name: str):
    mentions = []
    entity_lower = entity_name.lower()

    lines = text.splitlines()

    for line_number, line in enumerate(lines, start=1):
        if entity_lower in line.lower():
            mentions.append({
                "line": line_number,
                "text": line.strip()
            })

    return mentions