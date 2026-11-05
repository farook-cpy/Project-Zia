import asyncio
from engine.brain import brain_engine

class ErrorTracebackDebugger:
    """
    Automated Error Traceback Debugger for Project Zia.
    Intercepts terminal error dumps and pipes them straight to Gemini Flash
    for instant root cause analysis, exact patch suggestions, and executable terminal fixes.
    """
    def __init__(self):
        self.last_failed_cmd = None
        self.last_error_output = None
        self.last_returncode = None

    def record_failure(self, command: str, output: str, returncode: int):
        """Records the most recent terminal failure."""
        self.last_failed_cmd = command
        self.last_error_output = output
        self.last_returncode = returncode

    async def debug_error(self, command: str = None, error_dump: str = None) -> dict:
        """
        Analyzes the error dump via Gemini Flash and generates an actionable patch.
        """
        cmd = command or self.last_failed_cmd
        dump = error_dump or self.last_error_output

        if not dump and not cmd:
            return {
                "success": False,
                "analysis": "No recent terminal failure recorded. Run a command or specify 'debug <command>'."
            }

        prompt = f"""You are Zia's real-time error traceback debugger and systems engineer.
A terminal command failed on {brain_engine.api_key and 'host system'}.
Command executed: `{cmd or 'Unknown'}`
Terminal error dump / traceback:
```
{dump[:3000]}
```

Provide an immediate, concise, hacker-friendly diagnosis in this exact format:
- ROOT CAUSE: (1 clear sentence identifying what broke)
- EXACT FIX: (The exact terminal command or code change to resolve it)
- EXPLANATION: (1 concise sentence explaining the solution)"""

        try:
            res = await brain_engine.think_and_reply(user_message=prompt)
            return {
                "success": True,
                "command": cmd,
                "analysis": res.get("text", "Could not generate analysis."),
                "mood": "F8"
            }
        except Exception as e:
            return {
                "success": False,
                "analysis": f"Error consulting Gemini Flash: {str(e)}"
            }

error_debugger = ErrorTracebackDebugger()

