"""
Main application for the AI Trading Bot
"""
import asyncio
import os
import sys
import signal
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from agents.master_agent import MasterAgent
from utils.logger import trading_logger
from utils.email_sender import EmailSender

class AITradingBot:
    """Main AI Trading Bot application"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.logger = trading_logger.get_logger("main_app")
        self.config_path = config_path
        self.master_agent = None
        self.email_sender = None
        self.running = False
        
        # Load configuration
        self.config = self._load_config()
        
        # Schedule configuration
        self.schedule_config = self.config.get('schedule', {})
        
        self.logger.info("AI Trading Bot initialized")
    
    def _load_config(self):
        """Load configuration"""
        try:
            import yaml
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except Exception as e:
            self.logger.error("Error loading config", error=str(e))
            return {}
    
    async def initialize(self):
        """Initialize the trading bot"""
        try:
            self.logger.info("Initializing AI Trading Bot...")
            
            # Initialize master agent
            self.master_agent = MasterAgent(self.config_path)
            
            # Initialize email sender
            self.email_sender = EmailSender(self.config_path)
            self.email_sender.set_logger(trading_logger.get_logger("main_app"))
            
            # Start position monitoring if enabled
            if self.config.get('trading', {}).get('monitoring', {}).get('enable_automated_management', True):
                await self.master_agent.start_position_monitoring()
                self.logger.info("Position monitoring started")
            else:
                self.logger.info("Position monitoring disabled in configuration")
            
            # Test email configuration (disabled)
            # await self._test_email_configuration()
            
            self.logger.info("AI Trading Bot initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error("Error initializing AI Trading Bot", error=str(e))
            return False
    
    async def _test_email_configuration(self):
        """Test email configuration"""
        try:
            self.logger.info("Testing email configuration...")
            
            # Send test email
            success = self.email_sender.send_alert(
                "SYSTEM_TEST",
                "AI Trading Bot email configuration test",
                {"timestamp": datetime.now().isoformat(), "status": "testing"}
            )
            
            if success:
                self.logger.info("Email configuration test successful")
            else:
                self.logger.warning("Email configuration test failed")
                
        except Exception as e:
            self.logger.error("Error testing email configuration", error=str(e))
    
    async def run_market_analysis(self):
        """Run a single market analysis cycle"""
        try:
            self.logger.info("Starting market analysis...")
            
            # Execute comprehensive analysis
            results = await self.master_agent.execute_comprehensive_analysis()
            
            if results:
                self.logger.info("Market analysis completed successfully", 
                               results_summary=len(results.get('trading_decisions', {})))
                
                # Display trading decisions summary
                decision_summary = self.master_agent.get_decision_summary()
                self.logger.info("Trading decisions summary", summary=decision_summary)
                
                # Ask user if they want to execute trades
                if results.get('trading_decisions'):
                    await self._handle_trade_execution(results['trading_decisions'])
                
                # Send email report (always send, even if no actionable decisions)
                self.logger.info("Sending trading report email...")
                await self.master_agent.send_trading_report()
                self.logger.info("Email report process completed")
                
                # Check position management opportunities
                await self._check_position_management()
            else:
                self.logger.warning("No analysis results generated")
                # Send summary email even if no results
                self.logger.info("Sending summary email...")
                await self.master_agent.send_trading_report()
                
        except Exception as e:
            self.logger.error("Error in market analysis", error=str(e))
    
    async def _handle_trade_execution(self, trading_decisions: Dict):
        """Handle trade execution based on user preference"""
        try:
            # Check if there are any BUY/SELL decisions
            actionable_decisions = {
                ticker: decision for ticker, decision in trading_decisions.items()
                if decision.get('action') in ['BUY', 'SELL']
            }
            
            if not actionable_decisions:
                self.logger.info("No actionable trading decisions (all HOLD)")
                return
            
            # Check if auto-execution is enabled
            auto_execute = os.getenv('AUTO_EXECUTE_TRADES', 'false').lower() == 'true'
            
            if auto_execute:
                self.logger.info("Auto-execution enabled, executing trades...")
                execution_results = await self.master_agent.execute_trades()
                
                if execution_results:
                    self.logger.info("Trade execution completed", 
                                   executed_trades=len([r for r in execution_results.values() if r.get('success')]))
                else:
                    self.logger.warning("No trades were executed")
            else:
                self.logger.info("Auto-execution disabled. To enable, set AUTO_EXECUTE_TRADES=true in .env")
                self.logger.info(f"Found {len(actionable_decisions)} actionable decisions: {list(actionable_decisions.keys())}")
                
        except Exception as e:
            self.logger.error("Error handling trade execution", error=str(e))
    
    async def _check_position_management(self):
        """Check for position management opportunities"""
        try:
            self.logger.info("Checking position management opportunities...")
            
            # Check for averaging down and profit taking opportunities
            opportunities = self.master_agent.check_position_management_opportunities()
            
            if opportunities:
                self.logger.info(f"Found {len(opportunities)} position management opportunities")
                
                for opp in opportunities:
                    self.logger.info(f"Opportunity: {opp['ticker']} - {opp['action']} - {opp['reasoning']}")
                
                # Check if auto-execution is enabled
                auto_execute = os.getenv('AUTO_EXECUTE_TRADES', 'false').lower() == 'true'
                
                if auto_execute:
                    self.logger.info("Auto-execution enabled, executing position management actions...")
                    # Position management actions are handled by the position monitor
                else:
                    self.logger.info("Auto-execution disabled. Position management actions will not be executed automatically.")
            else:
                self.logger.info("No position management opportunities found")
                
        except Exception as e:
            self.logger.error("Error checking position management opportunities", error=str(e))
    
    async def run_intraday_monitoring(self):
        """Run intraday monitoring and analysis"""
        try:
            self.logger.info("Starting intraday monitoring...")
            
            # For now, just run a quick analysis
            # In a real implementation, this would be more focused monitoring
            success = await self.run_market_analysis()
            
            if success:
                self.logger.info("Intraday monitoring completed")
            else:
                self.logger.warning("Intraday monitoring completed with issues")
            
            return success
            
        except Exception as e:
            self.logger.error("Error in intraday monitoring", error=str(e))
            return False
    
    async def run_end_of_day_report(self):
        """Run end of day analysis and reporting"""
        try:
            self.logger.info("Starting end of day analysis...")
            
            # Run comprehensive analysis
            success = await self.run_market_analysis()
            
            if success:
                # Send comprehensive end-of-day report
                await self._send_end_of_day_report()
                self.logger.info("End of day analysis and reporting completed")
            else:
                self.logger.warning("End of day analysis completed with issues")
            
            return success
            
        except Exception as e:
            self.logger.error("Error in end of day analysis", error=str(e))
            return False
    
    async def _send_end_of_day_report(self):
        """Send comprehensive end of day report"""
        try:
            if not self.master_agent:
                return
            
            # Get analysis summaries
            analysis_summary = self.master_agent.analysis_agent.get_analysis_summary()
            news_summary = self.master_agent.news_agent.get_news_summary()
            decision_summary = self.master_agent.get_decision_summary()
            
            # Prepare comprehensive report
            report_data = {
                'analysis_summary': analysis_summary,
                'news_summary': news_summary,
                'decision_summary': decision_summary,
                'timestamp': datetime.now().isoformat(),
                'report_type': 'end_of_day'
            }
            
            # Send report email
            success = self.email_sender.send_alert(
                "END_OF_DAY_REPORT",
                "AI Trading Bot - End of Day Report",
                report_data
            )
            
            if success:
                self.logger.info("End of day report sent successfully")
            else:
                self.logger.error("Failed to send end of day report")
                
        except Exception as e:
            self.logger.error("Error sending end of day report", error=str(e))
    
    def setup_schedule(self):
        """Setup scheduled tasks"""
        try:
            self.logger.info("Setting up scheduled tasks...")
            
            # Market open analysis
            market_open_time = self.schedule_config.get('market_open_analysis', '09:30')
            schedule.every().day.at(market_open_time).do(
                lambda: asyncio.run(self.run_market_analysis())
            )
            self.logger.info(f"Scheduled market open analysis for {market_open_time}")
            
            # Intraday monitoring
            intraday_time = self.schedule_config.get('intraday_monitoring', '12:00')
            schedule.every().day.at(intraday_time).do(
                lambda: asyncio.run(self.run_intraday_monitoring())
            )
            self.logger.info(f"Scheduled intraday monitoring for {intraday_time}")
            
            # End of day report
            end_of_day_time = self.schedule_config.get('end_of_day_report', '16:00')
            schedule.every().day.at(end_of_day_time).do(
                lambda: asyncio.run(self.run_end_of_day_report())
            )
            self.logger.info(f"Scheduled end of day report for {end_of_day_time}")
            
            self.logger.info("Scheduled tasks setup completed")
            
        except Exception as e:
            self.logger.error("Error setting up scheduled tasks", error=str(e))
    
    async def run_scheduled_tasks(self):
        """Run scheduled tasks"""
        try:
            # Run initial analysis immediately
            self.logger.info("Running initial market analysis...")
            await self.run_market_analysis()
            
            # Then wait for scheduled tasks
            while self.running:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            self.logger.error("Error in scheduled tasks", error=str(e))
    
    async def run_manual_analysis(self):
        """Run manual analysis on demand"""
        try:
            self.logger.info("Running manual analysis...")
            
            success = await self.run_market_analysis()
            
            if success:
                self.logger.info("Manual analysis completed successfully")
            else:
                self.logger.warning("Manual analysis completed with issues")
            
            return success
            
        except Exception as e:
            self.logger.error("Error in manual analysis", error=str(e))
            return False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Main run loop"""
        try:
            self.logger.info("Starting AI Trading Bot...")
            
            # Initialize
            if not await self.initialize():
                self.logger.error("Failed to initialize AI Trading Bot")
                return False
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Setup schedule
            self.setup_schedule()
            
            # Set running flag
            self.running = True
            
            self.logger.info("AI Trading Bot started successfully")
            
            # Run scheduled tasks
            await self.run_scheduled_tasks()
            
        except Exception as e:
            self.logger.error("Error in main run loop", error=str(e))
            return False
        finally:
            self.logger.info("AI Trading Bot stopped")
    
    async def run_once(self):
        """Run the bot once and exit"""
        try:
            self.logger.info("Running AI Trading Bot once...")
            
            # Initialize
            if not await self.initialize():
                self.logger.error("Failed to initialize AI Trading Bot")
                return False
            
            # Run analysis once
            success = await self.run_market_analysis()
            
            if success:
                self.logger.info("Single run completed successfully")
            else:
                self.logger.warning("Single run completed with issues")
            
            return success
            
        except Exception as e:
            self.logger.error("Error in single run", error=str(e))
            return False

async def main():
    """Main entry point"""
    try:
        # Check if running in continuous mode or single run
        run_mode = os.getenv('RUN_MODE', 'once')  # Default to 'once' to avoid getting stuck
        
        # Create bot instance
        bot = AITradingBot()
        
        if run_mode == 'once':
            # Run once and exit
            await bot.run_once()
        else:
            # Run continuously
            await bot.run()
            
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
