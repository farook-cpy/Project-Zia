"""
Project Zia - LifeDesk Database Bridge (engine/lifedesk_bridge.py)
Direct SQLite connector linking Zia to LifeDesk databases (habits.db & finance.db)
for natural language habit logging and expense/income tracking with zero cloud dependencies.

100% Local, private, zero third-party cloud data storage.
"""

import os
import re
import time
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LIFEDESK_DIR = DATA_DIR / "lifedesk"
LIFEDESK_DIR.mkdir(parents=True, exist_ok=True)

HABITS_DB = Path(os.environ.get("LIFEDESK_HABITS_DB", str(LIFEDESK_DIR / "habits.db")))
FINANCE_DB = Path(os.environ.get("LIFEDESK_FINANCE_DB", str(LIFEDESK_DIR / "finance.db")))


class LifeDeskBridge:
    """Coordinates local SQLite syncing with LifeDesk productivity & personal finance databases."""

    @contextmanager
    def _conn(self, db_path: Path):
        """Context manager ensuring connection is always committed and closed cleanly."""
        conn = sqlite3.connect(str(db_path))
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def __init__(self):
        self._init_databases()

    def _init_databases(self):
        """Initializes tables for habits and financial ledgers if they do not exist with SQLite WAL acceleration."""
        # 1. Habits Database
        with self._conn(HABITS_DB) as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA temp_store = MEMORY;")
            conn.execute("PRAGMA cache_size = 10000;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT DEFAULT 'general',
                    target_per_day REAL DEFAULT 1.0,
                    unit TEXT DEFAULT 'times',
                    created_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS habit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER,
                    habit_name TEXT,
                    value REAL DEFAULT 1.0,
                    note TEXT,
                    date TEXT NOT NULL,
                    timestamp REAL,
                    FOREIGN KEY(habit_id) REFERENCES habits(id)
                )
            """)

        # Seed default core habits if empty
        with self._conn(HABITS_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM habits")
            if cur.fetchone()[0] == 0:
                now_ts = time.time()
                defaults = [
                    ("Coding", "development", 2.0, "hours", now_ts),
                    ("Deep Work", "focus", 3.0, "hours", now_ts),
                    ("Workout", "health", 45.0, "mins", now_ts),
                    ("Reading", "learning", 20.0, "pages", now_ts),
                    ("Prayer", "faith", 5.0, "prayers", now_ts),
                    ("Hydration", "health", 2.5, "liters", now_ts)
                ]
                cur.executemany(
                    "INSERT INTO habits (name, category, target_per_day, unit, created_at) VALUES (?, ?, ?, ?, ?)",
                    defaults
                )

        # 2. Personal Finance Database
        with self._conn(FINANCE_DB) as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA temp_store = MEMORY;")
            conn.execute("PRAGMA cache_size = 10000;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    note TEXT,
                    date TEXT NOT NULL,
                    timestamp REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS income (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    source TEXT NOT NULL,
                    note TEXT,
                    date TEXT NOT NULL,
                    timestamp REAL
                )
            """)

    # =========================================================================
    # Habit Tracking Methods
    # =========================================================================
    def log_habit(self, habit_name: str, value: float = 1.0, note: str = "") -> Dict[str, Any]:
        """Logs completion or progress for a habit on today's date."""
        today_str = date.today().isoformat()
        now_ts = time.time()
        clean_name = habit_name.strip()

        with self._conn(HABITS_DB) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Find or auto-create habit
            cur.execute("SELECT id, name, unit FROM habits WHERE LOWER(name) = LOWER(?)", (clean_name,))
            row = cur.fetchone()
            if row:
                habit_id = row["id"]
                canonical_name = row["name"]
                unit = row["unit"]
            else:
                cur.execute(
                    "INSERT INTO habits (name, category, target_per_day, unit, created_at) VALUES (?, 'custom', 1.0, 'times', ?)",
                    (clean_name.capitalize(), now_ts)
                )
                habit_id = cur.lastrowid
                canonical_name = clean_name.capitalize()
                unit = "times"

            cur.execute(
                "INSERT INTO habit_logs (habit_id, habit_name, value, note, date, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (habit_id, canonical_name, value, note, today_str, now_ts)
            )

        streak_info = self.get_habit_streak(canonical_name)
        return {
            "success": True,
            "habit": canonical_name,
            "value": value,
            "unit": unit,
            "streak_days": streak_info["streak"],
            "date": today_str,
            "message": f"Logged {value} {unit} for '{canonical_name}'. Current streak: {streak_info['streak']} days."
        }

    def get_habit_streak(self, habit_name: str) -> Dict[str, Any]:
        """Calculates consecutive daily streak for a specific habit."""
        with self._conn(HABITS_DB) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT date FROM habit_logs
                WHERE LOWER(habit_name) = LOWER(?)
                ORDER BY date DESC
            """, (habit_name.strip(),))
            rows = [r[0] for r in cur.fetchall()]

        if not rows:
            return {"habit": habit_name, "streak": 0, "total_days": 0}

        today = date.today()
        yesterday = today - timedelta(days=1)
        streak = 0
        current_check = today

        # If not logged today, check if logged yesterday to keep streak alive
        if rows[0] != today.isoformat() and rows[0] != yesterday.isoformat():
            return {"habit": habit_name, "streak": 0, "total_days": len(rows), "last_logged": rows[0]}

        if rows[0] == today.isoformat():
            current_check = today
        else:
            current_check = yesterday

        date_set = set(rows)
        while current_check.isoformat() in date_set:
            streak += 1
            current_check -= timedelta(days=1)

        return {
            "habit": habit_name,
            "name": habit_name,
            "streak": streak,
            "current_streak": streak,
            "longest_streak": streak,
            "total_days": len(rows),
            "last_logged": rows[0],
            "logged_today": (rows[0] == today.isoformat())
        }

    def get_all_habit_streaks(self) -> List[Dict[str, Any]]:
        """Returns streak analysis across all registered habits."""
        with self._conn(HABITS_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, unit, category FROM habits ORDER BY name ASC")
            habits = cur.fetchall()

        results = []
        for h_name, unit, cat in habits:
            info = self.get_habit_streak(h_name)
            info["unit"] = unit
            info["category"] = cat
            results.append(info)
        return results

    # =========================================================================
    # Financial Ledger Methods (Expenses & Income)
    # =========================================================================
    def log_expense(self, amount: float, category: str = "general", note: str = "", tx_type: str = "expense") -> Dict[str, Any]:
        """Records an expense entry into local finance.db."""
        if tx_type == "income":
            return self.log_income(amount, source=category, note=note)

        today_str = date.today().isoformat()
        now_ts = time.time()
        clean_cat = category.strip().lower() or "general"

        with self._conn(FINANCE_DB) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO expenses (amount, category, note, date, timestamp) VALUES (?, ?, ?, ?, ?)",
                (amount, clean_cat, note, today_str, now_ts)
            )
            expense_id = cur.lastrowid

        today_total = self.get_daily_expense_total()
        return {
            "success": True,
            "id": expense_id,
            "amount": amount,
            "category": clean_cat,
            "note": note,
            "date": today_str,
            "today_total": today_total,
            "message": f"Recorded expense of Rs. {amount:.2f} ({clean_cat}). Today's total: Rs. {today_total:.2f}"
        }

    def log_income(self, amount: float, source: str = "general", note: str = "") -> Dict[str, Any]:
        """Records an income credit entry into local finance.db."""
        today_str = date.today().isoformat()
        now_ts = time.time()

        with self._conn(FINANCE_DB) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO income (amount, source, note, date, timestamp) VALUES (?, ?, ?, ?, ?)",
                (amount, source.strip().lower(), note, today_str, now_ts)
            )

        return {
            "success": True,
            "amount": amount,
            "source": source,
            "date": today_str,
            "message": f"Recorded income of Rs. {amount:.2f} from '{source}'."
        }

    def get_daily_expense_total(self, target_date: Optional[str] = None) -> float:
        """Returns total spent on a given date (defaults to today)."""
        d_str = target_date or date.today().isoformat()
        with self._conn(FINANCE_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT SUM(amount) FROM expenses WHERE date = ?", (d_str,))
            total = cur.fetchone()[0]
            return float(total) if total else 0.0

    def get_monthly_summary(self, year_month: Optional[str] = None) -> Dict[str, Any]:
        """Generates category-wise expense breakdown for the active month (YYYY-MM)."""
        ym = year_month or date.today().strftime("%Y-%m")
        with self._conn(FINANCE_DB) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT category, SUM(amount), COUNT(*) 
                FROM expenses 
                WHERE date LIKE ? 
                GROUP BY category 
                ORDER BY SUM(amount) DESC
            """, (f"{ym}%",))
            rows = cur.fetchall()

            cur.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{ym}%",))
            total_expense = cur.fetchone()[0] or 0.0

            cur.execute("SELECT SUM(amount) FROM income WHERE date LIKE ?", (f"{ym}%",))
            total_income = cur.fetchone()[0] or 0.0

        breakdown = [{"category": r[0], "total": round(r[1], 2), "count": r[2]} for r in rows]
        return {
            "month": ym,
            "total_expenses": round(total_expense, 2),
            "total_income": round(total_income, 2),
            "net_savings": round(total_income - total_expense, 2),
            "breakdown": breakdown
        }

    def list_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves latest expense transactions."""
        with self._conn(FINANCE_DB) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cur.fetchall()]

    # =========================================================================
    # Natural Language Sentence Parser
    # =========================================================================
    def parse_natural_language(self, user_text: str) -> Optional[Dict[str, Any]]:
        """
        Interprets natural language queries related to habits and finances:
        - "logged 45 min workout"
        - "spent 250 on groceries" / "paid 50 for coffee"
        - "show today's expenses" / "how much did I spend today"
        - "habit streaks" / "show habits"
        """
        text = user_text.lower().strip().rstrip(".!?")

        # 1. Expense patterns: e.g. "spent 250 on food", "paid 40 for uber", "bought coffee for 15"
        # Also matches "log 150 rupees for lunch under food"
        log_exp_match = re.search(r"(?:log|record|add)\s*(?:₹|\$|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:rupees|rs|inr|dollars)?\s*(?:for|on)?\s*([a-z0-9_\s]+?)(?:\s+under\s+([a-z0-9_]+))?$", text)
        if log_exp_match and not any(k in text for k in ["habit", "workout", "reading", "coding"]):
            amount = float(log_exp_match.group(1))
            desc = log_exp_match.group(2).strip()
            cat = (log_exp_match.group(3) or desc.split()[-1] if log_exp_match.group(3) else "food" if "lunch" in desc or "dinner" in desc or "food" in desc else "general").strip()
            res = self.log_expense(amount, category=cat, note=desc)
            return {"type": "expense_logged", "result": res}

        expense_match = re.search(r"(?:spent|paid|bought|expense of)\s*(?:₹|\$|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:on|for)\s*([a-z0-9_\s]+)", text)
        if expense_match:
            amount = float(expense_match.group(1))
            cat = expense_match.group(2).strip()
            # Clean trailing words
            cat = re.sub(r"\b(today|yesterday|just now)\b", "", cat).strip()
            res = self.log_expense(amount, category=cat, note=user_text)
            return {"type": "expense_logged", "result": res}

        # Alt expense pattern: "spent on groceries 200"
        expense_match_alt = re.search(r"(?:spent|paid)\s*(?:on|for)\s*([a-z0-9_\s]+)\s*(?:₹|\$|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)", text)
        if expense_match_alt:
            cat = expense_match_alt.group(1).strip()
            amount = float(expense_match_alt.group(2))
            res = self.log_expense(amount, category=cat, note=user_text)
            return {"type": "expense_logged", "result": res}

        # 2. Daily/Monthly Expense Query: "how much did i spend", "show expenses"
        if any(k in text for k in ["how much did i spend", "show expenses", "today's expenses", "todays expenses", "daily expenses"]):
            total = self.get_daily_expense_total()
            txs = self.list_recent_transactions(5)
            return {
                "type": "expense_query",
                "result": {
                    "today_total": total,
                    "recent_count": len(txs),
                    "recent": txs,
                    "message": f"You have spent Rs. {total:.2f} today across {len(txs)} recorded transactions."
                }
            }

        if any(k in text for k in ["monthly summary", "monthly expenses", "finance summary", "how much spent this month"]):
            summary = self.get_monthly_summary()
            return {
                "type": "monthly_summary",
                "result": summary
            }

        # 3. Habit Log patterns: "logged 45 min workout", "completed prayer", "finished reading 20 pages"
        # Also matches "mark my morning workout and reading habit as done"
        mark_habit_match = re.search(r"mark\s+(?:my\s+)?([a-z0-9_\s]+?)\s*(?:habit|habits)?\s*as\s*(?:done|completed)", text)
        if mark_habit_match:
            raw_habits = mark_habit_match.group(1).replace("morning", "").strip()
            habit_names = [h.strip() for h in re.split(r"\band\b|,", raw_habits) if h.strip()]
            results = []
            for h in habit_names:
                h_clean = re.sub(r"\b(habit|my)\b", "", h).strip()
                if h_clean:
                    r = self.log_habit(h_clean, value=1.0, note="Marked as done via natural language")
                    results.append(r)
            if results:
                habits_str = ", ".join([r.get("habit", "") for r in results])
                return {
                    "type": "habit_logged",
                    "result": {
                        "success": True,
                        "habit": habits_str,
                        "habits": results,
                        "message": f"Marked {habits_str} as done in LifeDesk."
                    }
                }

        habit_match = re.search(r"(?:logged|completed|finished|did)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:min|mins|hours?|pages?|times?)?\s*(?:of\s*)?([a-z0-9_\s]+)", text)
        if habit_match:
            val = float(habit_match.group(1))
            h_name = habit_match.group(2).strip()
            # Clean trailing noise
            h_name = re.sub(r"\b(today|habit|session)\b", "", h_name).strip()
            if h_name:
                res = self.log_habit(h_name, value=val, note=user_text)
                return {"type": "habit_logged", "result": res}

        # Simple habit completion: "completed workout", "did coding"
        habit_simple = re.search(r"(?:completed|did|logged)\s*([a-z0-9_\s]+)", text)
        if habit_simple and not any(k in text for k in ["expense", "spent", "paid"]):
            h_name = habit_simple.group(1).strip()
            h_name = re.sub(r"\b(today|habit|session|task)\b", "", h_name).strip()
            if len(h_name) >= 3 and not h_name.isdigit():
                res = self.log_habit(h_name, value=1.0, note=user_text)
                return {"type": "habit_logged", "result": res}

        # 4. Habit streak queries: "show habits", "habit streaks", "how are my habits"
        if any(k in text for k in ["habit streaks", "show habits", "my habits", "habit report"]):
            streaks = self.get_all_habit_streaks()
            return {
                "type": "habit_streaks_query",
                "result": {
                    "habits": streaks,
                    "count": len(streaks)
                }
            }

        return None

    # =========================================================================
    # Compatibility & API Aliases
    # =========================================================================
    def get_financial_summary(self) -> Dict[str, Any]:
        """Alias returning monthly summary with categories dict for API convenience."""
        m = self.get_monthly_summary()
        cat_dict = {b["category"]: b["total"] for b in m.get("breakdown", [])}
        return {
            "month": m.get("month"),
            "total_expenses": m.get("total_expenses", 0.0),
            "total_income": m.get("total_income", 0.0),
            "net_balance": m.get("net_savings", 0.0),
            "categories": cat_dict,
            "breakdown": m.get("breakdown", [])
        }

    def get_habit_streaks(self) -> List[Dict[str, Any]]:
        """Alias for get_all_habit_streaks."""
        return self.get_all_habit_streaks()

    def get_daily_expenses(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Returns today's total and recent transaction records."""
        total = self.get_daily_expense_total(target_date)
        txs = self.list_recent_transactions(10)
        return {
            "date": target_date or date.today().isoformat(),
            "total": total,
            "transactions": txs
        }

    def get_monthly_breakdown(self, year_month: Optional[str] = None) -> Dict[str, Any]:
        """Alias for get_monthly_summary."""
        return self.get_monthly_summary(year_month)

    def parse_and_log_habit(self, text: str) -> Dict[str, Any]:
        """Parses natural language and logs habit."""
        res = self.parse_natural_language(text)
        if res and res.get("type") == "habit_logged":
            return res.get("result", {})
        # Fallback simple log
        clean = text.replace("log habit", "").strip()
        return self.log_habit(clean or "coding", 1.0, text)

    def parse_and_log_expense(self, text: str) -> Dict[str, Any]:
        """Parses natural language and logs expense."""
        res = self.parse_natural_language(text)
        if res and res.get("type") == "expense_logged":
            return res.get("result", {})
        return {"error": "Could not parse amount and category from sentence."}


# Global LifeDesk bridge singleton
lifedesk_bridge = LifeDeskBridge()
