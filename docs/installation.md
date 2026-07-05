# Installation

## Requirements

- Python **3.10** or newer
- Network access to LIME Core JWKS and OAuth metadata endpoints

## PyPI

```bash
pip install lime-mcp-server-sdk
```

## Latest from GitHub

```bash
pip install git+https://github.com/Mawyxx/lime-mcp-server-sdk.git
```

## Development install

```bash
git clone https://github.com/Mawyxx/lime-mcp-server-sdk.git
cd lime-mcp-server-sdk
pip install -e ".[dev]"
```

Build documentation locally:

```bash
pip install -r docs/requirements.txt && pip install .
mkdocs serve -f docs/mkdocs.yml
```
