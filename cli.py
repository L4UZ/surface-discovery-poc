#!/usr/bin/env python3
"""CLI interface for Surface Discovery"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from discovery.core import run_discovery
from discovery.config import get_config
from discovery.utils.logger import setup_logger
from discovery.utils.helpers import sanitize_filename
from discovery.utils.auth_parser import AuthConfigParser
from discovery.stages.authenticated import AuthenticatedDiscovery

console = Console()


@click.command()
@click.option(
    '--url',
    required=False,
    help='Target URL or domain to discover (e.g., https://example.com or example.com)'
)
@click.option(
    '--output',
    type=click.Path(),
    help='Output file path (default: discovery_<domain>.json)'
)
@click.option(
    '--depth',
    type=click.Choice(['shallow', 'normal', 'deep'], case_sensitive=False),
    default='normal',
    help='Discovery depth level (default: normal)'
)
@click.option(
    '--timeout',
    type=int,
    help='Maximum execution time in seconds (default: 600)'
)
@click.option(
    '--parallel',
    type=int,
    help='Maximum parallel tasks (default: 10)'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Enable verbose logging'
)
@click.option(
    '--check-tools',
    is_flag=True,
    help='Check if required tools are installed and exit'
)
@click.option(
    '--auth-mode',
    is_flag=True,
    help='Enable authenticated discovery mode (requires --auth-config)'
)
@click.option(
    '--auth-config',
    type=click.Path(exists=True),
    help='Path to YAML authentication configuration file'
)
@click.option(
    '--skip-vuln-scan',
    is_flag=True,
    help='Skip vulnerability scanning stage (Stage 5)'
)
def main(
    url: str,
    output: Optional[str],
    depth: str,
    timeout: Optional[int],
    parallel: Optional[int],
    verbose: bool,
    check_tools: bool,
    auth_mode: bool,
    auth_config: Optional[str],
    skip_vuln_scan: bool
):
    """Surface Discovery - In-depth web attack surface discovery service

    Example usage:

        python cli.py --url example.com --output results.json

        python cli.py --url https://example.com --depth deep --verbose
    """
    # Setup logger
    logger = setup_logger('cli', verbose=verbose)

    # Check tools mode
    if check_tools:
        asyncio.run(check_dependencies())
        return

    # Validate URL is provided for normal operation
    if not url:
        console.print("[bold red]Error:[/bold red] --url is required (unless using --check-tools)")
        sys.exit(1)

    # Validate auth-mode parameters
    if auth_mode and not auth_config:
        console.print("[bold red]Error:[/bold red] --auth-config is required when using --auth-mode")
        sys.exit(1)

    # Display banner
    display_banner()

    try:
        # Build config overrides
        config_overrides = {}
        if timeout:
            config_overrides['timeout'] = timeout
        if parallel:
            config_overrides['parallel'] = parallel
        if verbose:
            config_overrides['verbose'] = verbose
        if skip_vuln_scan:
            config_overrides['skip_vuln_scan'] = skip_vuln_scan

        # Handle authenticated discovery mode
        if auth_mode:
            result = asyncio.run(run_authenticated_discovery(
                url,
                auth_config,
                depth,
                verbose,
                **config_overrides
            ))
        else:
            # Run normal discovery
            console.print(f"\n[bold cyan]Target:[/bold cyan] {url}")
            console.print(f"[bold cyan]Depth:[/bold cyan] {depth}")
            console.print(f"[bold cyan]Starting discovery...[/bold cyan]\n")

            result = asyncio.run(run_discovery(url, depth, **config_overrides))

        # Generate output filename if not provided
        if not output:
            domain = result.metadata.target
            safe_domain = sanitize_filename(domain)
            output = f"discovery_{safe_domain}.json"

        # Save results
        output_path = Path(output)
        with output_path.open('w') as f:
            json.dump(result.model_dump(mode='json'), f, indent=2, default=str)

        console.print(f"\n[bold green]✓[/bold green] Results saved to: {output_path.absolute()}\n")

        # Display summary
        display_summary(result)

        sys.exit(0)

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Discovery interrupted by user[/bold yellow]")
        sys.exit(130)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


def display_banner():
    """Display ASCII banner"""
    banner = """
[bold cyan]
╔═══════════════════════════════════════════╗
║     Surface Discovery                     ║
║     Web Attack Surface Reconnaissance     ║
╚═══════════════════════════════════════════╝
[/bold cyan]
    """
    rprint(banner)


def display_summary(result):
    """Display discovery summary

    Args:
        result: DiscoveryResult object
    """
    # Create statistics table
    table = Table(title="Discovery Summary", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")

    stats = result.statistics

    table.add_row("Total Subdomains", str(stats.total_subdomains))
    table.add_row("Live Services", str(stats.live_services))
    table.add_row("Technologies Detected", str(stats.technologies_detected))
    table.add_row("Endpoints Discovered", str(stats.endpoints_discovered))
    table.add_row("", "")  # Spacer

    # Findings by severity
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = stats.findings_by_severity.get(severity, 0)
        if count > 0:
            color = {
                'critical': 'bold red',
                'high': 'red',
                'medium': 'yellow',
                'low': 'blue',
                'info': 'white'
            }[severity]
            table.add_row(f"{severity.capitalize()} Findings", f"[{color}]{count}[/{color}]")

    console.print(table)

    # Metadata
    duration = result.metadata.duration_seconds or 0
    console.print(f"\n[bold]Scan ID:[/bold] {result.metadata.scan_id}")
    console.print(f"[bold]Duration:[/bold] {duration:.2f} seconds")
    console.print(f"[bold]Completeness:[/bold] {stats.coverage_completeness:.1%}\n")


async def run_authenticated_discovery(
    url: str,
    auth_config_path: str,
    depth: str,
    verbose: bool,
    **config_overrides
):
    """Run authenticated discovery with auth config

    Args:
        url: Target URL requiring authentication
        auth_config_path: Path to YAML auth configuration
        depth: Discovery depth
        verbose: Verbose logging
        **config_overrides: Additional configuration overrides

    Returns:
        Combined DiscoveryResult with authenticated endpoints added
    """
    from discovery.models import DiscoveryResult, DiscoveryMetadata, DiscoveryStage

    # Parse auth config
    parser = AuthConfigParser(auth_config_path)
    auth_configuration = parser.load()

    # Find auth config for target URL
    auth_for_url = parser.get_auth_for_url(url)
    if not auth_for_url:
        console.print(f"[bold red]Error:[/bold red] No authentication config found for URL: {url}")
        console.print("[yellow]Check your auth config file for matching URL[/yellow]")
        sys.exit(1)

    console.print(f"\n[bold cyan]Target:[/bold cyan] {url}")
    console.print(f"[bold cyan]Depth:[/bold cyan] {depth}")
    console.print(f"[bold cyan]Mode:[/bold cyan] Authenticated Discovery")
    console.print(f"[bold cyan]Auth Config:[/bold cyan] {auth_config_path}")
    console.print(f"[bold cyan]Starting discovery...[/bold cyan]\n")

    # Step 1: Run normal discovery first
    console.print("[bold]Stage 1-4:[/bold] Running standard discovery...")
    result = await run_discovery(url, depth, **config_overrides)

    # Step 2: Run authenticated discovery as additional layer
    console.print(f"\n[bold]Stage 5:[/bold] Running authenticated discovery...")
    config = get_config(depth, **config_overrides)
    auth_discovery = AuthenticatedDiscovery(config)

    try:
        auth_results = await auth_discovery.run(url, auth_for_url)

        # Add authenticated endpoints to result
        result.endpoints.extend(auth_results.endpoints)

        # Update statistics
        result.update_statistics()

        # Add timeline event
        result.add_timeline_event(
            DiscoveryStage.COMPLETED,
            "Authenticated discovery completed",
            {
                "authenticated_endpoints": auth_results.authenticated_endpoints,
                "path_parameters": len(auth_results.path_parameters),
                "unique_paths": len(auth_results.unique_paths)
            }
        )

        console.print(
            f"[bold green]✓[/bold green] Authenticated discovery complete: "
            f"{auth_results.authenticated_endpoints} endpoints, "
            f"{len(auth_results.path_parameters)} path parameters"
        )

    except Exception as e:
        console.print(f"[bold red]Authenticated discovery failed:[/bold red] {e}")
        if verbose:
            console.print_exception()

    return result


async def check_dependencies():
    """Check if required tools are installed"""
    from discovery.tools.runner import ToolRunner

    console.print("\n[bold cyan]Checking required tools...[/bold cyan]\n")

    runner = ToolRunner()
    results = await runner.check_dependencies()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Tool", style="cyan")
    table.add_column("Status", justify="center")

    for tool, available in sorted(results.items()):
        status = "[green]✓ Installed[/green]" if available else "[red]✗ Missing[/red]"
        table.add_row(tool, status)

    console.print(table)

    missing = [tool for tool, available in results.items() if not available]
    if missing:
        console.print(f"\n[bold yellow]Missing tools:[/bold yellow] {', '.join(missing)}")
        console.print("\n[bold]Installation instructions:[/bold]")
        console.print("go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
        console.print("go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest")
        console.print("go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest")
        console.print("go install -v github.com/projectdiscovery/katana/cmd/katana@latest")
        console.print("go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest")
        console.print("go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest\n")
        sys.exit(1)
    else:
        console.print("\n[bold green]✓ All required tools are installed![/bold green]\n")


if __name__ == '__main__':
    main()
