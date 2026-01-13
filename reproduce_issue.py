import os
import pickle
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import sys
from datetime import datetime

# Mimic the classes from reader3.py needed for pickling
@dataclass
class ChapterContent:
    id: str
    href: str
    title: str
    content: str
    text: str
    order: int

@dataclass
class TOCEntry:
    title: str
    href: str
    file_href: str
    anchor: str
    children: List['TOCEntry'] = field(default_factory=list)

@dataclass
class BookMetadata:
    title: str
    language: str
    authors: List[str] = field(default_factory=list)
    description: Optional[str] = None
    publisher: Optional[str] = None
    date: Optional[str] = None
    identifiers: List[str] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)

@dataclass
class Book:
    metadata: BookMetadata
    spine: List[ChapterContent]
    toc: List[TOCEntry]
    images: Dict[str, str]
    source_file: str
    processed_at: str
    version: str = "3.0"

# Create dummy data
def create_dummy_data():
    os.makedirs("epub_test/book1_data", exist_ok=True)
    
    book = Book(
        metadata=BookMetadata(title="Test Book", language="en", authors=["Me"]),
        spine=[ChapterContent("1", "ch1.html", "Chapter 1", "<p>Hello</p>", "Hello", 0)],
        toc=[TOCEntry("Chapter 1", "ch1.html", "ch1.html", "")],
        images={},
        source_file="test.epub",
        processed_at=datetime.now().isoformat()
    )
    
    with open("epub_test/book1_data/book.pkl", "wb") as f:
        pickle.dump(book, f)
    
    print("Created dummy book.pkl")

if __name__ == "__main__":
    create_dummy_data()
