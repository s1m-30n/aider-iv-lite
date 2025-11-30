from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box
from datetime import datetime

class BotUI:
    def __init__(self):
        self.console = Console()
        
    def print_banner(self):
        self.console.print(Panel.fit(
            "[bold cyan]🚀 Aider Lite Trading Bot[/bold cyan]\n[dim]Advanced Boom/Crash Scalper with Spike Prediction[/dim]",
            border_style="cyan",
            box=box.ROUNDED
        ))
        
    def _format_trend_arrow(self, trend: str) -> str:
        if trend == "bullish":
            return "[green]↑[/green]"
        elif trend == "bearish":
            return "[red]↓[/red]"
        return "[dim]-[/dim]"

    def print_status(self, market_data: dict):
        """
        Print a table of current market status.
        market_data: dict of symbol -> {price, trend_d1, trend_h4, trend_h1, bias, signal, spike_prob}
        """
        table = Table(title=f"Market Status - {datetime.now().strftime('%H:%M:%S')}", box=box.ROUNDED)
        
        table.add_column("Symbol", style="cyan", no_wrap=True)
        table.add_column("Price", style="white")
        table.add_column("Trend (D1/H4/H1)", style="white")
        table.add_column("Bias", style="yellow")
        table.add_column("Spike Risk", style="red")
        table.add_column("Signal", style="green")
        
        for symbol, data in market_data.items():
            spike_prob = data.get('spike_prob', 0)
            spike_str = f"{spike_prob:.1f}%"
            if spike_prob > 50:
                spike_str = f"[bold red]{spike_str}[/bold red]"
            elif spike_prob < 30:
                spike_str = f"[green]{spike_str}[/green]"
                
            signal = data.get('signal', 'None')
            if signal != 'None':
                signal = f"[bold green]{signal}[/bold green]"
            else:
                signal = "[dim]None[/dim]"
            
            # Format Trend
            t_d1 = self._format_trend_arrow(data.get('trend_d1', 'neutral'))
            t_h4 = self._format_trend_arrow(data.get('trend_h4', 'neutral'))
            t_h1 = self._format_trend_arrow(data.get('trend_h1', 'neutral'))
            trend_str = f"{t_d1} {t_h4} {t_h1}"
                
            table.add_row(
                symbol,
                f"{data.get('price', 0):.2f}",
                trend_str,
                data.get('bias', 'N/A'),
                spike_str,
                signal
            )
            
        self.console.print(table)
        
    def log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "info":
            self.console.print(f"[dim]{timestamp}[/dim] [blue]INFO[/blue] {message}")
        elif level == "warning":
            self.console.print(f"[dim]{timestamp}[/dim] [yellow]WARN[/yellow] {message}")
        elif level == "error":
            self.console.print(f"[dim]{timestamp}[/dim] [bold red]ERROR[/bold red] {message}")
        elif level == "success":
            self.console.print(f"[dim]{timestamp}[/dim] [bold green]SUCCESS[/bold green] {message}")
            
    def trade_alert(self, symbol: str, type: str, price: float, sl: float, tp: float):
        content = f"""
[bold]{symbol}[/bold]
Type: [bold { 'green' if type == 'buy' else 'red' }]{type.upper()}[/]
Price: {price:.2f}
SL: {sl:.2f}
TP: {tp:.2f}
"""
        self.console.print(Panel(content, title="🚨 TRADE ALERT 🚨", border_style="red" if type == "sell" else "green"))
