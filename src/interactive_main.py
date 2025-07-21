#!/usr/bin/env python3
"""
Interactive ClickUp MCP Agent CLI

This script provides an interactive command-line interface for working with
ClickUp through the MCP server. Instead of running tasks one-off, you can:

1. Start an interactive session
2. Run multiple commands without reconnecting
3. Use built-in commands and shortcuts
4. Maintain conversation history

Usage:
    # Start interactive mode
    uv run python src/interactive_main.py

    # Run single command and exit
    uv run python src/interactive_main.py --command "List my tasks"

    # Or use the installed script (after uv sync)
    uv run clickup-cli

    # Set API key via environment variable
    export CLICKUP_MCP_API_KEY=your_api_key
"""
import asyncio
import os
import sys
from typing import Optional

import click
from agents import Agent, Runner
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

load_dotenv()

console = Console()


class ClickUpCLI:
    """Interactive CLI for ClickUp MCP Agent."""

    def __init__(self):
        self.agent: Optional[Agent] = None
        self.mcp: Optional[MCPServerStdio] = None
        self.connected = False
        self.commands_run = 0

    async def connect(self) -> bool:
        """Connect to the ClickUp MCP server."""
        api_key = os.getenv("CLICKUP_MCP_API_KEY")
        if not api_key:
            console.print("❌ [red]Error: ClickUp API key not found![/red]")
            console.print(
                "💡 [yellow]Set environment variable:[/yellow] "
                "CLICKUP_MCP_API_KEY=your_api_key"
            )
            return False

        try:
            # Setup MCP server parameters
            env = os.environ.copy()
            env["CLICKUP_MCP_API_KEY"] = api_key

            params = MCPServerStdioParams(
                command="uv",
                args=["run", "python", "-m", "clickup_mcp"],
                env=env,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                encoding="utf-8",
                encoding_error_handler="strict",
            )

            self.mcp = MCPServerStdio(params)

            with console.status("[bold blue]Connecting to ClickUp MCP server..."):
                await self.mcp.connect()

            # Create the agent
            self.agent = Agent(
                name="ClickUp Agent",
                instructions=(
                    "You are an expert on ClickUp workspace tasks and "
                    "documentation. Use the available MCP tools to fetch, "
                    "update, create, and summarise ClickUp content. You can "
                    "manage tasks, comments, time tracking, docs, and provide "
                    "analytics. Provide clear, concise responses and format "
                    "data in readable tables when appropriate."
                ),
                mcp_servers=[self.mcp],
            )

            self.connected = True
            console.print(
                "✅ [green]Connected to ClickUp MCP server " "successfully![/green]"
            )
            return True

        except Exception as e:
            console.print(f"❌ [red]Failed to connect to MCP server: {e}[/red]")
            return False

    async def cleanup(self):
        """Cleanup MCP connection."""
        if self.mcp and self.connected:
            console.print("\n🔄 [yellow]Cleaning up MCP connection...[/yellow]")
            await self.mcp.cleanup()
            console.print("✅ [green]Cleanup complete![/green]")
            self.connected = False

    async def run_task(self, task: str) -> Optional[str]:
        """Run a task using the agent."""
        if not self.connected or not self.agent:
            console.print("❌ [red]Not connected to MCP server![/red]")
            return None

        try:
            self.commands_run += 1

            with console.status(f"[bold blue]🤖 Processing: {task[:50]}..."):
                result = await Runner.run(self.agent, task)

            return result.final_output

        except Exception as e:
            console.print(f"❌ [red]Error running task: {e}[/red]")
            return None

    def show_help(self):
        """Show available commands and shortcuts."""
        help_table = Table(title="Available Commands")
        help_table.add_column("Command", style="cyan")
        help_table.add_column("Description", style="white")

        commands = [
            ("help, h, ?", "Show this help message"),
            ("quit, exit, q", "Exit the interactive session"),
            ("status", "Show connection status and stats"),
            ("clear", "Clear the screen"),
            ("history", "Show command history (last 10)"),
            ("<any text>", "Send command to ClickUp agent"),
        ]

        for cmd, desc in commands:
            help_table.add_row(cmd, desc)

        console.print(help_table)

        # Show some example commands
        console.print("\n💡 [bold yellow]Example Commands:[/bold yellow]")
        examples = [
            "List my overdue tasks",
            "Create a new task 'Fix authentication bug' in Development",
            "Show me all tasks assigned to John",
            "What are my tasks due this week?",
            "Update task status to 'in progress'",
            "Add a comment to task with ID 123456",
        ]

        for example in examples:
            console.print(f"  • [dim]{example}[/dim]")

    def show_status(self):
        """Show current connection status and statistics."""
        agent_status = "Ready" if self.agent else "Not initialized"
        status_panel = Panel.fit(
            f"[green]Connected: {self.connected}[/green]\n"
            f"[blue]Commands run: {self.commands_run}[/blue]\n"
            f"[yellow]Agent: {agent_status}[/yellow]",
            title="Status",
            border_style="blue",
        )
        console.print(status_panel)

    async def interactive_loop(self):
        """Main interactive loop."""
        # Show welcome message
        welcome = Panel.fit(
            "[bold blue]🚀 ClickUp MCP Interactive Agent[/bold blue]\n\n"
            "Type 'help' for available commands\n"
            "Type 'quit' to exit",
            title="Welcome",
            border_style="green",
        )
        console.print(welcome)

        command_history = []

        while True:
            try:
                # Get user input
                user_input = Prompt.ask(
                    "\n[bold cyan]ClickUp>[/bold cyan]", default="help"
                ).strip()

                if not user_input:
                    continue

                # Add to history
                command_history.append(user_input)
                if len(command_history) > 10:
                    command_history.pop(0)

                # Handle built-in commands
                if user_input.lower() in ["quit", "exit", "q"]:
                    console.print("👋 [yellow]Goodbye![/yellow]")
                    break

                elif user_input.lower() in ["help", "h", "?"]:
                    self.show_help()
                    continue

                elif user_input.lower() == "status":
                    self.show_status()
                    continue

                elif user_input.lower() == "clear":
                    os.system("clear" if os.name != "nt" else "cls")
                    continue

                elif user_input.lower() == "history":
                    console.print("[bold]Recent Commands:[/bold]")
                    for i, cmd in enumerate(command_history[-10:], 1):
                        console.print(f"  {i}. [dim]{cmd}[/dim]")
                    continue

                # Run the task
                console.print(f"\n🤖 [bold]Task:[/bold] {user_input}")
                console.print("─" * 60)

                result = await self.run_task(user_input)
                if result:
                    console.print("\n✅ [bold green]Response:[/bold green]")
                    console.print("─" * 60)

                    # Try to render as markdown if it looks like markdown
                    markdown_markers = ["**", "*", "```", "#", "-", "|"]
                    if any(marker in result for marker in markdown_markers):
                        try:
                            console.print(Markdown(result))
                        except Exception:
                            console.print(result)
                    else:
                        console.print(result)

            except KeyboardInterrupt:
                console.print("\n\n👋 [yellow]Interrupted by user. Goodbye![/yellow]")
                break
            except EOFError:
                console.print("\n\n👋 [yellow]Goodbye![/yellow]")
                break


@click.command()
@click.option(
    "--command", "-c", help="Run a single command and exit (non-interactive mode)"
)
@click.option(
    "--api-key",
    envvar="CLICKUP_MCP_API_KEY",
    help="ClickUp API key (or set CLICKUP_MCP_API_KEY environment variable)",
)
def main(command: Optional[str], api_key: Optional[str]):
    """
    Interactive ClickUp MCP Agent CLI.

    Start an interactive session to run multiple ClickUp commands
    without reconnecting each time.
    """

    async def run():
        cli = ClickUpCLI()

        # Connect to MCP server
        if not await cli.connect():
            sys.exit(1)

        try:
            if command:
                # Single command mode
                console.print(f"🤖 [bold]Running:[/bold] {command}")
                console.print("─" * 60)

                result = await cli.run_task(command)
                if result:
                    console.print("\n✅ [bold green]Response:[/bold green]")
                    console.print("─" * 60)
                    console.print(result)
            else:
                # Interactive mode
                await cli.interactive_loop()

        finally:
            await cli.cleanup()

    # Set API key if provided
    if api_key:
        os.environ["CLICKUP_MCP_API_KEY"] = api_key

    asyncio.run(run())


if __name__ == "__main__":
    main()
