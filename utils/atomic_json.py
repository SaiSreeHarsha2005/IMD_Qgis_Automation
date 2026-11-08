import os
import sys
import json
import datetime

def atomic_write_json(path: str, data: dict, indent: int = 2) -> bool:
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return True
    except Exception as exc:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"  [{ts}] [atomic_json] ERROR: failed to write {os.path.basename(path)}: {exc}", file=sys.stderr, flush=True)
        return False

def read_json_safe(path: str, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return default
        return json.loads(content)
    except (json.JSONDecodeError, OSError) as exc:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"  [{ts}] [atomic_json] WARN: corrupt JSON at {os.path.basename(path)}: {exc}", file=sys.stderr, flush=True)
        tmp = path + ".tmp"
        if os.path.exists(tmp):
            try:
                with open(tmp, "r", encoding="utf-8") as f:
                    return json.loads(f.read())
            except Exception:
                pass
        return default

def merge_json_atomic(path: str, updates: dict, indent: int = 2) -> bool:
    existing = read_json_safe(path, default={})
    if not isinstance(existing, dict):
        existing = {}
    existing.update(updates)
    return atomic_write_json(path, existing, indent)
