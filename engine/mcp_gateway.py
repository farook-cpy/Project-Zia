import os
import json
import re
from pathlib import Path

class MCPGateway:
    """
    Structured Model Context Protocol (MCP) Gateway.
    Implements JSON-RPC 2.0 schemas to bypass screenshot arrays for reading
    raw text, source code, and log files with 100% precision and zero token bloating.
    """
    def __init__(self, workspace_root: Path = None):
        self.workspace_root = workspace_root or Path.cwd()

    def handle_jsonrpc(self, request_str: str) -> str:
        """
        Processes standard JSON-RPC 2.0 requests.
        """
        try:
            req = json.loads(request_str)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "tools/list":
                result = self.list_tools()
            elif method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments", {})
                result = self.call_tool(name, arguments)
            else:
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not found."}
                })

            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            })
        except Exception as e:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            })

    def list_tools(self) -> dict:
        return {
            "tools": [
                {
                    "name": "read_file",
                    "description": "Reads raw contents of a text/code file with exact precision without screenshot downscaling.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Absolute or relative file path."},
                            "start_line": {"type": "integer", "default": 1},
                            "max_lines": {"type": "integer", "default": 200}
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "list_directory",
                    "description": "Lists contents of a directory in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "default": "."}
                        }
                    }
                },
                {
                    "name": "search_code",
                    "description": "Searches for regex or keywords across code and log files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "directory": {"type": "string", "default": "."}
                        },
                        "required": ["query"]
                    }
                }
            ]
        }

    def call_tool(self, name: str, args: dict) -> dict:
        if name == "read_file":
            return self.read_file(args.get("path"), args.get("start_line", 1), args.get("max_lines", 200))
        elif name == "list_directory":
            return self.list_directory(args.get("path", "."))
        elif name == "search_code":
            return self.search_code(args.get("query"), args.get("directory", "."))
        else:
            return {"error": f"Unknown MCP tool: {name}"}

    def read_file(self, file_path: str, start_line: int = 1, max_lines: int = 200) -> dict:
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace_root / path

        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        if not path.is_file():
            return {"error": f"Path is not a file: {file_path}"}

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            start_idx = max(0, start_line - 1)
            selected = lines[start_idx : start_idx + max_lines]
            content = "".join(selected)

            return {
                "path": str(path),
                "total_lines": total_lines,
                "start_line": start_line,
                "lines_returned": len(selected),
                "content": content
            }
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    def list_directory(self, dir_path: str = ".") -> dict:
        path = Path(dir_path)
        if not path.is_absolute():
            path = self.workspace_root / path

        if not path.exists():
            return {"error": f"Directory not found: {dir_path}"}

        try:
            items = []
            for item in sorted(path.iterdir()):
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None
                })
            return {"path": str(path), "items": items}
        except Exception as e:
            return {"error": f"Failed to list directory: {str(e)}"}

    def search_code(self, query: str, dir_path: str = ".") -> dict:
        path = Path(dir_path)
        if not path.is_absolute():
            path = self.workspace_root / path

        matches = []
        try:
            for root, dirs, files in os.walk(path):
                # Skip hidden folders & caches
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__", "venv"]]
                for file in files:
                    if file.endswith((".py", ".js", ".html", ".css", ".md", ".json", ".txt", ".sh", ".bat")):
                        fp = Path(root) / file
                        try:
                            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                                for line_no, line in enumerate(f, 1):
                                    if query.lower() in line.lower():
                                        matches.append({
                                            "file": str(fp.relative_to(self.workspace_root)),
                                            "line": line_no,
                                            "text": line.strip()[:150]
                                        })
                                        if len(matches) >= 30:
                                            return {"matches": matches, "truncated": True}
                        except Exception:
                            pass
            return {"matches": matches, "truncated": False}
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

mcp_gateway = MCPGateway()

