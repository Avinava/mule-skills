from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "skills/mule-docs/scripts/audit_documentation.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


audit = load_module(AUDIT, "audit_documentation")


class WalkTextFilesTests(unittest.TestCase):
    def test_skips_eval_results_but_keeps_other_results_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for relative in ("evals/results/run/out.json", "docs/results/page.md", "evals/case/prompt.md"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("text\n", encoding="utf-8")
            found = {path.relative_to(root).as_posix() for path in audit.walk_text_files(root)}
            self.assertEqual({"docs/results/page.md", "evals/case/prompt.md"}, found)


if __name__ == "__main__":
    unittest.main()
