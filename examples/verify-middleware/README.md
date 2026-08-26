# Sync Bearer verify (canonical)

```bash
pip install lime-mcp-server-sdk
export LIME_EXPECTED_DOMAIN=tools.example.com
python main.py
```

```python
# main.py — see main.py in this folder
```

Wire `authorize_mcp_request` into your MCP auth layer; then apply **your** ACL on `agent_id`.
