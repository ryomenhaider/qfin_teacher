# QFin RAG Tutor

An interactive CLI tutor for learning quantitative finance through papers and docs. RAG-powered with AI explanations connected to your trading platform build.

## Who This Is For

19-year-old self-taught developer building a quantitative market intelligence platform for crypto futures traders.

## Features

- **RAG Pipeline** - Add PDFs, markdown, text files → automatic chunking → FAISS vector store
- **AI Tutor** - Chat with your knowledge base, connects concepts to your trading system
- **Progress Tracking** - Tracks cleared topics vs remaining gaps
- **Market Microstructure Focus** - Built for your specific learning path

## Installation

```bash
git clone <this-repo>
cd learning_with_ai
pip install -r requirements.txt
```

## First Run

```bash
python rag_cli.py
```

Prompts for OpenRouter API key (free). Get one at [openrouter.ai](https://openrouter.ai).

## Commands

| Command | Description |
|---------|-------------|
| `add <file>` | Add document to knowledge base |
| `progress` | Show cleared vs remaining topics |
| `sources` | List loaded documents |
| `menu` / `help` | Show commands |
| `clear` | Reset conversation |
| `exit` | Quit |

## Your Learning Path

### Cleared (tracked automatically)
- *All of Statistics* — Wasserman
- *Forecasting: Principles and Practice* — Hyndman
- Pinsky & Karlin (Markov chains only)

### Remaining Gaps (priority order)
1. Stochastic processes — Brownian motion, Poisson, martingales
2. Hidden Markov Models — Baum-Welch, Viterbi, regime detection
3. Market microstructure — VPIN, Glosten-Milgrom, Kyle Lambda
4. Granger causality — lead/lag analysis
5. Causal inference — Pearl's framework
6. Prompt engineering — structured outputs

### Study Schedule
- Phase 1-2: Ingestion + microstructure
- Phase 3: Regime detection (HMM)
- Phase 4: Alternative data (sentiment)
- Phase 5: LLM reasoner

## Adding Documents

Drop papers/docs into the `docs/` folder, then:
```bash
python rag_cli.py add docs/paper.pdf
```

Or add from anywhere:
```bash
python rag_cli.py add /path/to/rabiner_hmm.pdf
```

Supported: PDF, MD, TXT, HTML.

## How It Works

1. **Ingest** - Reads documents, chunks by sentence (~1000 chars)
2. **Embed** - Sentence-transformers (all-MiniLM-L6-v2)
3. **Store** - FAISS vector index
4. **Retrieve** - Semantic search + context building
5. **Chat** - LLM answers with your docs as context

The tutor connects concepts to your trading platform, not abstract examples.

## Requirements

- Python 3.8+
- rich, requests, numpy, matplotlib
- PyPDF2, beautifulsoup4
- sentence-transformers, faiss-cpu