"""Entry point for the ClickUp MCP server."""

import asyncio
import json
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler

from .config import Config, ConfigError
from .server import ClickUpMCPServer

console = Console()


def setup_logging(debug: bool = False) -> None:
    """Configure logging with rich output."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group(invoke_without_command=True)
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """ClickUp MCP Server - AI assistant integration for ClickUp."""
    setup_logging(debug)

    if ctx.invoked_subcommand is None:
        # Default behavior: run the server
        ctx.invoke(serve, debug=debug)


@cli.command()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def serve(debug: bool) -> None:
    """Run the MCP server."""
    try:
        config = Config()
        server = ClickUpMCPServer(config)

        console.print("[green]Starting ClickUp MCP Server...[/green]")
        asyncio.run(server.run())

    except ConfigError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        console.print("\nPlease configure your API key using one of these methods:")
        console.print("1. Create ~/.config/clickup-mcp/config.json")
        console.print("2. Set CLICKUP_MCP_API_KEY environment variable")
        console.print("\nRun 'clickup-mcp check-config' for more details.")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if debug:
            console.print_exception()
        sys.exit(1)


@cli.command("check-config")
def check_config() -> None:
    """Check configuration and API key setup."""
    console.print("[bold]ClickUp MCP Configuration Check[/bold]\n")

    from platformdirs import user_config_dir

    config_locations = [
        Path.home() / ".config" / "clickup-mcp" / "config.json",
        Path(user_config_dir("clickup-mcp")) / "config.json",
        Path.home() / ".clickup-mcp" / "config.json",
    ]

    # Check for config files
    console.print("[yellow]Checking configuration files:[/yellow]")
    config_found = False
    for loc in config_locations:
        if loc.exists():
            console.print(f"  ✓ Found: {loc}")
            config_found = True
        else:
            console.print(f"  ✗ Not found: {loc}")

    # Check environment variable
    import os

    env_key = os.environ.get("CLICKUP_MCP_API_KEY")
    if env_key:
        console.print("  ✓ Environment variable CLICKUP_MCP_API_KEY is set")
        config_found = True
    else:
        console.print("  ✗ Environment variable CLICKUP_MCP_API_KEY not set")

    if not config_found:
        console.print("\n[red]No configuration found![/red]")
        console.print("\nTo configure, use the set-api-key command:")
        console.print("  [cyan]clickup-mcp set-api-key YOUR_API_KEY[/cyan]")
        console.print("\nOr create a file at one of these locations:")
        for loc in config_locations:
            console.print(f"  {loc}")
        console.print('\nWith content:\n{"api_key": "your_clickup_api_key_here"}')
        return

    # Try to load config
    try:
        config = Config()
        console.print("\n[green]✓ Configuration loaded successfully![/green]")
        console.print(f"  API key: {config.api_key[:10]}...{config.api_key[-4:]}")
        if config.default_workspace_id:
            console.print(f"  Default workspace: {config.default_workspace_id}")
    except ConfigError as e:
        console.print(f"\n[red]Configuration error:[/red] {e}")


@cli.command("test-connection")
def test_connection() -> None:
    """Test the connection to ClickUp API."""
    try:
        config = Config()

        console.print("[yellow]Testing ClickUp API connection...[/yellow]")

        # We'll implement the actual test in the client module
        import httpx

        async def test():
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": config.api_key}
                response = await client.get(
                    "https://api.clickup.com/api/v2/user",
                    headers=headers,
                )

                if response.status_code == 200:
                    user_data = response.json()
                    console.print("\n[green]✓ Connection successful![/green]")
                    console.print(f"  Authenticated as: {user_data['user']['username']}")
                    console.print(f"  Email: {user_data['user']['email']}")
                else:
                    console.print("\n[red]✗ Connection failed![/red]")
                    console.print(f"  Status code: {response.status_code}")
                    console.print(f"  Response: {response.text}")

        asyncio.run(test())

    except ConfigError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        console.print("\nRun 'clickup-mcp check-config' to diagnose.")
    except Exception as e:
        console.print(f"[red]Connection test failed:[/red] {e}")


@cli.command("set-api-key")
@click.argument("api_key")
def set_api_key(api_key: str) -> None:
    """Set the ClickUp API key."""
    from pathlib import Path

    # Use ~/.config/clickup-mcp/ as the default location
    config_dir = Path.home() / ".config" / "clickup-mcp"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"

    # Load existing config if it exists
    config_data = {}
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)
        except Exception:
            pass

    # Update API key
    config_data["api_key"] = api_key

    # Save config
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)

    console.print(f"[green]✓ API key saved to {config_file}[/green]")
    console.print(
        "\nNow you can test the connection with: [cyan]clickup-mcp test-connection[/cyan]"
    )


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
