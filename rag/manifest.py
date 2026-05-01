from pathlib import Path
from datetime import datetime
from typing import List, Dict
import json

MANIFEST_FILE = Path(__file__).parent.parent / "data" / "learning_manifest.json"

CLEARED_TOPICS = {
    "All of Statistics (Wasserman)": {
        "cleared": True,
        "topics": ["probability", "statistical inference", "convergence", "nonparametric methods", "regression fundamentals"],
        "notes": "Consider fully cleared"
    },
    "Forecasting: Principles and Practice (Hyndman)": {
        "cleared": True,
        "topics": ["time series decomposition", "ARIMA", "ETS", "forecasting evaluation", "stationarity"],
        "notes": "Consider fully cleared"
    },
    "Pinsky & Karlin (Markov chains only)": {
        "cleared": True,
        "topics": ["Markov chains"],
        "notes": "Chapters on Markov chains only"
    }
}

REMAINING_GAPS = [
    {
        "id": 1,
        "topic": "Stochastic processes",
        "subtopics": ["Brownian motion", "Poisson processes", "martingales"],
        "resource": "Pinsky & Karlin",
        "resource_url": "N/A - textbook",
        "limit": "chapters on stochastic processes only",
        "priority": "high",
        "phase": "1-2"
    },
    {
        "id": 2,
        "topic": "Hidden Markov Models",
        "subtopics": ["Baum-Welch", "Viterbi", "emission distributions", "posterior inference"],
        "resource": "Rabiner 1989 tutorial",
        "resource_url": "https://www.cs.cmu.edu/~cga/behavior/rabiner1.pdf",
        "limit": "Full paper (~30 pages)",
        "priority": "high",
        "phase": "3",
        "analogy": "Market regime = hidden state, price behavior = observation sequence"
    },
    {
        "id": 3,
        "topic": "Market microstructure theory",
        "subtopics": ["adverse selection", "informed vs uninformed trading", "price impact", "VPIN", "Kyle Lambda"],
        "resource": "Easley 2012 VPIN + Glosten-Milgrom 1985 + Kyle 1985",
        "resource_url": [
            "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1695596",
            "N/A - classic papers"
        ],
        "limit": "VPIN paper + key sections of Glosten-Milgrom",
        "priority": "high",
        "phase": "1-2"
    },
    {
        "id": 4,
        "topic": "Granger causality and lead/lag analysis",
        "subtopics": ["causality testing", "lead/lag relationships", "sentiment vs price"],
        "resource": "Granger 1969 paper",
        "resource_url": "https://mimuw.edu.pl/~noble/courses/TimeSeries/RESOURCES/69EconometricaGrangerCausality.pdf",
        "limit": "Full paper (~10 pages)",
        "priority": "medium",
        "phase": "4"
    },
    {
        "id": 5,
        "topic": "Causal inference",
        "subtopics": ["Pearl's framework", "causal chains vs correlation", "do-calculus"],
        "resource": "The Book of Why + Causal Inference: The Mixtape",
        "resource_url": [
            "https://www.cs.uic.edu/~elm/Teaching/Book/Causal_Inference_The_Mixtape.pdf"
        ],
        "limit": "Granger chapter from mixtape + Book of Why intro",
        "priority": "medium",
        "phase": "5"
    },
    {
        "id": 6,
        "topic": "Prompt engineering for causal extraction",
        "subtopics": ["structured JSON outputs", "hallucination mitigation", "citing source sentences"],
        "resource": "Anthropic prompt engineering docs",
        "resource_url": "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview",
        "limit": "Overview + JSON structured output sections",
        "priority": "medium",
        "phase": "5"
    }
]

STUDY_SCHEDULE = {
    "Phase 1-2": {
        "focus": "Ingestion + microstructure",
        "resources": ["Easley VPIN", "Glosten-Milgrom", "Kyle 1985"],
        "status": "active"
    },
    "Phase 3": {
        "focus": "Regime detection (HMM)",
        "resources": ["Rabiner HMM tutorial"],
        "status": "pending"
    },
    "Phase 4": {
        "focus": "Alternative data (sentiment)",
        "resources": ["Granger 1969", "PRAW docs", "FRED API docs"],
        "status": "pending"
    },
    "Phase 5": {
        "focus": "LLM reasoner",
        "resources": ["Anthropic prompt engineering", "Pearl causality"],
        "status": "pending"
    }
}

def load_manifest() -> dict:
    if MANIFEST_FILE.exists():
        return json.loads(MANIFEST_FILE.read_text())
    return {
        "cleared": CLEARED_TOPICS,
        "remaining": REMAINING_GAPS,
        "schedule": STUDY_SCHEDULE,
        "history": []
    }

def save_manifest(data: dict):
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(data, indent=2))

def add_cleared_topic(topic: str, subtopics: List[str], notes: str = ""):
    data = load_manifest()
    data["cleared"][topic] = {
        "cleared": True,
        "topics": subtopics,
        "notes": notes,
        "date_cleared": datetime.now().isoformat()
    }
    save_manifest(data)

def mark_gap_completed(gap_id: int):
    data = load_manifest()
    for gap in data["remaining"]:
        if gap["id"] == gap_id:
            gap["completed"] = True
            gap["completed_date"] = datetime.now().isoformat()
    save_manifest(data)

def get_active_phase() -> str:
    data = load_manifest()
    for phase, info in data["schedule"].items():
        if info.get("status") == "active":
            return phase
    return "Phase 1-2"

def show_progress():
    data = load_manifest()
    cleared = [k for k, v in data["cleared"].items() if v.get("cleared")]
    remaining = [r for r in data["remaining"] if not r.get("completed")]
    return {
        "cleared": cleared,
        "remaining": remaining,
        "total_cleared": len(cleared),
        "total_remaining": len(remaining)
    }