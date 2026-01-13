# Reader3 Project Context

## Project Overview
**Reader3** is a lightweight, self-hosted EPUB reader designed to facilitate reading books alongside Large Language Models (LLMs). It parses EPUB files into a structured format and serves them via a local web interface, allowing users to easily copy chapter text for LLM analysis.

## Tech Stack
*   **Language:** Python (>=3.10)
*   **Web Framework:** FastAPI
*   **Template Engine:** Jinja2
*   **EPUB Processing:** `ebooklib`, `beautifulsoup4`
*   **Server:** Uvicorn
*   **Dependency/Task Management:** `uv`

## Key Files & Architecture
*   **`reader3.py`**: The core processing script.
    *   Parses EPUB files using `ebooklib`.
    *   Extracts metadata, TOC, and spine (content).
    *   Cleans HTML content (removes scripts, styles) using `BeautifulSoup`.
    *   Extracts and sanitizes images.
    *   Serializes the processed `Book` object to a `book.pkl` file in a dedicated `*_data` directory.
*   **`server.py`**: The FastAPI web server.
    *   Serves the library view (`/`) listing available books.
    *   Serves the reader interface (`/read/{book_id}/{chapter_index}`).
    *   Implements caching (`@lru_cache`) for loading book data.
    *   Serves extracted images locally.
*   **`templates/`**:
    *   `library.html`: Displays the list of processed books.
    *   `reader.html`: The main reading interface with navigation.
*   **`pyproject.toml`**: Project configuration and dependencies.

## Usage

### 1. Process an EPUB
To import a book into the library, run the processor script on an EPUB file. This creates a directory named `<filename>_data` containing the processed artifacts.

```bash
uv run reader3.py <path_to_epub_file>
```
*Example:* `uv run reader3.py dracula.epub` -> creates `dracula_data/`

### 2. Start the Server
Launch the web server to browse and read books.

```bash
uv run server.py
```
*   Access the library at: `http://127.0.0.1:8123`

## Development Conventions
*   **Data Persistence:** The project uses the local filesystem as a database. Processed books are folders ending in `_data`.
*   **Serialization:** Python `pickle` is used for storing the internal `Book` object structure.
*   **State:** The server is stateless regarding user progress; it simply serves the requested chapter.
*   **Styling:** HTML templates are likely simple and functional, prioritizing content access.
