"""Assemble one RYTV publication into PDF, HTML, and machine-readable files."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

MACHINE_SUFFIXES = {".xsd", ".json", ".ids", ".ifc", ".yaml", ".yml", ".bpmn"}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build a RYTV publication.")
    parser.add_argument("root", nargs="?", default=".", help="Publication repository root")
    args = parser.parse_args(argv)
    build(Path(args.root).resolve())


def build(root: Path) -> Path:
    config_path = root / "publication.json"
    if not config_path.is_file():
        raise SystemExit(f"missing {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    markdown = root / config["markdown"]
    if not markdown.is_file():
        raise SystemExit(f"missing markdown entry {markdown}")

    artefact = root / "artefact"
    staging = root / "staging"
    if artefact.exists():
        shutil.rmtree(artefact)
    figures = staging / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    rendered = render_mermaid(root / "diagrams", figures)
    html_dir = artefact / "html"
    html_dir.mkdir(parents=True)
    machine = artefact / "machine-readable"
    copied = copy_machine_readable(root, machine)

    title = config.get("title", "RYTV")
    resource_path = os.pathsep.join(
        [str(markdown.parent), str(figures), str(root / "figures")]
    )
    pandoc_pdf(markdown, artefact / "publication.pdf", resource_path, title, config.get("pdfFont"))
    pandoc(
        markdown,
        html_dir / "index.html",
        resource_path,
        title,
        pdf=False,
        media_dir=html_dir / "media",
    )

    index = {
        "title": title,
        "language": config.get("language", ""),
        "domain": config.get("domain", ""),
        "version": config.get("version", ""),
        "diagrams": [path.name for path in rendered],
        "machineReadable": [path.relative_to(machine).as_posix() for path in copied],
    }
    (artefact / "publication-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"built {artefact}")
    return artefact


def render_mermaid(diagrams: Path, figures: Path) -> list[Path]:
    if not diagrams.is_dir():
        return []
    sources = sorted(diagrams.glob("*.mmd"))
    if not sources:
        return []
    use_kroki = shutil.which("mmdc") is None
    if use_kroki:
        print("warning: mmdc is not installed, rendering Mermaid through kroki.io", file=sys.stderr)
    rendered = []
    for source in sources:
        target = figures / f"{source.stem}.png"
        if use_kroki:
            if not render_with_kroki(source, target):
                continue
        else:
            subprocess.run(
                ["mmdc", "-i", str(source), "-o", str(target), "-b", "transparent"],
                check=True,
            )
        rendered.append(target)
    return rendered


def render_with_kroki(source: Path, target: Path) -> bool:
    request = urllib.request.Request(
        "https://kroki.io/mermaid/png",
        data=source.read_bytes(),
        headers={"Content-Type": "text/plain", "User-Agent": "rytv-builder"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            target.write_bytes(response.read())
    except Exception as error:
        print(f"warning: could not render {source.name}: {error}", file=sys.stderr)
        return False
    return True


def copy_machine_readable(root: Path, machine: Path) -> list[Path]:
    copied: list[Path] = []
    schema = root / "schema"
    if schema.is_dir():
        for source in sorted(path for path in schema.rglob("*") if path.is_file()):
            if source.suffix.lower() not in MACHINE_SUFFIXES:
                continue
            target = machine / "schema" / source.relative_to(schema)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
    diagrams = root / "diagrams"
    if diagrams.is_dir():
        for source in sorted(diagrams.glob("*.bpmn")):
            target = machine / "bpmn" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
    return copied


def pandoc_pdf(markdown: Path, output: Path, resource_path: str, title: str, requested_font: str | None) -> None:
    preferred = ["Segoe UI", "DejaVu Sans", "Liberation Sans"] if os.name == "nt" else ["DejaVu Sans", "Liberation Sans", "Segoe UI"]
    fonts = []
    for name in ([requested_font] if requested_font else []) + preferred:
        if name and name not in fonts:
            fonts.append(name)
    last_error = None
    for font in fonts:
        try:
            pandoc(markdown, output, resource_path, title, font, pdf=True)
            return
        except subprocess.CalledProcessError as error:
            last_error = error
            print(f"warning: PDF font {font} failed, trying the next one", file=sys.stderr)
    if last_error is not None:
        raise last_error


def pandoc(
    markdown: Path,
    output: Path,
    resource_path: str,
    title: str,
    font: str = "",
    pdf: bool = False,
    media_dir: Path | None = None,
) -> None:
    command = [
        "pandoc",
        str(markdown),
        "-o",
        str(output),
        f"--resource-path={resource_path}",
        "--standalone",
        "-M",
        f"title={title}",
    ]
    if pdf:
        command += ["--pdf-engine=xelatex", "-V", f"mainfont={font}", "-V", "geometry:margin=2.2cm"]
    elif media_dir is not None:
        command += ["--extract-media", str(media_dir)]
    subprocess.run(command, check=True)
