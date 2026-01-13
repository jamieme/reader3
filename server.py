import os
import sys
import pickle
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from reader3 import Book, BookMetadata, ChapterContent, TOCEntry

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Where are the book folders located?
# Populated from command line args
BOOK_DIRS = ["."]

def resolve_book_path(book_id: str):
    """
    Resolves a book ID to its filesystem path.
    ID format: "index:folder_name" or just "folder_name" (fallback).
    Returns (pkl_path, book_folder_path) or (None, None).
    """
    # Try explicit index
    if ":" in book_id:
        try:
            idx_s, folder = book_id.split(":", 1)
            idx = int(idx_s)
            if 0 <= idx < len(BOOK_DIRS):
                base_dir = BOOK_DIRS[idx]
                return os.path.join(base_dir, folder, "book.pkl"), os.path.join(base_dir, folder)
        except ValueError:
            pass

    # Fallback: Search all directories for the folder
    for d in BOOK_DIRS:
        pkl_path = os.path.join(d, book_id, "book.pkl")
        if os.path.exists(pkl_path):
            return pkl_path, os.path.join(d, book_id)
    
    return None, None

@lru_cache(maxsize=10)
def load_book_cached(book_id: str) -> Optional[Book]:
    """
    Loads the book from the pickle file.
    Cached so we don't re-read the disk on every click.
    """
    file_path, _ = resolve_book_path(book_id)
    if not file_path or not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "rb") as f:
            book = pickle.load(f)
        return book
    except Exception as e:
        print(f"Error loading book {book_id}: {e}")
        return None

@app.get("/", response_class=HTMLResponse)
async def library_view(request: Request, dir_index: Optional[int] = None):
    """
    Lists available books. 
    If multiple directories are configured and no dir_index is provided, lists directories.
    """
    # Case 1: Multiple directories and no selection -> Show Directories
    if len(BOOK_DIRS) > 1 and dir_index is None:
        directories = []
        for i, d in enumerate(BOOK_DIRS):
            directories.append({
                "name": os.path.basename(os.path.abspath(d)) or d,
                "path": os.path.abspath(d),
                "index": i
            })
        return templates.TemplateResponse("library.html", {"request": request, "directories": directories})

    # Case 2: Show Books (from specific dir or default single dir)
    target_idx = dir_index if dir_index is not None else 0
    
    if target_idx < 0 or target_idx >= len(BOOK_DIRS):
        # Fallback or error
        target_idx = 0

    target_dir = BOOK_DIRS[target_idx]
    books = []

    if os.path.exists(target_dir):
        for item in os.listdir(target_dir):
            if item.endswith("_data"):
                full_item_path = os.path.join(target_dir, item)
                if os.path.isdir(full_item_path):
                    # Construct ID with index to ensure uniqueness/traceability
                    # e.g. "0:dracula_data"
                    scoped_id = f"{target_idx}:{item}"
                    
                    # Try to load to get title
                    book = load_book_cached(scoped_id)
                    if book:
                        books.append({
                            "id": scoped_id,
                            "title": book.metadata.title,
                            "author": ", ".join(book.metadata.authors),
                            "chapters": len(book.spine)
                        })

    return templates.TemplateResponse("library.html", {"request": request, "books": books})

@app.get("/read/{book_id}", response_class=HTMLResponse)
async def redirect_to_first_chapter(book_id: str):
    """Helper to just go to chapter 0."""
    return await read_chapter(book_id=book_id, chapter_index=0)

@app.get("/read/{book_id}/{chapter_index}", response_class=HTMLResponse)
async def read_chapter(request: Request, book_id: str, chapter_index: int):
    """The main reader interface."""
    book = load_book_cached(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if chapter_index < 0 or chapter_index >= len(book.spine):
        raise HTTPException(status_code=404, detail="Chapter not found")

    current_chapter = book.spine[chapter_index]

    # Calculate Prev/Next links
    prev_idx = chapter_index - 1 if chapter_index > 0 else None
    next_idx = chapter_index + 1 if chapter_index < len(book.spine) - 1 else None

    return templates.TemplateResponse("reader.html", {
        "request": request,
        "book": book,
        "current_chapter": current_chapter,
        "chapter_index": chapter_index,
        "book_id": book_id,
        "prev_idx": prev_idx,
        "next_idx": next_idx
    })

@app.get("/read/{book_id}/images/{image_name}")
async def serve_image(book_id: str, image_name: str):
    """
    Serves images specifically for a book.
    """
    _, book_folder = resolve_book_path(book_id)
    if not book_folder:
        raise HTTPException(status_code=404, detail="Book path not found")

    safe_image_name = os.path.basename(image_name)
    img_path = os.path.join(book_folder, "images", safe_image_name)

    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(img_path)

if __name__ == "__main__":
    import uvicorn
    
    # Parse args for book directories
    if len(sys.argv) > 1:
        BOOK_DIRS = sys.argv[1:]
    else:
        BOOK_DIRS = ["."]

    print(f"Serving books from: {BOOK_DIRS}")
    print("Starting server at http://127.0.0.1:8123")
    uvicorn.run(app, host="127.0.0.1", port=8123)
