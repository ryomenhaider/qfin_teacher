# QFinance Learning CLI

An interactive CLI tool for learning statistics, Markov models, and quantitative finance with AI-powered explanations and live visualizations.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **AI Tutor** - Explains concepts via OpenRouter's free models
- **Rich TUI** - Beautiful terminal interface with markdown rendering
- **Auto-Visualization** - AI generates matplotlib code you can run instantly
- **Interactive Menu** - Topic browser for structured learning

## Installation

```bash
git clone https://github.com/yourusername/qfinance-ai.git
cd qfinance-ai
pip install -r requirements.txt
```

## Usage

```bash
python qfinance_ai.py
```

First run prompts for OpenRouter API key (free). Get one at [openrouter.ai](https://openrouter.ai).

### Commands

| Command | Description |
|---------|------------|
| `menu` | Show topic browser |
| `clear` | Reset conversation |
| `quit` | Exit |

### Example Session

```
You> show me uniform distribution
AI> [explains concept]
Run visualization? (y/n): y
[shows chart]
```

## Topics Covered

- Statistics (distributions, hypothesis testing)
- Probability theory (Bayes, random variables)
- Markov Chains
- Hidden Markov Models
- Quantitative Finance (options, risk, VaR)

## Requirements

- Python 3.8+
- rich
- requests
- numpy
- matplotlib

## License

MIT