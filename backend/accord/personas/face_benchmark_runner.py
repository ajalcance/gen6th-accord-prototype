"""Owner-invoked bounded offline JSON evaluation; paths are explicit, never discovered."""

import argparse
import json
from pathlib import Path

from accord.personas.benchmark_corpus import check_corpus
from accord.personas.face_benchmark import BenchmarkManifest, BenchmarkRun, evaluate


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate benchmark JSON key")
        result[key] = value
    return result


def read_json(path: Path) -> object:
    with path.open("rb") as source:
        data = source.read(16 * 1024 * 1024 + 1)
    if len(data) > 16 * 1024 * 1024:
        raise ValueError("benchmark JSON exceeds the bound")
    return json.loads(data, object_pairs_hook=unique_object)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("observations", type=Path)
    parser.add_argument("--corpus-root", type=Path)
    args = parser.parse_args()
    manifest = BenchmarkManifest.model_validate(read_json(args.manifest))
    run = BenchmarkRun.model_validate(read_json(args.observations))
    if args.corpus_root:
        check_corpus(manifest, args.corpus_root)
    report = evaluate(manifest, run)
    if args.corpus_root:
        report["corpus_binding"] = "bytes_checked"
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
