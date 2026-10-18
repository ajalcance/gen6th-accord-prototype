"""Explicit private corpus byte preflight; permission references remain owner assertions."""

import hashlib
from pathlib import Path

from accord.personas.face_benchmark import BenchmarkManifest

MAX_ASSET_BYTES = 10 * 1024 * 1024
MAX_CORPUS_BYTES = 256 * 1024 * 1024


def check_corpus(manifest: BenchmarkManifest, root: Path) -> None:
    base = root.resolve(strict=True)
    if not base.is_dir():
        raise ValueError("corpus root must be a directory")
    consumed = 0
    for asset in manifest.assets:
        relative = Path(asset.relative_path or "")
        if not asset.relative_path or relative.is_absolute() or ".." in relative.parts:
            raise ValueError("each corpus asset requires a confined relative path")
        path = (base / relative).resolve(strict=True)
        if not path.is_relative_to(base) or not path.is_file():
            raise ValueError("corpus asset escapes its root or is not a file")
        with path.open("rb") as source:
            data = source.read(MAX_ASSET_BYTES + 1)
        consumed += len(data)
        if not data or len(data) > MAX_ASSET_BYTES or consumed > MAX_CORPUS_BYTES:
            raise ValueError("corpus byte budget exceeded or empty asset")
        if hashlib.sha256(data).hexdigest() != asset.sha256:
            raise ValueError("corpus asset digest mismatch")
