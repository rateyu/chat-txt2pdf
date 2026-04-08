import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Tuple


SWIFT_EXTRACTOR = r"""import Foundation
import PDFKit

let args = Array(CommandLine.arguments.dropFirst())
guard args.count == 2 else {
    fputs("usage: pdf2txt-extractor <input.pdf> <output.txt>\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: args[0])
let outputURL = URL(fileURLWithPath: args[1])

guard let document = PDFDocument(url: inputURL) else {
    fputs("failed to open PDF: \(inputURL.path)\n", stderr)
    exit(1)
}

let extracted = document.string ?? ""
let text = extracted.isEmpty ? "[No extractable text found]\n" : extracted

do {
    let parent = outputURL.deletingLastPathComponent()
    try FileManager.default.createDirectory(at: parent, withIntermediateDirectories: true)
    try text.write(to: outputURL, atomically: true, encoding: .utf8)
} catch {
    fputs("failed to write TXT: \(error)\n", stderr)
    exit(1)
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files using macOS PDFKit via Swift."
    )
    parser.add_argument(
        "input_path",
        help="Path to a PDF file or a directory containing PDFs.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Write TXT files into this directory. Directory inputs preserve relative paths.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing TXT files.",
    )
    return parser.parse_args()


def collect_pdf_jobs(input_path: Path, output_dir: Path | None) -> List[Tuple[Path, Path]]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {input_path}")
        return [(input_path, build_output_path(input_path, input_path.parent, output_dir))]

    if not input_path.is_dir():
        raise ValueError(f"Path does not exist: {input_path}")

    pdfs = sorted(p for p in input_path.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf")
    jobs: List[Tuple[Path, Path]] = []
    for pdf_path in pdfs:
        jobs.append((pdf_path, build_output_path(pdf_path, input_path, output_dir)))
    return jobs


def build_output_path(pdf_path: Path, root_input: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        return pdf_path.with_suffix(".txt")

    if root_input.is_dir():
        rel = pdf_path.relative_to(root_input)
        return output_dir / rel.with_suffix(".txt")

    return output_dir / pdf_path.with_suffix(".txt").name


def ensure_swift_available() -> None:
    try:
        result = subprocess.run(
            ["swift", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("swift is not installed on this machine") from exc

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "swift is unavailable")


def run_extractor(swift_script: Path, pdf_path: Path, txt_path: Path) -> None:
    env = os.environ.copy()
    env.setdefault("CLANG_MODULE_CACHE_PATH", "/tmp/clang-module-cache")
    result = subprocess.run(
        ["swift", str(swift_script), str(pdf_path), str(txt_path)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown swift error"
        raise RuntimeError(message)


def render_jobs(jobs: Iterable[Tuple[Path, Path]]) -> str:
    return "\n".join(f"{pdf} -> {txt}" for pdf, txt in jobs)


def main() -> int:
    if sys.platform != "darwin":
        print("pdf2txt.py requires macOS because it uses PDFKit.", file=sys.stderr)
        return 2

    args = parse_args()
    input_path = Path(args.input_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None

    try:
        jobs = collect_pdf_jobs(input_path, output_dir)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not jobs:
        print("No PDF files found.")
        return 0

    ensure_swift_available()

    if not args.overwrite:
        jobs = [(pdf, txt) for pdf, txt in jobs if not txt.exists()]

    if not jobs:
        print("No files to extract. Use --overwrite to regenerate existing TXT files.")
        return 0

    print("Planned extractions:")
    print(render_jobs(jobs))

    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False, encoding="utf-8") as tmp:
        tmp.write(SWIFT_EXTRACTOR)
        swift_script = Path(tmp.name)

    failures: List[Tuple[Path, str]] = []
    try:
        for pdf_path, txt_path in jobs:
            try:
                run_extractor(swift_script, pdf_path, txt_path)
                print(f"[ok] {pdf_path} -> {txt_path}")
            except RuntimeError as exc:
                failures.append((pdf_path, str(exc)))
                print(f"[failed] {pdf_path}: {exc}", file=sys.stderr)
    finally:
        swift_script.unlink(missing_ok=True)

    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
