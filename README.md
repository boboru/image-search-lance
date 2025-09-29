# Image Search with LanceDB

A REST API built for real-time image search.

## Key Features

- **Image Search:** Search for images using natural language queries.
- **Image Upload:** Upload new images to the vector database.
- **Vector Search:** Uses LanceDB for efficient vector similarity search.
- **Easy to Deploy:** Comes with a Docker Compose setup for quick deployment.

## Tech Stack

- Python 3.12+
- FastAPI
- SQLModel
- PostgreSQL
- LanceDB
- Docker

## Why LanceDB?

LanceDB is a vector database that is designed to be fast and efficient. It is built on top of Lance, a modern columnar data format and designed to handle multimodal data with a lakehouse-style architecture. Since the storage (and indices) is on disk, it is more cost-effective than in-memory databases. LancdDb also supports multple storage backend from cloud object storage to local disk.

## Installation and Setup

### Prerequisites

- Python 3.12+
- Docker
- GPU (optional, for CLIP)

### Quick Start

1.  **Build image**

    ```bash
    docker compose build --no-cache
    ```
    There will be two images built: `backend-api` (CPU-focus) and `embed-api`(GPU-focus). The `embed-api` consists of pytorch dependencies.

2.  **Start the application**

    Use Docker Compose to run the services including postgres, embed-api and backend-api.

    ```bash
    docker compose up 
    ```

    The image search backend API will be available at `http://localhost:8000`. And the embedding API will be available at `http://localhost:8005`. Visit `http://{host}:{port}/docs` to see the API documentation.

## Usage Example

### 0. Initialize LanceDB

Put your images in the `imgs` directory. Or change the `IMAGE_DIR` in the `app/config.py`.

LanceDB will initialize automatically when the application starts. The default table is `images` containing 328 images with embeddings and IVF-PQ index.

### 1. Upload an Image

You can upload an image using a tool like `curl`.

```bash
curl -X 'POST' \
  'http://localhost:8000/images' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'image=@/path/to/your/image.jpg;type=image/jpeg'
```

### 2. Search for an Image

Once you have images in the database, you can search for them with a text query.

```bash
curl -X 'POST' \
  'http://localhost:8000/search' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "fire"
}'
```

The API will return the URI of the most similar image and the search id.

### 3. Submit feedback of the search result

You can submit feedback, `is_good` (1 for good, 0 for bad), for a certain search id.

```bash test the servi
curl -X 'PATCH' \
  'http://localhost:8000/search/{search_id}' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "is_good": false
}'
```

## Load Test
We can conduct load testing using [hey](https://github.com/rakyll/hey).
- Test the embedding API for text

```bash
hey -n 1000 -c 10 -m POST -H "Content-Type: application/json" -d '{"input": "dog"}' http://localhost:8005/embed/text
```

- Test the search API for images

```bash
hey -n 1000 -c 10 -m POST -H "Content-Type: application/json" -d '{"query": "dog"}' http://localhost:8000/search
```