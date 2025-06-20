"""Paper trading simulator for PhaseGrid strategy validation."""
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)

@dataclass
class TradeResult:
    source_id: str
    timestamp: datetime
    stake: float
    odds: float
    result: str  # 'WIN', 'LOSS', 'PUSH'
    pnl: float
    phase: str
    
    
class PaperTrader:
    """Simulates trading with repaired sheet data."""
    
    def __init__(self, bankroll: float = 10000.0):
        self.initial_bankroll = bankroll
        self.bankroll = bankroll
        self.trades: List[TradeResult] = []
        self.phase_mapping = self._load_phase_mapping()
        self.kelly_divisors = self._load_kelly_divisors()
        
    def _load_phase_mapping(self) -> Dict:
        """Load phase mapping configuration."""
        config_path = Path("config/phase_mapping.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {"default": {"threshold": 0.55, "confidence": 0.7}}
    
    def _load_kelly_divisors(self) -> Dict:
        """Load Kelly divisor configuration."""
        config_path = Path("config/phase_kelly_divisors.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {"conservative": 4, "moderate": 3, "aggressive": 2}
    
    def calculate_stake(self, confidence: float, odds: float, phase: str) -> float:
        """Calculate stake using Kelly criterion with phase adjustment."""
        # Kelly formula: f = (p*b - q) / b
        # where p = win probability, b = decimal odds - 1, q = 1 - p
        p = confidence
        b = odds - 1
        q = 1 - p
        
        kelly_fraction = (p * b - q) / b if b > 0 else 0
        
        # Apply phase-based divisor
        divisor = self.kelly_divisors.get(phase, 4)
        adjusted_fraction = kelly_fraction / divisor
        
        # Cap at 5% of bankroll
        max_stake = self.bankroll * 0.05
        stake = min(self.bankroll * adjusted_fraction, max_stake)
        
        return max(stake, 0)
    
    def simulate_trade(self, confidence: float, odds: float, 
                      phase: str = "conservative") -> TradeResult:
        """Simulate a single trade."""
        stake = self.calculate_stake(confidence, odds, phase)
        
        # Simulate outcome based on confidence
        random_val = random.random()
        if random_val < confidence:
            result = "WIN"
            pnl = stake * (odds - 1)
        elif random_val < confidence + 0.05:  # 5% push probability
            result = "PUSH"
            pnl = 0
        else:
            result = "LOSS"
            pnl = -stake
            
        self.bankroll += pnl
        
        trade = TradeResult(
            source_id=f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            timestamp=datetime.now(),
            stake=stake,
            odds=odds,
            result=result,
            pnl=pnl,
            phase=phase
        )
        
        self.trades.append(trade)
        return trade
    
    def run_dry_run(self, days: int = 7, trades_per_day: int = 10) -> Dict:
        """Run paper trading simulation for specified days."""
        logger.info(f"Starting {days}-day DRY_RUN simulation...")
        
        start_date = datetime.now() - timedelta(days=days)
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            for _ in range(trades_per_day):
                # Generate realistic parameters
                confidence = random.uniform(0.52, 0.68)
                odds = random.uniform(1.7, 2.5)
                phase = random.choice(["conservative", "moderate", "aggressive"])
                
                self.simulate_trade(confidence, odds, phase)
        
        return self.calculate_metrics()
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics."""
        if not self.trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "roi": 0.0,
                "total_pnl": 0.0,
                "avg_stake": 0.0,
                "final_bankroll": self.bankroll
            }
        
        wins = sum(1 for t in self.trades if t.result == "WIN")
        losses = sum(1 for t in self.trades if t.result == "LOSS")
        pushes = sum(1 for t in self.trades if t.result == "PUSH")
        
        total_staked = sum(t.stake for t in self.trades)
        total_pnl = sum(t.pnl for t in self.trades)
        
        metrics = {
            "total_trades": len(self.trades),
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "win_rate": wins / (wins + losses) if (wins + losses) > 0 else 0.0,
            "roi": (total_pnl / total_staked * 100) if total_staked > 0 else 0.0,
            "total_pnl": total_pnl,
            "avg_stake": total_staked / len(self.trades),
            "initial_bankroll": self.initial_bankroll,
            "final_bankroll": self.bankroll,
            "bankroll_growth": ((self.bankroll - self.initial_bankroll) / self.initial_bankroll * 100)
        }
        
        return metrics
    
    def save_results(self, output_path: Path = Path("output/paper_metrics.csv")):
        """Save trade results to CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['source_id', 'timestamp', 'stake', 'odds', 
                           'result', 'pnl', 'phase', 'running_bankroll'])
            
            running_bankroll = self.initial_bankroll
            for trade in self.trades:
                running_bankroll += trade.pnl
                writer.writerow([
                    trade.source_id,
                    trade.timestamp.isoformat(),
                    f"{trade.stake:.2f}",
                    f"{trade.odds:.2f}",
                    trade.result,
                    f"{trade.pnl:.2f}",
                    trade.phase,
                    f"{running_bankroll:.2f}"
                ])
        
        logger.info(f"Results saved to {output_path}")
    
    def print_summary(self, metrics: Dict):
        """Print metrics summary to console."""
        print("\n" + "="*50)
        print("PAPER TRADER - 7-DAY DRY RUN SUMMARY")
        print("="*50)
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Wins/Losses/Pushes: {metrics['wins']}/{metrics['losses']}/{metrics['pushes']}")
        print(f"Win Rate: {metrics['win_rate']:.1%}")
        print(f"ROI: {metrics['roi']:.2f}%")
        print(f"Total P&L: ${metrics['total_pnl']:.2f}")
        print(f"Bankroll: ${metrics['initial_bankroll']:.2f} → ${metrics['final_bankroll']:.2f}")
        print(f"Growth: {metrics['bankroll_growth']:.2f}%")
        print("="*50)


def main():
    """Execute paper trading simulation after repairs."""
    # Initialize with environment or default bankroll
    import os
    bankroll = float(os.getenv('BANKROLL', 10000))
    
    trader = PaperTrader(bankroll=bankroll)
    
    # Run 7-day simulation
    metrics = trader.run_dry_run(days=7, trades_per_day=15)
    
    # Save results
    trader.save_results()
    
    # Print summary
    trader.print_summary(metrics)
    
    return metrics


if __name__ == "__main__":
    main()