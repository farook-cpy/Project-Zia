import sys
import asyncio
from engine.brain import brain_engine

class ShellCompiler:
    """
    Natural Language to Shell Compiler for Project Zia.
    Translates complex, unfamiliar human requests into exact, safe terminal pipelines
    (awk, sed, find, ffmpeg, xargs, PowerShell) tailored to the host OS.
    """
    def __init__(self):
        self.os_type = sys.platform

    async def compile_to_shell(self, natural_request: str) -> dict:
        target_shell = "PowerShell 7 / Windows" if self.os_type == "win32" else "Bash / Linux Mint / Unix"

        prompt = f"""You are Zia's precision natural-language-to-shell compiler.
Target OS / Shell: {target_shell}
User request: "{natural_request}"

Translate this request into the most efficient, idiomatic, single-line terminal command.
Use standard CLI tools (awk, sed, grep, find, ffmpeg, xargs, curl, powershell) without unnecessary wrappers.

Respond in this exact concise format:
COMMAND: <single line shell command>
SAFETY: <SAFE | CAUTION (modifies files) | DANGEROUS (deletes data)>
EXPLANATION: <1 sentence describing what each flag/pipeline step does>"""

        try:
            res = await brain_engine.think_and_reply(user_message=prompt)
            raw = res.get("text", "")
            return {
                "success": True,
                "request": natural_request,
                "output": raw,
                "mood": "F4"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

shell_compiler = ShellCompiler()

