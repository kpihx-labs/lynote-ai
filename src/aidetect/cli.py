"""Rich CLI for the local heuristic analyzer, without changing its scoring."""
import json
import sys
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typer.main import get_command

from .core import analyze_text

console = Console()
app = typer.Typer(no_args_is_help=True, add_completion=False, rich_markup_mode="rich",
                  help="[bold]Lynote[/bold] - local, explainable AI-like style risk analysis. No neural model or remote API.",
                  epilog="Explore: scan --help, compare --help, info --help. Full recursive help: --help-all. English-oriented lexical rules; scores never prove authorship.")


def _version(value: bool):
    if value:
        typer.echo(f"lynote-ai {version('lynote-ai')}")
        raise typer.Exit()


def _help_all(value: bool):
    if not value:
        return
    root_command = get_command(app)
    context = typer.Context(root_command, info_name="lynote-ai")
    typer.echo(root_command.get_help(context))
    for name, command in root_command.commands.items():
        typer.echo(command.get_help(typer.Context(command, info_name=name, parent=context)))
    raise typer.Exit()


@app.callback()
def root(
    version_flag: Annotated[bool, typer.Option("--version", callback=_version, is_eager=True,
                                      help="Installed distribution version.")] = False,
    help_all: Annotated[bool, typer.Option("--help-all", callback=_help_all, is_eager=True,
                                  help="Show every command's help, options and examples.")] = False,
):
    """Heuristics are English-oriented; non-English scores are not calibrated."""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise typer.BadParameter(f"Cannot read UTF-8 file {path}: {exc}") from exc


def _analyze(text):
    if not text.strip():
        raise typer.BadParameter("No text provided. Pass a file, --text or UTF-8 stdin.")
    start = perf_counter()
    data = analyze_text(text).to_dict()
    data["timings"] = {"analysis_seconds": round(perf_counter()-start, 6)}
    data["engine"] = "local heuristics (English-oriented lexical rules)"
    return data


def _print_human_report(data, title="Lynote analysis"):
    table = Table(title=title, show_header=False)
    for label, value in (("Score:", f"{data['score']}/100 (not a probability)"),
                         ("Verdict", data["verdict"]), ("Confidence:", data["confidence"]),
                         ("Tokens counted as words", data["word_count"]),
                         ("Local analysis", f"{data['timings']['analysis_seconds']:.4f}s")):
        table.add_row(label, str(value))
    console.print(table)
    console.print("Conclusion:", data["conclusion"], markup=False)
    signals = Table(title="All evidence signals")
    for header in ("Signal", "Value", "Weight", "Observation"):
        signals.add_column(header)
    for signal in data["signals"]:
        signals.add_row(signal["name"], f"{signal['value']:.3f}", f"{signal['weight']:.2f}", signal["note"])
    console.print(signals)
    console.print(Panel("\n".join(data["caveats"] + ["English lexical rules and ASCII word matching limit French and other languages."]), title="Caveats:"))
    for step in data["next_steps"]:
        console.print(step, markup=False)


@app.command(rich_help_panel="Analysis")
def scan(
    path: Annotated[Optional[Path], typer.Argument(help="UTF-8 file; omit to read stdin.")] = None,
    text: Annotated[Optional[str], typer.Option("--text", "-t", help="Literal prose; exclusive with PATH.", rich_help_panel="Input")] = None,
    file: Annotated[Optional[Path], typer.Option("--file", "-f", help="Explicit UTF-8 file path.", rich_help_panel="Input")] = None,
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Full JSON only on stdout.", rich_help_panel="Output")] = False,
):
    """Analyze one document without uploading text or loading model weights.

    [bold]Examples[/bold]

    lynote-ai scan essay.txt --json

    lynote-ai scan --text 'A short sample will return insufficient_text.'

    lynote-ai scan --file report.txt

    [bold]Output[/bold]: risk score, confidence, six weighted signals, caveats and
    local analysis seconds. Under roughly 80 counted words the tool abstains.
    English-oriented markers and tokenization limit French interpretation.
    """
    if sum(x is not None for x in (path, file, text)) > 1:
        raise typer.BadParameter("Choose one of PATH, --file or --text")
    source = path or file
    content = _read(source) if source else text if text is not None else sys.stdin.read()
    data = _analyze(content)
    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        _print_human_report(data, str(source or "Literal text / stdin"))


@app.command(rich_help_panel="Analysis")
def compare(
    first: Annotated[Path, typer.Argument(help="First UTF-8 document.")],
    second: Annotated[Path, typer.Argument(help="Second UTF-8 document.")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Full JSON array on stdout.")] = False,
):
    """Analyze two documents with identical unchanged heuristic rules.

    Example: lynote-ai compare first.txt second.txt --json

    Output: two complete reports and independent analysis timings. Score differences
    are descriptive and do not establish either document's provenance.
    """
    sources = [(path, _read(path)) for path in (first, second)]
    reports = [{"file": str(path), **_analyze(text)} for path, text in sources]
    if json_output:
        typer.echo(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            _print_human_report(report, report["file"])


@app.command(rich_help_panel="Reference")
def info(json_output: Annotated[bool, typer.Option("--json", help="Machine-readable engine description.")] = False):
    """Explain engine, language limitations and evidence types. No analysis runs.

    Example: lynote-ai info --json

    This CLI uses the lightweight heuristic core, NOT the separate upstream
    multilingual neural training pipeline. There are no model weights to pull.
    """
    data = {"engine": "heuristics", "neural_model": None, "network_required": False,
            "lexical_language": "en", "word_pattern": "ASCII Latin plus CJK ideographs",
            "calibrated_languages": [], "minimum_words": 80,
            "signals": ["burstiness", "formulaic_markers", "transition_density",
                        "lexical_smoothness", "structured_answer_shape", "compressibility"],
            "caveat": "Not proof of authorship; multilingual validity has not been established."}
    if json_output:
        typer.echo(json.dumps(data, indent=2))
    else:
        console.print(Panel(json.dumps(data, indent=2), title="Lynote engine"), markup=False)


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] not in {"scan", "compare", "info", "--help", "-h", "--help-all", "--version"}:
        args.insert(0, "scan")
    # Preserve historical stdin invocations without a subcommand.
    if not args and not sys.stdin.isatty():
        args = ["scan"]
    try:
        result = app(args=args, prog_name="lynote-ai", standalone_mode=True)
        return result if isinstance(result, int) else 0
    except SystemExit as exc:
        return int(exc.code or 0)


if __name__ == "__main__":
    raise SystemExit(main())
