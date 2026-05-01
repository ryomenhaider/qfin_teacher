#!/usr/bin/env python3
"""Rich TUI for learning stats, Markov models, and quantitative finance with code execution."""

import subprocess
import tempfile
import os
import sys
import re
import requests
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.theme import Theme
from rich.syntax import Syntax
from rich import box
from rich.rule import Rule

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "green",
    "user": "bold cyan",
    "ai": "italic yellow",
})

console = Console(theme=custom_theme)

API_BASE = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = """You are an expert tutor helping someone learn:
1. Statistics and probability theory
2. Markov chains and hidden Markov models
3. Quantitative finance (quant trading, risk management, derivatives pricing)

When the user wants to VISUALIZE something, you MUST write runnable Python code in ```python code blocks``` that:
1. Uses matplotlib/numpy
2. Shows the concept visually
3. Is self-contained and runnable
4. IMPORTANT: Put code on SEPARATE LINES from comments. Example:

```python
import numpy as np
import matplotlib.pyplot as plt

# Parameters
a, b = 0, 5
num_points = 500

# Code on separate lines
x_cont = np.linspace(a, b, num_points)
plt.show()
```

NEVER write: "# comment code here" - ALWAYS use newlines!"""

def load_config():
    config_dir = Path.home() / ".config" / "qfinance-ai"
    config_file = config_dir / "config.json"
    if config_file.exists():
        return json.loads(config_file.read_text())
    return {}

def get_api_key():
    config = load_config()
    if config.get("api_key"):
        return config["api_key"]
    console.print("[warning]No API key found. Please enter your OpenRouter API key:[/warning]")
    api_key = Prompt.ask("[user]>[/user] ").strip()
    config_dir = Path.home() / ".config" / "qfinance-ai"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({"api_key": api_key}, indent=2))
    return api_key

def show_welcome():
    console.clear()
    console.print(Panel(
        "[bold cyan]📊 QFinance Learning CLI[/bold cyan]\n\n"
        "[yellow]Learn:[/yellow] Statistics • Markov Chains • Quantitative Finance\n\n"
        "[dim]Features:[/dim] [info]Auto-visualization[/info] with matplotlib\n\n"
        "[dim]Commands:[/dim] [info]'menu'[/info] topics  [info]'clear'[/info] reset  [info]'quit'[/info] exit",
        box=box.DOUBLE,
        border_style="cyan",
        title="Welcome! 🎓",
    ))

def show_menu():
    console.print(Panel(
        "[bold cyan]📚 Learning Topics[/bold cyan]\n\n"
        "[1] [yellow]Statistics[/yellow] - Descriptive, distributions, hypothesis\n\n"
        "[2] [yellow]Probability[/yellow] - Bayes, random variables\n\n"
        "[3] [yellow]Markov Chains[/yellow] - State transitions\n\n"
        "[4] [yellow]Hidden Markov Models[/yellow] - Viterbi algorithm\n\n"
        "[5] [yellow]Quantitative Finance[/yellow] - Options, risk, VaR\n\n"
        "[6] [yellow]Code Demo[/yellow] - Python visualization examples",
        box=box.ROUNDED,
        border_style="cyan",
        title="📋 Menu",
    ))

TOPIC_PROMPTS = {
    "1": "Explain statistics: mean, median, variance, distributions (normal, uniform, etc). Give examples and ask if they want visualization.",
    "2": "Explain probability: Bayes theorem, random variables, distributions. Give examples and offer visualization.",
    "3": "Explain Markov chains: transitions, Markov property, stationary distribution. Give examples and offer visualization.",
    "4": "Explain Hidden Markov Models: states, observations, Viterbi algorithm. Give examples.",
    "5": "Explain quantitative finance: Black-Scholes, VaR, portfolio theory. Give examples and offer visualization.",
    "6": "Show me a Python visualization demonstrating a key concept (like uniform distribution, normal distribution, or random walk). Write complete runnable code with matplotlib.",
}

def extract_code(response: str) -> str | None:
    """Extract Python code from markdown response."""
    import re
    
    pattern = r'```python\s*\n(.*?)```'
    match = re.search(pattern, response, re.DOTALL)
    if match:
        code = match.group(1).strip()
        if 'import' in code or 'matplotlib' in code:
            return code
    
    pattern = r'```\s*python?\s*\n(.*?)```'
    match = re.search(pattern, response, re.DOTALL)
    if match:
        code = match.group(1).strip()
        if 'import' in code or 'matplotlib' in code:
            return code
    
    lines = response.split('\n')
    code_lines = []
    in_code = False
    indent = 0
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```python') or stripped == '```':
            in_code = not in_code
            continue
        if in_code:
            if stripped and not stripped.startswith('#') and not stripped.startswith('1️⃣') and not stripped.startswith('2️⃣'):
                code_lines.append(line)
    
    if code_lines:
        code = '\n'.join(code_lines)
        if 'import' in code:
            return code
    
    return None

def run_code(code: str) -> str:
    """Run Python code and return output."""
    import tempfile
    import subprocess
    import os
    import sys
    
    code = code.replace('plt.show()', 'plt.savefig("viz.png", dpi=100, bbox_inches="tight")\nprint("Saved to viz.png")')
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'MPLBACKEND': 'Agg'}
        )
        output = result.stdout + result.stderr
    finally:
        os.unlink(temp_file)
    
    return output if output else "Visualization saved to viz.png"

def show_code_output(code: str, output: str):
    """Show code and its output."""
    console.print(Rule("[bold cyan]📊 Code & Visualization[/bold cyan]", style="cyan"))
    
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    if "error" in output.lower() or "traceback" in output.lower():
        console.print(Panel(output, title="❌ Error", border_style="red", box=box.ROUNDED))
    else:
        console.print(Panel(output[:2000], title="✅ Output", border_style="green", box=box.ROUNDED))

def chat():
    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://qfinance-ai.local",
        "X-Title": "QFinance AI"
    }
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    show_welcome()
    
    while True:
        console.print()
        user_input = Prompt.ask("[user]You[/user]").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() in ["exit", "quit", "q"]:
            console.print("[success]Goodbye! Keep learning! 📈[/success]")
            break
            
        if user_input.lower() == "clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            show_welcome()
            continue
            
        if user_input.lower() == "menu":
            show_menu()
            continue
            
        if user_input in TOPIC_PROMPTS:
            user_input = TOPIC_PROMPTS[user_input]
            console.print(f"[dim]→ Topic selected[/dim]")
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            console.print("[dim]Thinking...[/dim]", end="\r")
            
            resp = requests.post(
                f"{API_BASE}/chat/completions",
                headers=headers,
                json={
                    "model": "openrouter/free",
                    "messages": messages
                },
                timeout=120
            )
            
            console.print("", end="\r")
            
            if resp.status_code != 200:
                console.print(f"[danger]Error {resp.status_code}: {resp.text}[/danger]")
                messages.pop()
                continue
            
            result = resp.json()
            assistant_msg = result["choices"][0]["message"]["content"]
            messages.append({"role": "assistant", "content": assistant_msg})
            
            console.print()
            md = Markdown(assistant_msg)
            console.print(Panel(md, box=box.ROUNDED, border_style="yellow", title="AI"))
            
            code = extract_code(assistant_msg)
            if code:
                should_run = Prompt.ask(
                    "[cyan]Run visualization?[/cyan] ([green]y[/green]/[red]n[/red])",
                    default="y"
                ).lower()
                
                if should_run.startswith("y"):
                    console.print("\n[dim]Running code...[/dim]")
                    output = run_code(code)
                    show_code_output(code, output)
            
            console.print()
            
        except requests.exceptions.Timeout:
            console.print("[warning]Request timed out. Try again.[/warning]")
            messages.pop()
        except Exception as e:
            console.print(f"[danger]Error: {e}[/danger]")
            messages.pop()
    
    return messages[1:]

if __name__ == "__main__":
    chat()