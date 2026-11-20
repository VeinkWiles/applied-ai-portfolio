#!/usr/bin/env python3
"""Minimal agent loop that talks to LM Studio directly (no OpenClaw).

Usage (run.sh calls this when AGENT=direct):
  direct_agent.py --model qwen3.6-35b-a3b-mlx --session results/.sessions/KEY \
                  --message-file part1.md [--workdir REPO] [--timeout 5400]

The session (message history) is kept in <session>.json so later calls with the same
--session continue the conversation (multi-part tasks, fix rounds). Every request,
tool call and result is appended to <session>.jsonl for grading.

stdout: the model's final reply only. Exit codes:
  0 final reply   3 context budget reached   4 provider error   5 time or step limit
Lines starting with "HARNESS:" are written by this script, not the model.
"""
import argparse, base64, json, os, subprocess, sys, time, urllib.request, urllib.error

SHELL = "/bin/zsh" if os.path.exists("/bin/zsh") else "/bin/bash"

TOOLS = [
    {"type": "function", "function": {"name": "read", "description": "Read a text file. Returns numbered lines. Use offset/limit for large files.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "offset": {"type": "integer", "description": "first line, 1-based"},
            "limit": {"type": "integer", "description": "max lines (default 300)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write", "description": "Create a NEW file (fails if the file exists; use edit for existing files).",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                       "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit", "description": "Replace old_text with new_text in an existing file. old_text must match exactly once.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"},
                       "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}}},
    {"type": "function", "function": {"name": "exec", "description": "Run a shell command (zsh) in the repo. Returns exit code and output (long output is cut down).",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"},
                       "timeout": {"type": "integer", "description": "seconds, default 600"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "view_image", "description": "Look at a PNG or JPEG image (e.g. a render preview).",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
]

def api_key():
    """LMS_API_KEY if set, else the lmstudio key from OpenClaw's config (read at run time, never stored)."""
    k = os.environ.get("LMS_API_KEY")
    if k:
        return k
    try:
        cfg = json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))
        return cfg["models"]["providers"]["lmstudio"].get("apiKey") or "lm-studio"
    except Exception:
        return "lm-studio"

def clip(s, limit):
    if len(s) <= limit:
        return s
    head, tail = int(limit * 0.6), int(limit * 0.3)
    return s[:head] + f"\n…[{len(s) - head - tail} characters cut]…\n" + s[-tail:]

class Agent:
    def __init__(self, a):
        self.a = a
        self.workdir = os.path.abspath(a.workdir)
        self.state_path = a.session + ".json"
        self.log_path = a.session + ".jsonl"
        os.makedirs(os.path.dirname(os.path.abspath(a.session)), exist_ok=True)
        if os.path.exists(self.state_path):
            self.messages = json.load(open(self.state_path))
        else:
            self.messages = [{"role": "system", "content": open(a.system_file).read()}]

    def log(self, kind, **kw):
        with open(self.log_path, "a") as f:
            f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "kind": kind, **kw}) + "\n")

    def save(self):
        tmp = self.state_path + ".tmp"
        json.dump(self.messages, open(tmp, "w"))
        os.replace(tmp, self.state_path)

    def path(self, p):
        p = os.path.expanduser(p.strip())
        return p if os.path.isabs(p) else os.path.join(self.workdir, p)

    # ---- tools -------------------------------------------------------------
    def t_read(self, path, offset=1, limit=300):
        lines = open(self.path(path), errors="replace").read().splitlines()
        offset = max(1, int(offset or 1)); limit = max(1, min(int(limit or 300), 1000))
        chunk = lines[offset - 1: offset - 1 + limit]
        out = "\n".join(f"{i}\t{l}" for i, l in enumerate(chunk, offset))
        more = len(lines) - (offset - 1 + len(chunk))
        return out + (f"\n…[{more} more lines; {len(lines)} total]" if more > 0 else "")

    def t_write(self, path, content):
        p = self.path(path)
        if os.path.exists(p):
            return f"ERROR: {p} exists. write only creates new files; use edit to change it."
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(content)
        return f"wrote {p} ({len(content)} chars)"

    def t_edit(self, path, old_text, new_text):
        p = self.path(path); s = open(p).read(); n = s.count(old_text)
        if n != 1:
            return f"ERROR: old_text found {n} times in {p} (must be exactly once). Re-read the lines and try again."
        open(p, "w").write(s.replace(old_text, new_text))
        return f"edited {p}"

    def t_exec(self, command, timeout=600):
        timeout = max(1, min(int(timeout or 600), 3600))
        try:
            r = subprocess.run([SHELL, "-c", command], cwd=self.workdir, capture_output=True,
                               text=True, errors="replace", timeout=timeout)
            out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
            return f"exit {r.returncode}\n" + clip(out, self.a.max_tool_chars)
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            return f"TIMEOUT after {timeout}s (process killed)\n" + clip(out, self.a.max_tool_chars)

    def t_view_image(self, path):
        p = self.path(path); data = open(p, "rb").read()
        mime = "image/jpeg" if p.lower().endswith((".jpg", ".jpeg")) else "image/png"
        self.pending_images.append((p, f"data:{mime};base64," + base64.b64encode(data).decode()))
        return f"image {p} ({len(data)} bytes) is attached in the next message."

    def run_tool(self, name, args):
        fn = getattr(self, "t_" + name, None)
        if fn is None:
            return f"ERROR: unknown tool {name}"
        try:
            return fn(**args)
        except TypeError as e:
            return f"ERROR: bad arguments for {name}: {e}"
        except Exception as e:
            return f"ERROR: {type(e).__name__}: {e}"

    # ---- model -------------------------------------------------------------
    def call(self, deadline):
        body = {"model": self.a.model, "messages": self.messages, "tools": TOOLS, "max_tokens": self.a.max_tokens, "stream": False}
        self.last_chars = len(json.dumps(self.messages))
        req = urllib.request.Request(self.a.base_url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key()})
        for attempt in (1, 2):
            try:
                with urllib.request.urlopen(req, timeout=max(30, deadline - time.time())) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                raise RuntimeError(f"provider error {e.code}: {e.read().decode('utf-8', 'replace')[:600]}")
            except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
                if attempt == 2 or time.time() > deadline:
                    raise ConnectionError(f"provider unreachable: {e}")
                time.sleep(10)

    def trim_history(self, keep):
        """Shrink everything older than the last KEEP steps: long tool output becomes its first
        lines plus a note; long write/edit/exec arguments become a size note (the files are on
        disk). System and user messages are never touched. Returns characters removed."""
        steps = [i for i, m in enumerate(self.messages) if m["role"] == "assistant"]
        if len(steps) <= keep:
            return 0
        cut = steps[-keep]
        removed = 0
        for m in self.messages[:cut]:
            if m["role"] == "tool" and len(m["content"]) > 600:
                old = len(m["content"])
                m["content"] = m["content"][:300] + f"\n…[trimmed from history: {old - 300} more characters of old output; run it again if you need it]"
                removed += old - len(m["content"])
            elif m["role"] == "assistant":
                for tc in m.get("tool_calls") or []:
                    fn = tc["function"]; raw = fn.get("arguments") or ""
                    if len(raw) <= 600:
                        continue
                    try:
                        args = json.loads(raw)
                    except json.JSONDecodeError:
                        fn["arguments"] = json.dumps({"trimmed": f"{len(raw)} characters of arguments"})
                        removed += len(raw) - len(fn["arguments"]); continue
                    if not isinstance(args, dict):
                        continue
                    for k, v in list(args.items()):
                        if isinstance(v, str) and len(v) > 300:
                            note = f"[trimmed from history: {len(v)} characters]"
                            if fn["name"] == "write" and k == "content":
                                note = f"[trimmed from history: {len(v)} characters written to {args.get('path', '?')}; read the file if you need it]"
                            elif k == "command":
                                note = v[:200] + f" …[trimmed from history: {len(v) - 200} more characters]"
                            args[k] = note
                    new = json.dumps(args)
                    removed += len(raw) - len(new); fn["arguments"] = new
        return removed

    def drop_old_images(self):
        # keep only the newest image in the history; older ones become a text stub
        seen = 0
        for m in reversed(self.messages):
            if m["role"] == "user" and isinstance(m.get("content"), list) and any(c.get("type") == "image_url" for c in m["content"]):
                seen += 1
                if seen > 1:
                    m["content"] = [c for c in m["content"] if c.get("type") != "image_url"] + [{"type": "text", "text": "[older image removed]"}]

    def run(self, prompt):
        deadline = time.time() + self.a.timeout
        self.messages.append({"role": "user", "content": prompt}); self.save()
        self.log("prompt", text=prompt[:2000])
        steps = 0
        while True:
            if time.time() > deadline:
                return 5, f"HARNESS: time limit ({self.a.timeout}s) reached"
            if steps >= self.a.max_steps:
                return 5, f"HARNESS: step limit ({self.a.max_steps} model calls) reached"
            steps += 1
            t0 = time.time()
            try:
                resp = self.call(deadline)
            except ConnectionError as e:
                self.log("error", error=str(e)); return 4, f"HARNESS: {e}"
            except RuntimeError as e:
                self.log("error", error=str(e))
                msg = str(e)
                if "context length" in msg or "does not fit" in msg:
                    return 3, f"HARNESS: context full: {msg}"
                return 4, f"HARNESS: {msg}"
            usage = resp.get("usage") or {}
            choice = resp["choices"][0]; msg = choice["message"]
            calls = msg.get("tool_calls") or []
            self.log("response", secs=round(time.time() - t0, 1), prompt_tokens=usage.get("prompt_tokens"),
                     completion_tokens=usage.get("completion_tokens"), finish=choice.get("finish_reason"),
                     text=(msg.get("content") or "")[:2000], tool_calls=[c["function"]["name"] for c in calls])
            entry = {"role": "assistant", "content": msg.get("content") or ""}
            if calls:
                entry["tool_calls"] = [{"id": c["id"], "type": "function", "function": c["function"]} for c in calls]
            self.messages.append(entry)
            if not calls:
                self.save()
                if choice.get("finish_reason") == "length":
                    return 5, (msg.get("content") or "") + "\nHARNESS: reply cut off at max_tokens"
                return 0, msg.get("content") or ""
            self.pending_images = []
            for c in calls:
                name = c["function"]["name"]
                try:
                    args = json.loads(c["function"].get("arguments") or "{}")
                    result = self.run_tool(name, args) if isinstance(args, dict) else "ERROR: arguments must be a JSON object"
                except json.JSONDecodeError as e:
                    args, result = c["function"].get("arguments"), f"ERROR: arguments are not valid JSON ({e})"
                result = clip(str(result), self.a.max_tool_chars)
                self.log("tool", name=name, args=args if len(json.dumps(args)) < 4000 else "[long]", result=result[:3000])
                self.messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
            for p, url in self.pending_images:
                self.messages.append({"role": "user", "content": [{"type": "text", "text": f"view_image: {p}"},
                                                                  {"type": "image_url", "image_url": {"url": url}}]})
            self.drop_old_images()
            self.save()
            pt = usage.get("prompt_tokens") or 0
            trimmed = 0
            if pt > self.a.trim_at:
                # trim deep enough (to ~60% of trim_at) that the next trim is a while off: each trim
                # changes old messages, so LM Studio has to reprocess the whole prompt once
                ratio = pt / max(1, self.last_chars)
                for keep in sorted({self.a.keep_steps, 6, 3, 1}, reverse=True):
                    trimmed += self.trim_history(keep)
                    if len(json.dumps(self.messages)) * ratio < 0.6 * self.a.trim_at:
                        break
                if trimmed:
                    self.log("trim", prompt_tokens=pt, chars_removed=trimmed)
                    self.save()
            if pt > self.a.budget and trimmed < 4000:
                return 3, f"HARNESS: context budget reached ({pt} prompt tokens > {self.a.budget}); stopped before the provider overflows"

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--session", required=True)
    ap.add_argument("--message-file", required=True)
    ap.add_argument("--workdir", default=".", help="repository the agent may edit; run.sh passes the frozen checkout")
    ap.add_argument("--system-file", default=os.path.join(here, "..", "agent", "SYSTEM.md"))
    ap.add_argument("--base-url", default=os.environ.get("LMS_URL", "http://127.0.0.1:1234/v1"))
    ap.add_argument("--timeout", type=int, default=2400)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--budget", type=int, default=int(os.environ.get("DIRECT_BUDGET", "110000")),
                    help="stop when a request's prompt exceeds this many tokens")
    ap.add_argument("--max-steps", type=int, default=400)
    ap.add_argument("--max-tool-chars", type=int, default=12000)
    ap.add_argument("--trim-at", type=int, default=int(os.environ.get("DIRECT_TRIM_AT", "60000")),
                    help="trim old history when a request's prompt exceeds this many tokens (0 = always, huge = never)")
    ap.add_argument("--keep-steps", type=int, default=int(os.environ.get("DIRECT_KEEP_STEPS", "10")),
                    help="model steps at the end of the history that are never trimmed")
    a = ap.parse_args()
    agent = Agent(a)
    code, text = agent.run(open(a.message_file).read())
    agent.log("end", code=code, text=text[:2000])
    print(text)
    sys.exit(code)

if __name__ == "__main__":
    main()
