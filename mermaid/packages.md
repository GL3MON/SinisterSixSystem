# Required Python Packages

## Core Packages

### 1. mmdc (v0.4.0)
- **Purpose**: Mermaid diagram converter - converts Mermaid syntax to PNG images
- **Install**: `pip install mmdc`
- **Usage**: Used in `mermaid.py` to render flowcharts

### 2. google-generativeai (v0.8.6+)
- **Purpose**: Google Gemini API client for LLM-based flowchart generation
- **Install**: `pip install google-generativeai`
- **Usage**: Used in `llm_graph_generator.py` for AI-powered flowchart generation
- **Dependencies**: Automatically installs:
  - google-ai-generativelanguage
  - google-api-core
  - google-api-python-client
  - google-auth
  - protobuf
  - And other required dependencies

## Installation

Install all required packages:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install mmdc
pip install google-generativeai
```

## Package List

To see all installed packages:

```bash
pip list
```

## Requirements File

The `requirements.txt` file contains:
```
mmdc>=0.4.0
google-generativeai>=0.8.0
```

## Note

- **mmdc** is required for all flowchart generation (with or without LLM)
- **google-generativeai** is only required if using the `--llm` flag for AI-powered generation
- Without LLM, the code uses local template-based generation
