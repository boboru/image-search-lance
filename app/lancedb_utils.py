# %%
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

import lancedb
import pandas as pd
import pyarrow as pa
import requests

from app.config import settings

EMBED_SERVER_URL = f"{settings.EMBED_SERVER_URL}/embed/image"
BATCH_SIZE = 32


extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]

schema = pa.schema(
    [
        pa.field("vector", pa.list_(pa.float32(), 512)),
        pa.field("uri", pa.string()),
    ]
)


def prepare_lancedb():
    db = lancedb.connect(settings.LANCDEDB_PATH)
    tbl = db.create_table(settings.LANCEDB_TABLE_NAME, schema=schema, mode="overwrite")
    image_paths = [
        p.resolve().as_uri()
        for p in Path(settings.IMAGE_DIR).rglob("*")
        if p.suffix.lower() in extensions
    ]
    embeddings = []
    for i in range(0, len(image_paths), BATCH_SIZE):
        batch_paths = image_paths[i : i + BATCH_SIZE]
        files = [
            (
                "files",
                open(url2pathname(urlparse(path).path), "rb"),
            )
            for path in batch_paths
        ]
        response = requests.post(EMBED_SERVER_URL, files=files)
        if response.status_code == 200:
            data = response.json()
            embeddings.extend(data["embeddings"])

    data = pd.DataFrame({"uri": image_paths, "vector": embeddings})
    tbl.add(data)

    # add IVF_PQ index
    tbl.create_index(metric="dot", num_partitions=16, num_sub_vectors=32)
