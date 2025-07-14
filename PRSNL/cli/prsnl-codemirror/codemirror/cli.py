#!/usr/bin/env python3
"""
PRSNL CodeMirror CLI Tool

AI-powered repository intelligence for offline analysis and GitHub integration.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import click
import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON

from .analyzer import RepositoryAnalyzer
from .config import CLIConfig
from .sync import PRSNLSync

console = Console()


@click.group()
@click.pass_context
def cli(ctx):
    """PRSNL CodeMirror - AI-powered repository intelligence."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = CLIConfig()


@cli.command()
def version():
    """Show version information."""
    console.print("[bold blue]PRSNL CodeMirror CLI v1.0.0[/bold blue]")
    console.print("AI-powered repository intelligence for offline analysis and GitHub integration.")


@cli.command()
@click.argument('repo_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--depth', 
              type=click.Choice(['quick', 'standard', 'deep']), 
              default='standard',
              help='Analysis depth level')
@click.option('--output', '-o', 
              type=click.Path(file_okay=True, dir_okay=False),
              help='Output file for analysis results (JSON)')
@click.option('--upload', 
              is_flag=True,
              help='Upload results to PRSNL after analysis')
@click.option('--patterns', 
              is_flag=True,
              help='Include pattern detection in analysis')
@click.option('--insights', 
              is_flag=True,
              help='Generate AI insights from analysis')
@click.pass_context
def audit(ctx, repo_path: str, depth: str, output: Optional[str], upload: bool, patterns: bool, insights: bool):
    """Audit and analyze a repository with AI."""
    config = ctx.obj['config']
    repo_path = Path(repo_path).resolve()
    
    console.print(f"[bold blue]🔍 Auditing repository:[/bold blue] {repo_path}")
    console.print(f"[dim]Analysis depth: {depth}[/dim]")
    
    try:
        # Initialize analyzer
        analyzer = RepositoryAnalyzer(config, console)
        
        # Run analysis
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing repository...", total=None)
            
            result = asyncio.run(analyzer.analyze_repository(
                repo_path=repo_path,
                depth=depth,
                include_patterns=patterns,
                include_insights=insights
            ))
            
            progress.update(task, description="Analysis complete!")
        
        # Display results
        _display_analysis_results(result)
        
        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.write_text(json.dumps(result, indent=2, default=str))
            console.print(f"[green]✅ Results saved to:[/green] {output_path}")
        
        # Upload to PRSNL if requested
        if upload:
            if not config.prsnl_url or not config.prsnl_token:
                console.print("[red]❌ PRSNL connection not configured. Use 'prsnl-codemirror config' to set up.[/red]")
                sys.exit(1)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Uploading to PRSNL...", total=None)
                
                sync = PRSNLSync(config, console)
                upload_result = asyncio.run(sync.upload_analysis(result))
                
                if upload_result:
                    console.print(f"[green]✅ Results uploaded to PRSNL[/green]")
                    if upload_result.get('analysis_url'):
                        console.print(f"[dim]View online: {upload_result['analysis_url']}[/dim]")
                else:
                    console.print("[red]❌ Failed to upload to PRSNL[/red]")
    
    except Exception as e:
        console.print(f"[red]❌ Analysis failed:[/red] {str(e)}")
        if config.debug:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option('--prsnl-url', 
              help='PRSNL backend URL (e.g., https://api.prsnl.fyi)')
@click.option('--prsnl-token', 
              help='PRSNL API token')
@click.option('--github-token', 
              help='GitHub personal access token')
@click.option('--openai-key', 
              help='OpenAI API key for local AI processing')
@click.option('--debug', 
              is_flag=True,
              help='Enable debug mode')
@click.pass_context
def config(ctx, prsnl_url: Optional[str], prsnl_token: Optional[str], 
          github_token: Optional[str], openai_key: Optional[str], debug: bool):
    """Configure PRSNL CodeMirror CLI settings."""
    config = ctx.obj['config']
    
    if not any([prsnl_url, prsnl_token, github_token, openai_key, debug]):
        # Show current configuration
        _display_config(config)
        return
    
    # Update configuration
    if prsnl_url:
        config.prsnl_url = prsnl_url
    if prsnl_token:
        config.prsnl_token = prsnl_token
    if github_token:
        config.github_token = github_token
    if openai_key:
        config.openai_key = openai_key
    if debug:
        config.debug = debug
    
    # Save configuration
    config.save()
    console.print("[green]✅ Configuration updated![/green]")
    _display_config(config)


@cli.command()
@click.option('--repo-id', 
              help='Specific repository ID to sync from PRSNL')
@click.option('--download', 
              is_flag=True,
              help='Download analyses from PRSNL to local cache')
@click.option('--clear-cache', 
              is_flag=True,
              help='Clear local analysis cache')
@click.pass_context
def sync(ctx, repo_id: Optional[str], download: bool, clear_cache: bool):
    """Sync data with PRSNL backend."""
    config = ctx.obj['config']
    
    if not config.prsnl_url or not config.prsnl_token:
        console.print("[red]❌ PRSNL connection not configured. Use 'prsnl-codemirror config' to set up.[/red]")
        sys.exit(1)
    
    sync_client = PRSNLSync(config, console)
    
    try:
        if clear_cache:
            sync_client.clear_cache()
            console.print("[green]✅ Local cache cleared[/green]")
        
        if download:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Downloading from PRSNL...", total=None)
                
                result = asyncio.run(sync_client.download_analyses(repo_id))
                
                if result:
                    console.print(f"[green]✅ Downloaded {len(result)} analyses[/green]")
                else:
                    console.print("[yellow]⚠️ No analyses found[/yellow]")
    
    except Exception as e:
        console.print(f"[red]❌ Sync failed:[/red] {str(e)}")
        if config.debug:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument('repo_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--format', 'output_format',
              type=click.Choice(['table', 'json', 'markdown']),
              default='table',
              help='Output format')
@click.pass_context
def info(ctx, repo_path: str, output_format: str):
    """Show repository information and cached analyses."""
    config = ctx.obj['config']
    repo_path = Path(repo_path).resolve()
    
    try:
        analyzer = RepositoryAnalyzer(config, console)
        repo_info = analyzer.get_repository_info(repo_path)
        
        if output_format == 'json':
            console.print(JSON(json.dumps(repo_info, indent=2, default=str)))
        elif output_format == 'markdown':
            _display_repo_info_markdown(repo_info)
        else:
            _display_repo_info_table(repo_info)
    
    except Exception as e:
        console.print(f"[red]❌ Failed to get repository info:[/red] {str(e)}")
        sys.exit(1)


def _display_analysis_results(result: Dict[str, Any]):
    """Display analysis results in a formatted way."""
    console.print("\n[bold green]📊 Analysis Results[/bold green]")
    
    # Summary table
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Repository", result.get('repository', {}).get('name', 'Unknown'))
    table.add_row("Analysis Depth", result.get('analysis_depth', 'Unknown'))
    table.add_row("Files Analyzed", str(result.get('stats', {}).get('files_analyzed', 0)))
    table.add_row("Languages Detected", str(len(result.get('languages', []))))
    table.add_row("Patterns Found", str(len(result.get('patterns', []))))
    table.add_row("Insights Generated", str(len(result.get('insights', []))))
    
    console.print(table)
    
    # Languages
    if result.get('languages'):
        console.print("\n[bold]🔤 Languages:[/bold]")
        lang_table = Table(show_header=True, header_style="bold blue")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Files", style="white")
        lang_table.add_column("Lines", style="white")
        
        for lang in result['languages']:
            lang_table.add_row(
                lang.get('name', 'Unknown'),
                str(lang.get('file_count', 0)),
                str(lang.get('line_count', 0))
            )
        
        console.print(lang_table)
    
    # Top insights
    if result.get('insights'):
        console.print("\n[bold]💡 Key Insights:[/bold]")
        for i, insight in enumerate(result['insights'][:5]):  # Show top 5
            severity_color = {
                'low': 'green',
                'medium': 'yellow', 
                'high': 'red',
                'critical': 'bright_red'
            }.get(insight.get('severity', 'medium'), 'white')
            
            console.print(f"[{severity_color}]• {insight.get('title', 'Untitled')}[/{severity_color}]")
            if insight.get('description'):
                console.print(f"  [dim]{insight['description'][:100]}...[/dim]")


def _display_config(config: CLIConfig):
    """Display current configuration."""
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("PRSNL URL", config.prsnl_url or "[dim]Not set[/dim]")
    table.add_row("PRSNL Token", "***" if config.prsnl_token else "[dim]Not set[/dim]")
    table.add_row("GitHub Token", "***" if config.github_token else "[dim]Not set[/dim]")
    table.add_row("OpenAI Key", "***" if config.openai_key else "[dim]Not set[/dim]")
    table.add_row("Debug Mode", "✅" if config.debug else "❌")
    table.add_row("Config File", str(config.config_file))
    
    console.print(Panel(table, title="[bold]Configuration[/bold]"))


def _display_repo_info_table(repo_info: Dict[str, Any]):
    """Display repository info as a table."""
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Name", repo_info.get('name', 'Unknown'))
    table.add_row("Path", str(repo_info.get('path', 'Unknown')))
    table.add_row("Git Remote", repo_info.get('git', {}).get('remote', 'None'))
    table.add_row("Current Branch", repo_info.get('git', {}).get('branch', 'Unknown'))
    table.add_row("Total Files", str(repo_info.get('stats', {}).get('total_files', 0)))
    table.add_row("Total Lines", str(repo_info.get('stats', {}).get('total_lines', 0)))
    table.add_row("Cached Analyses", str(len(repo_info.get('cached_analyses', []))))
    
    console.print(Panel(table, title="[bold]Repository Information[/bold]"))


def _display_repo_info_markdown(repo_info: Dict[str, Any]):
    """Display repository info as markdown."""
    md = f"""# Repository Information

**Name:** {repo_info.get('name', 'Unknown')}  
**Path:** {repo_info.get('path', 'Unknown')}  
**Git Remote:** {repo_info.get('git', {}).get('remote', 'None')}  
**Current Branch:** {repo_info.get('git', {}).get('branch', 'Unknown')}  
**Total Files:** {repo_info.get('stats', {}).get('total_files', 0)}  
**Total Lines:** {repo_info.get('stats', {}).get('total_lines', 0)}  
**Cached Analyses:** {len(repo_info.get('cached_analyses', []))}  
"""
    console.print(md)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()