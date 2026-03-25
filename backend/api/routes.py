from fastapi import APIRouter
from backend.api.schemas import ExtractGraphRequest, GraphResponse, NodeResponse, EdgeResponse
from backend.translate.ner import rebel_on_long_text
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

@router.post("/extract-graph", response_model=GraphResponse)
def extract_graph(request: ExtractGraphRequest):
    translated = translate_long_text(request.text)
    kb = rebel_on_long_text(translated)

    nodes = []
    edges = []

    for entity in kb.entities:
        nodes.append(NodeResponse(
            id=entity,
            label=entity,
            type=None,
            source="rebel"
        ))

    for rel in kb.relations:
        edges.append(EdgeResponse(
            head=rel["head"],
            tail=rel["tail"],
            type=rel["type"],
            confidence=1.0
        ))

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
    doc.status = "NER"
    db.commit()

    kb = rebel_on_long_text(translated)

    nodes = [
        {
            "id": e,
            "label": e,
            "type": None,
            "source": "rebel"
        }
        for e in kb.entities
    ]

    edges = [
        {
            "head": r["head"],
            "tail": r["tail"],
            "type": r["type"],
            "confidence": 1.0
        }
        for r in kb.relations
    ]

    doc.graph_json = json.dumps({
        "nodes": nodes,
        "edges": edges,
        "filename": doc.filename,
        "translated_pdf": pdf_name
    })

    doc.status = "DONE"
    db.commit()

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
        "translated_pdf": doc.translated_pdf
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

    if lang == "sl":
        translated = translate_long_text(text)
    else:
        translated = text

    pdf_name = f"translation_{uuid.uuid4().hex}.pdf"
    pdf_path = f"translated_pdf/{pdf_name}"

    save_pdf(translated.split("\n"), pdf_path)

    doc.translated_pdf = pdf_name
    doc.status = "NER"
    db.commit()

    kb = rebel_on_long_text(translated)

    nodes = [
        {
            "id": e,
            "label": e,
            "type": None,
            "source": "rebel"
        }
        for e in kb.entities
    ]

    edges = [
        {
            "head": r["head"],
            "tail": r["tail"],
            "type": r["type"],
            "confidence": 1.0
        }
        for r in kb.relations
    ]

    doc.graph_json = json.dumps({
        "nodes": nodes,
        "edges": edges,
        "filename": "pasted_text",
        "translated_pdf": pdf_name,
        "created_at": doc.created_at.isoformat()
    })

    doc.status = "DONE"
    db.commit()
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
