import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DailyAnalysisPipeline:
    """
    Orchestrates the full WNBA betting analysis pipeline.
    Runs all analyzers and generates a comprehensive daily report.
    """
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.report_lines = []
        
    def log(self, message, level="INFO"):
        """Log message to console and report."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Clean message for console (Windows compatibility)
        console_msg = message.replace('✅', '[OK]').replace('❌', '[FAIL]').replace('⚠️', '[WARN]')
        formatted_console = f"[{timestamp}] {level}: {console_msg}"
        print(formatted_console)
        
        # Keep original for report file
        formatted_report = f"[{timestamp}] {level}: {message}"
        self.report_lines.append(formatted_report)
        
    def run_volatility_analysis(self):
        """Run volatility analysis inline."""
        self.log("Running Volatility Analyzer...")
        
        try:
            from core.volatility_analyzer import VolatilityAnalyzer
            
            # Load gamelogs
            gamelogs_df = pd.read_csv('data/wnba_combined_gamelogs.csv')
            gamelogs_df = gamelogs_df.rename(columns={'PLAYER_NAME': 'Player', 'GAME_DATE': 'Date'})
            
            # Run analysis
            analyzer = VolatilityAnalyzer(lookback_games=10)
            volatility_results = analyzer.analyze_player_volatility(gamelogs_df)
            
            # Save results
            volatility_results = volatility_results.sort_values('Overall_Volatility', ascending=False)
            volatility_results.to_csv('output/player_volatility_analysis.csv', index=False)
            
            # Get patterns
            patterns_df = analyzer.identify_volatility_patterns(volatility_results)
            if not patterns_df.empty:
                patterns_df.to_csv('output/volatility_patterns.csv', index=False)
            
            self.log(f"✅ Volatility analysis complete - {len(volatility_results)} players analyzed")
            return True
            
        except Exception as e:
            self.log(f"❌ Volatility analysis failed: {str(e)}", "ERROR")
            return False
            
    def run_cycle_detection(self):
        """Run performance cycle detection inline."""
        self.log("Running Performance Cycle Detector...")
        
        try:
            from core.performance_cycle_detector import PerformanceCycleDetector
            
            # Load gamelogs
            gamelogs_df = pd.read_csv('data/wnba_combined_gamelogs.csv')
            gamelogs_df = gamelogs_df.rename(columns={'PLAYER_NAME': 'Player', 'GAME_DATE': 'Date'})
            gamelogs_df['Date'] = pd.to_datetime(gamelogs_df['Date'], format='mixed', errors='coerce')
            
            # Run detection
            detector = PerformanceCycleDetector(min_games=20)
            cycles_results = detector.detect_cycles(gamelogs_df)
            
            # Save results
            cycles_results.to_csv('output/player_performance_cycles.csv', index=False)
            
            # Find opportunities
            opportunities = detector.identify_betting_opportunities(cycles_results)
            if not opportunities.empty:
                opportunities = opportunities.sort_values('Opportunity_Count', ascending=False)
                opportunities.to_csv('output/cycle_betting_opportunities.csv', index=False)
                
            self.log(f"✅ Cycle detection complete - {len(cycles_results)} players analyzed")
            return True
            
        except Exception as e:
            self.log(f"❌ Cycle detection failed: {str(e)}", "ERROR")
            return False
            
    def run_prop_value_analysis(self):
        """Run prop value analysis inline."""
        self.log("Running Prop Value Analyzer...")
        
        try:
            from core.prop_value_analyzer import PropValueAnalyzer
            
            # Initialize analyzer
            analyzer = PropValueAnalyzer()
            
            # Load all required data
            volatility_df = pd.read_csv('output/player_volatility_analysis.csv')
            cycles_df = pd.read_csv('output/player_performance_cycles.csv')
            
            gamelogs_df = pd.read_csv('data/wnba_combined_gamelogs.csv')
            gamelogs_df = gamelogs_df.rename(columns={'PLAYER_NAME': 'Player', 'GAME_DATE': 'Date'})
            
            props_df = pd.read_csv('data/wnba_prizepicks_props.csv')
            
            # Stat mapping
            stat_mapping = {
                'Points': 'PTS',
                'Rebounds': 'REB', 
                'Assists': 'AST',
                'Steals': 'STL',
                'Blocks': 'BLK',
                '3-PT Made': 'FG3M',
                'Pts+Rebs+Asts': 'PRA',
                'Pts+Rebs': 'PR',
                'Pts+Asts': 'PA'
            }
            
            # Run analysis
            value_results = analyzer.analyze_props(props_df, gamelogs_df, volatility_df, cycles_df, stat_mapping)
            
            if not value_results.empty:
                value_results = value_results.sort_values('EV', ascending=False)
                value_results.to_csv('output/prop_value_analysis.csv', index=False)
                self.log(f"✅ Prop value analysis complete - {len(value_results)} valuable props found")
            else:
                self.log("⚠️  No valuable props found", "WARN")
                
            return True
            
        except Exception as e:
            self.log(f"❌ Prop value analysis failed: {str(e)}", "ERROR")
            return False
            
    def check_data_freshness(self):
        """Check if data files are recent."""
        self.log("Checking data freshness...")
        
        gamelogs_path = 'data/wnba_combined_gamelogs.csv'
        if os.path.exists(gamelogs_path):
            mod_time = datetime.fromtimestamp(os.path.getmtime(gamelogs_path))
            days_old = (datetime.now() - mod_time).days
            
            if days_old > 7:
                self.log(f"⚠️  Gamelogs are {days_old} days old. Consider updating.", "WARN")
            else:
                self.log(f"✅ Gamelogs are {days_old} days old")
                
    def generate_summary_report(self):
        """Generate final summary report combining all analyses."""
        self.log("Generating summary report...")
        
        report_path = f'output/daily_report_{self.timestamp}.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"WNBA BETTING INTELLIGENCE REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Pipeline execution log
            f.write("PIPELINE EXECUTION LOG:\n")
            f.write("-" * 40 + "\n")
            for line in self.report_lines:
                f.write(line + "\n")
            f.write("\n")
            
            # Top betting opportunities
            f.write("TOP BETTING OPPORTUNITIES:\n")
            f.write("-" * 40 + "\n")
            
            try:
                # Load prop value analysis
                props_df = pd.read_csv('output/prop_value_analysis.csv')
                if not props_df.empty:
                    f.write(f"Found {len(props_df)} props with edge\n\n")
                    
                    # Top 5 by EV
                    top_props = props_df.nlargest(5, 'EV')
                    for _, prop in top_props.iterrows():
                        f.write(f"• {prop['Player']} {prop['Stat']} {prop['Recommendation']}\n")
                        f.write(f"  Line: {prop['Line']}, Projection: {prop['Projection']}\n")
                        f.write(f"  Hit%: {prop['Hit_Probability']}%, EV: {prop['EV']}%\n")
                        f.write(f"  Risk Level: {prop['Risk_Level']}\n\n")
                else:
                    f.write("No valuable props found today.\n\n")
            except:
                f.write("Could not load prop analysis.\n\n")
                
            # High-risk players to avoid
            f.write("HIGH-RISK PLAYERS (AVOID):\n")
            f.write("-" * 40 + "\n")
            
            try:
                volatility_df = pd.read_csv('output/player_volatility_analysis.csv')
                extreme_players = volatility_df[volatility_df['Risk_Level'] == 'EXTREME'].head(10)
                
                for _, player in extreme_players.iterrows():
                    f.write(f"• {player['Player']} - CV: {player['Overall_Volatility']:.3f}\n")
                f.write("\n")
            except:
                f.write("Could not load volatility analysis.\n\n")
                
            # Players on hot streaks
            f.write("PLAYERS ON HOT STREAKS:\n")
            f.write("-" * 40 + "\n")
            
            try:
                cycles_df = pd.read_csv('output/player_performance_cycles.csv')
                hot_players = []
                
                for _, player in cycles_df.iterrows():
                    hot_stats = []
                    for stat in ['PTS', 'REB', 'AST']:
                        if player.get(f'{stat}_Current_Streak') == 'hot':
                            hot_stats.append(f"{stat}({player.get(f'{stat}_Streak_Length', 0)})")
                    
                    if hot_stats:
                        hot_players.append(f"• {player['Player']}: {', '.join(hot_stats)}")
                
                for player_info in hot_players[:10]:
                    f.write(player_info + "\n")
                f.write("\n")
            except:
                f.write("Could not load cycle analysis.\n\n")
                
            # Summary statistics
            f.write("SUMMARY STATISTICS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Pipeline version: 1.0\n")
            
        self.log(f"✅ Report saved to {report_path}")
        return report_path
        
    def create_betting_slip(self):
        """Create a simple betting slip with top plays."""
        self.log("Creating betting slip...")
        
        try:
            props_df = pd.read_csv('output/prop_value_analysis.csv')
            
            # Filter for best bets
            strong_bets = props_df[
                (props_df['EV'] >= 10) & 
                (props_df['Confidence'] >= 60)
            ].sort_values('EV', ascending=False)
            
            if not strong_bets.empty:
                slip_path = f'output/betting_slip_{self.timestamp}.csv'
                
                betting_slip = strong_bets[
                    ['Player', 'Stat', 'Line', 'Recommendation', 'Hit_Probability', 'EV']
                ].copy()
                
                betting_slip['Bet'] = betting_slip.apply(
                    lambda x: f"{x['Player']} {x['Recommendation']} {x['Line']} {x['Stat']}", 
                    axis=1
                )
                
                betting_slip[['Bet', 'Hit_Probability', 'EV']].to_csv(slip_path, index=False, encoding='utf-8')
                self.log(f"✅ Betting slip saved to {slip_path}")
            else:
                self.log("No high-confidence bets found today")
                
        except Exception as e:
            self.log(f"Could not create betting slip: {e}", "ERROR")
            
    def run_pipeline(self):
        """Execute the full analysis pipeline."""
        print("\n" + "=" * 80)
        print("WNBA DAILY BETTING ANALYSIS PIPELINE")
        print("=" * 80 + "\n")
        
        # Check data freshness
        self.check_data_freshness()
        
        # Run analyzers in sequence
        success1 = self.run_volatility_analysis()
        success2 = self.run_cycle_detection()
        success3 = self.run_prop_value_analysis()
        
        all_success = success1 and success2 and success3
        
        # Generate reports
        if all_success:
            self.log("\nAll analyzers completed. Generating reports...")
            report_path = self.generate_summary_report()
            self.create_betting_slip()
            
            print("\n" + "=" * 80)
            print("PIPELINE COMPLETE")
            print("=" * 80)
            print(f"\nDaily report: {report_path}")
            print(f"Analysis outputs in: output/")
            print(f"Check betting slip for today's best plays")
            
        else:
            self.log("\nPipeline completed with errors. Check logs.", "WARN")
            self.generate_summary_report()  # Still generate report with what we have
            
def main():
    """Run the daily analysis pipeline."""
    pipeline = DailyAnalysisPipeline()
    pipeline.run_pipeline()
    
if __name__ == "__main__":
    main()