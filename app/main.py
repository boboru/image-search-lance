import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, TypedDict
from urllib.parse import urlparse
from urllib.request import url2pathname

import aiofiles
import lancedb
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import get_session
from app.lancedb_utils import prepare_lancedb
from app.models import Image, Search, SearchCreate, SearchUpdate

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class State(TypedDict):
    client: AsyncClient
    async_lancedb: lancedb.AsyncConnection
    async_tbl: lancedb.AsyncTable


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncClient()
    async_db = await lancedb.connect_async(settings.LANCDEDB_PATH)

    # check for table status
    if settings.LANCEDB_TABLE_NAME not in await async_db.table_names():
        logger.info("Lancedb table not found, preparing lancedb...")
        prepare_lancedb()
        logger.info("Lancedb table prepared")

    # set strong consistency for immediate commited data visibility
    async_tbl = await async_db.open_table(settings.LANCEDB_TABLE_NAME)

    yield {"client": client, "async_lancedb": async_db, "async_tbl": async_tbl}

    await client.aclose()
    async_tbl.close()
    async_db.close()


app = FastAPI(lifespan=lifespan)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@app.post("/search", response_model=Search)
async def search(request: Request, search_request: SearchCreate, session: SessionDep):
    client = request.state.client
    # get embedding of query
    query_emb = await client.post(
        f"{settings.EMBED_SERVER_URL}/embed/text", json={"input": search_request.query}
    )
    tbl = request.state.async_tbl

    # search for most similar image
    results = await (
        (await tbl.search(query_emb.json()["embeddings"][0]))
        .distance_type("dot")
        .limit(1)
        .to_list()
    )

    # save search to database
    search_obj = Search(query=search_request.query, image_uri=results[0]["uri"])
    session.add(search_obj)
    await session.commit()
    await session.refresh(search_obj)

    return search_obj


# update search
@app.patch("/search/{id}", response_model=Search)
async def update_search(
    request: Request, id: uuid.UUID, search_update: SearchUpdate, session: SessionDep
):
    search_obj = await session.get(Search, id)
    if not search_obj:
        raise HTTPException(status_code=404, detail="Search not found")
    search_obj.is_good = search_update.is_good
    session.add(search_obj)
    await session.commit()
    await session.refresh(search_obj)
    return search_obj


@app.get("/images/{uri:path}", response_class=FileResponse)
async def get_image(request: Request, uri: str):
    return url2pathname(urlparse(uri).path)


@app.post("/images", status_code=201, response_model=Image)
async def upload_image(request: Request, image: UploadFile):
    client = request.state.client

    # save image to disk, transform to uri
    output_path = f"{settings.IMAGE_DIR}/{image.filename}"
    file_uri = Path(output_path).resolve().as_uri()

    content = await image.read()
    async with aiofiles.open(output_path, "wb") as out_file:
        await out_file.write(content)

    response = await client.post(
        f"{settings.EMBED_SERVER_URL}/embed/image",
        files={"files": (image.filename, content)},
    )

    # add image to lancedb
    tbl = request.state.async_tbl
    await tbl.add([{"uri": file_uri, "vector": response.json()["embeddings"][0]}])
    await tbl.checkout_latest()

    # TODO: consider tbl.optimize() periodically

    return {"uri": file_uri}
