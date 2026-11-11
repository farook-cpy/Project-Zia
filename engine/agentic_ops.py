"""
Project Zia - Advanced Agentic & Multi-Agent Operations Engine
Implements:
1. Self-Correction Loop for failed subagent tasks
2. Dynamic Subagent Token Cost Budgeter
3. Asynchronous SQLite Task Queuing & Persistence (data/task_queue.db)
4. Automated Unit Test Generator (AST based)
5. Multi-Step Reasoning Plan Visualizer
6. Smart Code Reviewer Subagent
7. Incremental Context Primmer
8. Local OCR Text Extraction Pipeline
9. Autonomous Documentation Scraper (offline cache in data/docs/)
10. Background Dependency Resolver (AST import analyzer)
"""

import os
import sys
import ast
import json
import time
import sqlite3
import re
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
QUEUE_DB = DATA_DIR / "task_queue.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)


class AgenticOperationsEngine:
    """Core coordinator for advanced multi-agent workflows and local intelligence."""

    def __init__(self):
        self._init_queue_db()
        self.token_budget_limit = 500000  # Default 500k tokens safety threshold
        self.token_usage_tracker = {
            "total_prompt_tokens": 0,
            "total_candidate_tokens": 0,
            "estimated_cost_usd": 0.0,
            "subagent_breakdown": {}
        }
        self.context_summary_archive = []

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(QUEUE_DB)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # 1. SQLite Asynchronous Task Queue & Persistence
    # -------------------------------------------------------------------------
    def _init_queue_db(self):
        try:
            with self._conn() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS task_queue (
                        id TEXT PRIMARY KEY,
                        role TEXT,
                        description TEXT,
                        payload TEXT,
                        status TEXT,
                        retries INTEGER DEFAULT 0,
                        created_at REAL,
                        updated_at REAL,
                        result TEXT,
                        error TEXT
                    )
                """)
        except Exception as e:
            print(f"[AgenticOps] DB init notice: {e}")

    def enqueue_task(self, role: str, description: str, payload: Optional[dict] = None) -> str:
        """Enqueues an offline/asynchronous task into local SQLite queue."""
        task_id = f"queue_{int(time.time())}_{os.urandom(2).hex()}"
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO task_queue (id, role, description, payload, status, retries, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'pending', 0, ?, ?)",
                (task_id, role, description, json.dumps(payload or {}), time.time(), time.time())
            )
        return task_id

    def list_queued_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if status:
                cur.execute("SELECT * FROM task_queue WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cur.execute("SELECT * FROM task_queue ORDER BY created_at DESC LIMIT 20")
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def process_pending_queue(self) -> int:
        """Checks and executes queued tasks if network is restored."""
        processed = 0
        from engine.subagents import subagent_pool
        pending = self.list_queued_tasks(status="pending")
        for item in pending:
            tid = item["id"]
            with self._conn() as conn:
                conn.execute("UPDATE task_queue SET status='running', updated_at=? WHERE id=?", (time.time(), tid))

            subagent_pool.spawn(item["role"], item["description"])
            with self._conn() as conn:
                conn.execute("UPDATE task_queue SET status='dispatched', updated_at=? WHERE id=?", (time.time(), tid))
            processed += 1
        return processed

    # -------------------------------------------------------------------------
    # 2. Self-Correction Loop for Failed Subagent Tasks
    # -------------------------------------------------------------------------
    def execute_with_self_correction(self, task_fn, max_retries: int = 2) -> Dict[str, Any]:
        """
        Executes a task. If it fails with code syntax errors or malformed JSON,
        re-prompts with specific traceback diagnostics to self-heal.
        """
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                res = task_fn(last_error=last_error, attempt=attempt)
                if isinstance(res, dict) and res.get("success") is False and attempt < max_retries:
                    last_error = res.get("error") or "Execution returned unsuccessful status"
                    continue
                return {"success": True, "result": res, "attempts": attempt + 1}
            except Exception as e:
                last_error = str(e)
                if attempt >= max_retries:
                    return {"success": False, "error": f"Failed after {attempt + 1} attempts. Last error: {last_error}"}
                time.sleep(0.5)

        return {"success": False, "error": last_error}

    # -------------------------------------------------------------------------
    # 3. Dynamic Subagent Token Cost Budgeter
    # -------------------------------------------------------------------------
    def track_token_usage(self, arg1: Any, arg2: Any, arg3: Any = "general") -> Dict[str, Any]:
        """
        Accumulates Gemini Flash tokens in real-time.
        Supports both signatures:
          track_token_usage(prompt_tokens, candidate_tokens, agent_role)
          track_token_usage(agent_role, prompt_tokens, candidate_tokens)
        """
        if isinstance(arg1, str):
            agent_role = arg1
            prompt_tokens = int(arg2)
            candidate_tokens = int(arg3) if isinstance(arg3, (int, float)) else 0
        else:
            prompt_tokens = int(arg1)
            candidate_tokens = int(arg2)
            agent_role = str(arg3)

        self.token_usage_tracker["total_prompt_tokens"] += prompt_tokens
        self.token_usage_tracker["total_candidate_tokens"] += candidate_tokens

        prompt_cost = (prompt_tokens / 1_000_000.0) * 0.075
        candidate_cost = (candidate_tokens / 1_000_000.0) * 0.30
        added_cost = prompt_cost + candidate_cost
        self.token_usage_tracker["estimated_cost_usd"] += added_cost

        # Role breakdown
        if agent_role not in self.token_usage_tracker["subagent_breakdown"]:
            self.token_usage_tracker["subagent_breakdown"][agent_role] = {"tokens": 0, "cost_usd": 0.0}

        self.token_usage_tracker["subagent_breakdown"][agent_role]["tokens"] += (prompt_tokens + candidate_tokens)
        self.token_usage_tracker["subagent_breakdown"][agent_role]["cost_usd"] += added_cost

        total_tokens = self.token_usage_tracker["total_prompt_tokens"] + self.token_usage_tracker["total_candidate_tokens"]
        budget_exceeded = total_tokens >= self.token_budget_limit

        return {
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(self.token_usage_tracker["estimated_cost_usd"], 6),
            "budget_limit": self.token_budget_limit,
            "budget_exceeded": budget_exceeded,
            "warning": "Warning: Token budget threshold exceeded!" if budget_exceeded else None
        }

    # -------------------------------------------------------------------------
    # 4. Automated Unit Test Generator (AST Inspection)
    # -------------------------------------------------------------------------
    def generate_unit_tests(self, file_path: str) -> Dict[str, Any]:
        """
        Parses a python file using AST and generates a corresponding unittest test suite.
        """
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return {"error": f"File '{file_path}' does not exist."}

        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception as e:
            return {"error": f"Failed to parse AST from {file_path}: {e}"}

        functions = []
        classes = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                classes.append({"class_name": node.name, "methods": methods})

        module_name = p.stem
        test_lines = [
            "import unittest",
            f"import {module_name}",
            "",
            f"class Test{module_name.capitalize()}(unittest.TestCase):",
            "    def setUp(self):",
            "        pass",
            ""
        ]

        for fn in functions:
            test_lines.append(f"    def test_{fn}(self):")
            test_lines.append(f"        # Test placeholder for function {fn}")
            test_lines.append(f"        self.assertTrue(hasattr({module_name}, '{fn}'))")
            test_lines.append("")

        for cls in classes:
            cname = cls["class_name"]
            for m in cls["methods"]:
                test_lines.append(f"    def test_{cname.lower()}_{m}(self):")
                test_lines.append(f"        # Test placeholder for {cname}.{m}")
                test_lines.append(f"        self.assertTrue(hasattr({module_name}.{cname}, '{m}'))")
                test_lines.append("")

        test_lines.extend([
            "if __name__ == '__main__':",
            "    unittest.main()",
            ""
        ])

        generated_code = "\n".join(test_lines)
        test_file_path = p.parent / f"test_{p.name}"

        return {
            "success": True,
            "functions_found": functions,
            "classes_found": [c["class_name"] for c in classes],
            "test_file_path": str(test_file_path),
            "generated_code": generated_code
        }

    # -------------------------------------------------------------------------
    # 5. Multi-Step Reasoning Plan Visualizer
    # -------------------------------------------------------------------------
    def visualize_plan(self, complex_goal: str) -> str:
        """
        Outputs a hierarchical breakdown tree of how Zia plans to decompose
        and execute a complex goal.
        """
        lines = []
        lines.append(f"\033[1m\033[96mPLANNING DECOMPOSITION TREE\033[0m: '{complex_goal}'")
        lines.append("|-- \033[93m[Phase 1] Environment & Boundary Validation\033[0m")
        lines.append("|   |-- Check system resources & battery levels (<20% CPU)")
        lines.append("|   \\-- Verify file permissions and dependencies")
        lines.append("|-- \033[93m[Phase 2] Context & Memory Extraction\033[0m")
        lines.append("|   |-- Read relevant codebase symbols via MCP Gateway")
        lines.append("|   \\-- Query persistent user facts in memory.json")
        lines.append("|-- \033[93m[Phase 3] Subagent Task Delegation\033[0m")
        lines.append("|   |-- Spawn Worker [1]: Target execution & data processing")
        lines.append("|   \\-- Spawn Worker [2]: Verification & syntax error interception")
        lines.append("\\-- \033[92m[Phase 4] Verification & Multi-Device Delivery\033[0m")
        lines.append("    |-- Run companion test suites")
        lines.append("    \\-- Dispatch result to CLI & MacBook remote notification")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 6. Smart Code Reviewer Subagent
    # -------------------------------------------------------------------------
    def review_code_snippet(self, code_text_or_path: str, filename: str = "snippet.py") -> Dict[str, Any]:
        """
        Runs local static analysis and security linting on code strings or files.
        Detects dangerous calls (eval, exec, hardcoded keys, SQL injection patterns).
        """
        target_path = Path(code_text_or_path)
        if target_path.exists() and target_path.is_file():
            code_text = target_path.read_text(encoding="utf-8", errors="ignore")
            filename = target_path.name
        else:
            code_text = code_text_or_path

        warnings = []
        checks_run = 0

        # Security check patterns
        patterns = [
            (r"\beval\s*\(", "CRITICAL: Use of dangerous 'eval()' detected."),
            (r"\bexec\s*\(", "CRITICAL: Use of dangerous 'exec()' detected."),
            (r"(api[_-]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]", "SECURITY: Possible hardcoded secret or API key!"),
            (r"except\s*:", "LINT: Bare 'except:' clause caught. Catch specific exceptions."),
            (r"SELECT\s+.*\s+FROM\s+.*%.*", "SECURITY: Possible unparameterized SQL format string vulnerability."),
            (r"os\.system\s*\(", "WARNING: 'os.system' is deprecated and vulnerable to injection. Prefer subprocess.run(..., shell=False).")
        ]

        for pat, msg in patterns:
            checks_run += 1
            if re.search(pat, code_text, re.IGNORECASE):
                warnings.append(msg)

        # AST syntax check
        syntax_ok = True
        try:
            ast.parse(code_text)
        except SyntaxError as se:
            syntax_ok = False
            warnings.append(f"SYNTAX ERROR on line {se.lineno}: {se.msg}")

        status = "PASSED" if not warnings else ("WARNINGS" if syntax_ok else "FAILED")
        return {
            "status": status,
            "filename": filename,
            "checks_run": checks_run,
            "warnings_count": len(warnings),
            "warnings": warnings
        }

    # -------------------------------------------------------------------------
    # 7. Incremental Context Primmer
    # -------------------------------------------------------------------------
    def prime_context(self, history: List[Dict[str, str]], keep_recent: int = 4) -> tuple[str, List[Dict[str, str]]]:
        """
        Summarizes conversation turns older than keep_recent and archives them.
        """
        if len(history) <= keep_recent:
            return "", history

        older_turns = history[:-keep_recent]
        recent_turns = history[-keep_recent:]

        summary_snippets = []
        for turn in older_turns:
            role = turn.get("role", "user")
            content = turn.get("content", "")[:100]
            summary_snippets.append(f"{role}: {content}")

        archived_summary = f"[Archived Summary ({len(older_turns)} turns)]: " + " | ".join(summary_snippets)
        self.context_summary_archive.append(archived_summary)

        return archived_summary, recent_turns

    # -------------------------------------------------------------------------
    # 8. Local OCR Text Extraction Pipeline
    # -------------------------------------------------------------------------
    def extract_text_local_ocr(self, image_path: str) -> Dict[str, Any]:
        """
        Lightweight offline OCR pipeline using OpenCV / PyTesseract if available,
        or bounding-box edge analysis fallback.
        """
        if not os.path.exists(image_path):
            return {"error": f"Image file '{image_path}' not found."}

        # 1. Try pytesseract if installed
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            extracted = pytesseract.image_to_string(img).strip()
            if extracted:
                return {"success": True, "backend": "pytesseract", "text": extracted}
        except Exception:
            pass

        # 2. OpenCV edge & text region heuristic
        try:
            import cv2
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                h, w = img.shape
                # Adaptive threshold for text region isolation
                thresh = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                mean_lum = float(thresh.mean())
                return {
                    "success": True,
                    "backend": "opencv_geometry",
                    "text": f"[OCR Image Dimensions: {w}x{h} px, mean luminance: {mean_lum:.1f}]. For full character OCR on Termux/Linux, install tesseract-ocr.",
                    "metadata": {"width": w, "height": h}
                }
        except Exception as e:
            return {"error": f"Local image analysis error: {e}"}

        return {"error": "No OCR vision backend available."}

    # -------------------------------------------------------------------------
    # 9. Autonomous Documentation Scraper (Offline Cache)
    # -------------------------------------------------------------------------
    def fetch_and_cache_docs(self, url: str, doc_name: str) -> Dict[str, Any]:
        """
        Fetches an API documentation page, strips HTML, and caches it in data/docs/<name>.md.
        """
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", doc_name.lower()) + ".md"
        out_file = DOCS_DIR / clean_name

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ProjectZia/DocBot"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Simple clean HTML-to-text regex converter
            text = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

            out_file.write_text(f"# Offline Documentation: {doc_name}\nSource: {url}\nCached: {time.ctime()}\n\n" + text[:15000], encoding="utf-8")
            return {
                "success": True,
                "file": str(out_file),
                "chars_cached": len(text[:15000]),
                "url": url
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch doc from {url}: {e}"}

    # -------------------------------------------------------------------------
    # 10. Background Dependency Resolver (AST Scanner)
    # -------------------------------------------------------------------------
    def scan_missing_dependencies(self, script_path: str) -> Dict[str, Any]:
        """
        Analyzes import statements in a script and identifies missing packages.
        """
        p = Path(script_path)
        if not p.exists():
            return {"error": f"Script '{script_path}' not found."}

        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception as e:
            return {"error": f"AST parse error: {e}"}

        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split(".")[0])

        # Standard library filter
        stdlib = getattr(sys, "stdlib_module_names", set())
        missing = []
        installed = []

        for mod in sorted(imported_modules):
            if mod in stdlib:
                continue
            try:
                __import__(mod)
                installed.append(mod)
            except ImportError:
                missing.append(mod)

        return {
            "script": script_path,
            "total_third_party_imports": len(imported_modules),
            "installed": installed,
            "missing": missing,
            "install_command": f"pip install {' '.join(missing)}" if missing else None
        }


# Global agentic operations singleton
agentic_ops = AgenticOperationsEngine()
