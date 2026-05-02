#!/usr/bin/env python3
"""RAG-powered CLI tutor for learning quantitative finance."""

import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Optional, Dict
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.theme import Theme
from rich.syntax import Syntax
from rich import box
from rich.rule import Rule

from rag.manifest import load_manifest, show_progress, get_active_phase
from rag.ingest import DocumentIngestor
from rag.embed import get_embedder
from rag.store import VectorStore
from rag.retrieve import TutorRetriever
from rag.config import load_config, set_api_key

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "green",
    "user": "bold cyan",
    "ai": "italic yellow",
    "dim": "dim",
})

console = Console(theme=custom_theme)

API_BASE = "https://openrouter.ai/api/v1"

def get_system_prompt(manifest: dict) -> str:
    cleared = [k for k, v in manifest.get("cleared", {}).items() if v.get("cleared")]
    remaining = [r for r in manifest.get("remaining", []) if not r.get("completed")]
    active_phase = get_active_phase()
    
    remaining_str = "\n".join([f"- {r['topic']}: {', '.join(r['subtopics'])}" for r in remaining[:6]])
    
    return f"""You are tutoring a 19-year-old self-taught developer building a quantitative market intelligence platform for crypto futures traders.

YOUR RULES:
1. No textbooks unless absolutely necessary. Papers and docs only.
2. No more than 40 pages per resource. If longer, point to specific sections only.
3. Explain by connecting directly to what they are building — not abstract examples.
4. When they hit a wall, study exactly what the wall requires. No front-loading theory.
5. If they ask about a concept, explain it, then show where it appears in their system.
6. Never tell them to read something already cleared. Track what's been covered.
7. Challenge understanding by asking them to explain things back.
8. No motivation speeches. No "great question." Just direct answers.
9. When citing sources, use the context chunks provided. Cite as [source: filename]

CLEARED TOPICS:
{chr(10).join(cleared) if cleared else "None yet"}

ACTIVE PHASE: {active_phase}

REMAINING GAPS (priority order):
{remaining_str}

BUILD PHASES:
- Phase 1-2: Ingestion + microstructure (VPIN, Glosten-Milgrom, Kyle)
- Phase 3: Regime detection (HMM - Rabiner tutorial)
- Phase 4: Alternative data (Granger causality, sentiment analysis)
- Phase 5: LLM reasoner (prompt engineering, Pearl causality)

KEY ANALOGIES:
- Market regime = hidden state
- Price behavior = observation sequence
- Order flow = data stream
- Adverse selection = what they're measuring
- Regime detection via HMM = speech recognition math applied to markets

When they want VISUALIZATION, write Python code in ```python blocks```."""

def get_api_key() -> str:
    config = load_config()
    if config.get("api_key"):
        return config["api_key"]
    console.print("[warning]No API key found. Please enter your OpenRouter API key:[/warning]")
    console.print("[dim]Get one free at: https://openrouter.ai[/dim]")
    api_key = Prompt.ask("[user]API Key[/user]").strip()
    set_api_key(api_key)
    return api_key

def build_prompt(query: str, context: Dict) -> str:
    sources = context.get("sources", [])
    chunks = context.get("chunks", [])
    
    context_text = ""
    if chunks:
        context_text = "\n\n".join([
            f"[Source: {c['source']}]\n{c['text'][:600]}"
            for c in chunks[:3]
        ])
    
    system_prompt = f"""You are tutoring a 19-year-old self-taught developer building a quantitative market intelligence platform.

RULES:
- Connect concepts to their trading system
- Use market microstructure analogies
- Cite sources when using context
- No motivation speeches

CONTEXT FROM DOCUMENTS:
{context_text}

SOURCES: {', '.join(sources) if sources else 'None - use general knowledge'}

Remember: They learn by building, then hitting walls, then studying exactly what the wall requires. Don't front-load theory."""

    user_prompt = f"""Based on the context above and your knowledge, answer this question:

{query}

If the context is relevant, cite it. If not, answer from knowledge but note you're going beyond the loaded documents."""

    return f"{system_prompt}\n\n{user_prompt}"

def call_llm(query: str, context: Dict) -> str:
    api_key = get_api_key()
    
    prompt = build_prompt(query, context)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://qfin-rag.local",
        "X-Title": "QFin RAG Tutor"
    }
    
    try:
        resp = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json={
                "model": "openrouter/free",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            },
            timeout=120
        )
        
        if resp.status_code != 200:
            return f"Error {resp.status_code}: {resp.text[:200]}"
        
        result = resp.json()
        return result["choices"][0]["message"]["content"]
    
    except requests.exceptions.Timeout:
        return "Request timed out. Try again."
    except Exception as e:
        return f"Error: {str(e)[:200]}"

def show_welcome():
    progress = show_progress()
    manifest = load_manifest()
    active_phase = get_active_phase()
    
    remaining = manifest.get("remaining", [])
    next_topic = remaining[0]["topic"] if remaining else "None"
    
    console.print(Panel(
        f"[bold cyan]QFin RAG Tutor[/bold cyan] - Your learning pipeline\n\n"
        f"[yellow]Building:[/yellow] Quantitative market intelligence platform\n"
        f"[yellow]Active Phase:[/yellow] {active_phase}\n"
        f"[yellow]Next:[/yellow] {next_topic}\n\n"
        f"[dim]Progress:[/dim] {progress['total_cleared']} cleared, {progress['total_remaining']} remaining\n"
        f"[dim]Documents:[/dim] {len(manifest.get('cleared', {}))} cleared sources loaded\n\n"
        f"[dim]Commands:[/dim]\n"
        f"  [info]add[/info] <file>     Add a document (PDF, MD, TXT)\n"
        f"  [info]ls[/info]             List loaded documents\n"
        f"  [info]clear[/info]          Clear conversation\n"
        f"  [info]progress[/info]      Show learning progress\n"
        f"  [info]sources[/info]       Show document sources\n"
        f"  [info]exit[/info]           Quit",
        box=box.DOUBLE,
        border_style="cyan",
        title="QFin RAG Tutor",
    ))

def show_progress_display():
    progress = show_progress()
    manifest = load_manifest()
    
    console.print(Panel(
        f"[bold cyan]Learning Progress[/bold cyan]\n\n"
        f"[green]CLEARED ({progress['total_cleared']}):[/green]\n" +
        "\n".join([f"  ✓ {t}" for t in progress['cleared']]) +
        f"\n\n[yellow]REMAINING ({progress['total_remaining']}):[/yellow]\n" +
        "\n".join([f"  {r['id']}. {r['topic']} ({r['phase']})" for r in manifest.get('remaining', []) if not r.get('completed')]),
        box=box.ROUNDED,
        border_style="green",
        title="Progress"
    ))

def show_sources():
    store = VectorStore()
    if store.load():
        stats = store.get_stats()
        if stats["total_chunks"] == 0:
            console.print("[warning]No documents loaded. Use 'add' to add documents.[/warning]")
            return
        
        console.print(Panel(
            f"[bold cyan]Loaded Documents[/bold cyan]\n\n"
            f"Total chunks: {stats['total_chunks']}\n"
            f"Unique sources: {stats['unique_sources']}\n\n"
            f"[yellow]Sources:[/yellow]\n" + "\n".join([f"  - {s}" for s in stats["sources"]]),
            box=box.ROUNDED,
            border_style="cyan",
            title="Documents"
        ))
    else:
        console.print("[warning]No vector store found. Add documents first.[/warning]")

def add_document(file_path: str, show_progress: bool = True):
    try:
        ingestor = DocumentIngestor()
        embedder = get_embedder()
        store = VectorStore(embedder_dim=embedder.embedding_dim)
        
        if show_progress:
            console.print(f"[dim]Ingesting {file_path}...[/dim]")
        
        doc = ingestor.add_document(file_path)
        
        chunks = doc.get("chunks", [])
        if not chunks:
            console.print(f"[warning]No text in {file_path} (scanned PDF?).[/warning]")
            return False
        
        if show_progress:
            console.print(f"[dim]Embedding {len(chunks)} chunks...[/dim]")
        
        embeddings = embedder.encode_chunks(chunks)
        
        if store.load():
            existing = store.get_stats()["total_chunks"]
        else:
            existing = 0
        
        store.add_chunks(chunks, embeddings)
        store.save()
        
        if show_progress:
            console.print(f"[success]Added {len(chunks)} chunks (was {existing}, now {existing + len(chunks)})[/success]")
        
        return True
    
    except Exception as e:
        console.print(f"[danger]Error: {e}[/danger]")
        return False

def add_all_docs():
    ingestor = DocumentIngestor()
    store = None
    
    for path in sorted(Path("docs").glob("*")):
        if path.suffix.lower() in {".pdf", ".md", ".txt", ".html"}:
            result = add_document(str(path), show_progress=False)
            if result:
                console.print(f"[green]✓[/green] {path.name}")
            else:
                console.print(f"[dim]—[/dim] {path.name} (no text)")
    
    console.print(f"\n[success]Done. Check sources with 'python rag_cli.py sources'[/success]")

def run_chat():
    store = VectorStore()
    store.load()
    retriever = TutorRetriever(store)
    manifest = load_manifest()
    
    messages = []
    
    show_welcome()
    
    while True:
        console.print()
        user_input = Prompt.ask("[user]You[/user]").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ["exit", "quit", "q"]:
            console.print("[success]Goodbye![/success]")
            break
        
        if user_input.lower() == "clear":
            messages = []
            show_welcome()
            continue
        
        if user_input.lower() == "progress":
            show_progress_display()
            continue
        
        if user_input.lower() == "sources":
            show_sources()
            continue
        
        if user_input.lower().startswith("add "):
            file_path = user_input[4:].strip()
            add_document(file_path)
            continue
        
        if user_input.lower() == "menu" or user_input.lower() == "help":
            show_welcome()
            continue
        
        console.print("[dim]Thinking...[/dim]", end="\r")
        
        context = retriever.build_context_for_tutor(user_input)
        response = call_llm(user_input, context)
        
        console.print("\r" + " " * 50 + "\r")
        
        md = Markdown(response)
        console.print(Panel(md, box=box.ROUNDED, border_style="yellow", title="AI"))
        
        if context.get("sources"):
            console.print(f"[dim]Sources: {', '.join(context['sources'])}[/dim]")

def main():
    args = sys.argv[1:]
    
    if not args:
        run_chat()
    elif args[0] == "add":
        if len(args) < 2:
            console.print("[warning]Usage: python rag_cli.py add <file>[/warning]")
            return
        if args[1] == "all":
            add_all_docs()
        else:
            add_document(args[1])
    elif args[0] == "progress":
        show_progress_display()
    elif args[0] == "sources":
        show_sources()
    elif args[0] == "chat":
        run_chat()
    else:
        console.print("[warning]Commands: add, add all, progress, sources, chat[/warning]")

if __name__ == "__main__":
    main()