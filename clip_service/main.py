import io

import torch
from fastapi import FastAPI, UploadFile
from PIL import Image
from pydantic import BaseModel
from transformers import CLIPModel, CLIPProcessor

app = FastAPI(title="CLIP Embedding Service")

# Select device
device = (
    "mps"
    if torch.backends.mps.is_available()
    else ("cuda" if torch.cuda.is_available() else "cpu")
)

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32", use_fast=False
)


class TextQuery(BaseModel):
    input: str | list[str]


class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]]


@app.post("/embed/text", response_model=EmbeddingResponse)
async def embed_text(query: TextQuery):
    inputs = processor(text=query.input, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        text_embeds = model.get_text_features(**inputs)

    # normalize for cosine similarity
    text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)
    return EmbeddingResponse(embeddings=text_embeds.cpu().tolist())


@app.post("/embed/image", response_model=EmbeddingResponse)
async def embed_image(files: list[UploadFile]):
    if isinstance(files, UploadFile):
        files = [files]
    images = []
    for file in files:
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")
        images.append(image)
    inputs = processor(images=images, return_tensors="pt").to(device)
    with torch.no_grad():
        image_embeds = model.get_image_features(**inputs)

    # normalize for cosine similarity
    image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
    return EmbeddingResponse(embeddings=image_embeds.cpu().tolist())


@app.get("/health")
async def healthcheck():
    return {"status": "ok", "device": device}
