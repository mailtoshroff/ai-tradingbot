"""
Email utility for sending trading reports and notifications
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import yaml

class EmailSender:
    """Email sender for trading bot notifications"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = None  # Will be set by the calling agent
        
    def set_logger(self, logger):
        """Set logger instance"""
        self.logger = logger
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def _get_email_config(self) -> Dict:
        """Get email configuration from environment or config"""
        email_config = self.config.get('email', {})
        
        # Override with environment variables if available
        return {
            'smtp_server': os.getenv('SMTP_SERVER', email_config.get('smtp_server', 'smtp.gmail.com')),
            'smtp_port': int(os.getenv('SMTP_PORT', email_config.get('smtp_port', 587))),
            'sender_email': os.getenv('SENDER_EMAIL', email_config.get('sender_email', '')),
            'sender_password': os.getenv('SENDER_PASSWORD', email_config.get('sender_password', '')),
            'recipient_emails': os.getenv('RECIPIENT_EMAILS', email_config.get('recipient_emails', '')).split(',')
        }
    
    def send_trading_report(self, trading_signals: List[Dict], portfolio_status: Dict) -> bool:
        """Send comprehensive trading report"""
        try:
            email_config = self._get_email_config()
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = ', '.join(email_config['recipient_emails'])
            msg['Subject'] = f"AI Trading Bot Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Create HTML content
            html_content = self._create_trading_report_html(trading_signals, portfolio_status)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            success = self._send_email(msg, email_config)
            
            if success and self.logger:
                self.logger.info("Trading report email sent successfully", 
                               recipient_count=len(email_config['recipient_emails']))
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error("Error sending trading report email", error=str(e))
            return False
    
    def send_trade_notification(self, ticker: str, action: str, quantity: int, 
                               price: float, reasoning: str) -> bool:
        """Send individual trade notification"""
        try:
            email_config = self._get_email_config()
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = ', '.join(email_config['recipient_emails'])
            msg['Subject'] = f"AI Trading Bot Trade: {action.upper()} {ticker}"
            
            # Create HTML content
            html_content = self._create_trade_notification_html(ticker, action, quantity, price, reasoning)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            success = self._send_email(msg, email_config)
            
            if success and self.logger:
                self.logger.info("Trade notification email sent successfully", 
                               ticker=ticker, action=action)
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error("Error sending trade notification email", error=str(e))
            return False
    
    def send_alert(self, alert_type: str, message: str, details: Optional[Dict] = None) -> bool:
        """Send alert email"""
        try:
            email_config = self._get_email_config()
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = ', '.join(email_config['recipient_emails'])
            msg['Subject'] = f"AI Trading Bot Alert: {alert_type}"
            
            # Create HTML content
            html_content = self._create_alert_html(alert_type, message, details)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            success = self._send_email(msg, email_config)
            
            if success and self.logger:
                self.logger.info("Alert email sent successfully", alert_type=alert_type)
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error("Error sending alert email", error=str(e))
            return False
    
    def _create_trading_report_html(self, trading_signals: List[Dict], 
                                   portfolio_status: Dict) -> str:
        """Create HTML content for trading report"""
        
        # Create comprehensive analysis table (matching terminal output)
        analysis_html = """
        <h3>AI Trading Bot Analysis Results</h3>
        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 12px;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 8px; text-align: left;">Ticker</th>
                <th style="padding: 8px; text-align: left;">Tech Signals</th>
                <th style="padding: 8px; text-align: left;">Sentiment Score</th>
                <th style="padding: 8px; text-align: left;">Final Decision</th>
                <th style="padding: 8px; text-align: left;">Confidence</th>
                <th style="padding: 8px; text-align: left;">Reasoning</th>
            </tr>
        """
        
        # Add analysis rows (this will be populated by the master agent)
        if trading_signals:
            for signal in trading_signals:
                ticker = signal.get('ticker', 'N/A')
                tech_signals = signal.get('tech_signals', 'None')
                sentiment_score = signal.get('sentiment_score', 'No News')
                final_decision = signal.get('signal', 'HOLD')
                confidence = signal.get('confidence', 0.0)
                reasoning = signal.get('reasoning', 'No signals triggered')
                
                # Color code the decision
                decision_color = "#90EE90" if final_decision == 'BUY' else "#FFB6C1" if final_decision == 'SELL' else "#F0F0F0"
                
                analysis_html += f"""
                <tr>
                    <td style="padding: 6px;"><strong>{ticker}</strong></td>
                    <td style="padding: 6px;">{tech_signals}</td>
                    <td style="padding: 6px;">{sentiment_score}</td>
                    <td style="padding: 6px; background-color: {decision_color};"><strong>{final_decision}</strong></td>
                    <td style="padding: 6px;">{confidence:.2f}</td>
                    <td style="padding: 6px;">{reasoning[:60]}...</td>
                </tr>
                """
        else:
            # No signals case - show summary
            analysis_html += """
            <tr>
                <td colspan="6" style="padding: 8px; text-align: center; background-color: #f9f9f9;">
                    <em>No actionable trading signals generated - All positions on HOLD</em>
                </td>
            </tr>
            """
        
        analysis_html += "</table>"
        
        # Create portfolio summary table
        portfolio_summary_html = ""
        if portfolio_status and not portfolio_status.get('error'):
            portfolio_summary_html = f"""
            <h3>Portfolio Summary</h3>
            <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 8px; text-align: left;">Metric</th>
                    <th style="padding: 8px; text-align: left;">Value</th>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Total Portfolio Value</strong></td>
                    <td style="padding: 8px; background-color: #90EE90;">${portfolio_status.get('total_value', 0):,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Cash Available</strong></td>
                    <td style="padding: 8px;">${portfolio_status.get('cash', 0):,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Buying Power</strong></td>
                    <td style="padding: 8px;">${portfolio_status.get('buying_power', 0):,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Day Trade Count</strong></td>
                    <td style="padding: 8px;">{portfolio_status.get('day_trade_count', 0)}</td>
                </tr>
            </table>
            """
        
        # Create positions table
        positions_html = ""
        if portfolio_status and portfolio_status.get('positions'):
            positions_html = """
            <h3>Current Positions</h3>
            <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 8px; text-align: left;">Ticker</th>
                    <th style="padding: 8px; text-align: left;">Quantity</th>
                    <th style="padding: 8px; text-align: left;">Avg Entry Price</th>
                    <th style="padding: 8px; text-align: left;">Current Price</th>
                    <th style="padding: 8px; text-align: left;">Market Value</th>
                    <th style="padding: 8px; text-align: left;">Unrealized P&L</th>
                </tr>
            """
            
            for ticker, position in portfolio_status['positions'].items():
                # Get position data with proper error handling
                quantity = position.get('quantity', 0)
                avg_price = position.get('avg_entry_price', 0)
                current_price = position.get('current_price', 0)
                market_value = position.get('market_value', 0)
                unrealized_pl = position.get('unrealized_pl', 0)
                
                # Color code P&L
                pnl_color = "#90EE90" if unrealized_pl >= 0 else "#FFB6C1"
                
                positions_html += f"""
                <tr>
                    <td style="padding: 6px;"><strong>{ticker}</strong></td>
                    <td style="padding: 6px;">{quantity:,}</td>
                    <td style="padding: 6px;">${avg_price:.2f}</td>
                    <td style="padding: 6px;">${current_price:.2f}</td>
                    <td style="padding: 6px;">${market_value:,.2f}</td>
                    <td style="padding: 6px; background-color: {pnl_color};">${unrealized_pl:,.2f}</td>
                </tr>
                """
            
            positions_html += "</table>"
        elif portfolio_status and portfolio_status.get('error'):
            positions_html = f"""
            <h3>Portfolio Status</h3>
            <p style="color: #FF6B6B;"><strong>Error:</strong> {portfolio_status.get('error', 'Unable to retrieve portfolio data')}</p>
            """
        else:
            positions_html = """
            <h3>Current Positions</h3>
            <p style="color: #666;"><em>No positions currently held</em></p>
            """
        
        # Full HTML template
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h3 {{ color: #666; margin-top: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 AI Trading Bot Analysis Report</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            {analysis_html}
            {portfolio_summary_html}
            {positions_html}
            
            <div class="summary">
                <h3>Report Summary</h3>
                <p><strong>Analysis Status:</strong> {'Completed with ' + str(len(trading_signals)) + ' signals' if trading_signals else 'Completed - No actionable signals'}</p>
                <p><strong>Portfolio Status:</strong> {'Retrieved successfully' if portfolio_status and not portfolio_status.get('error') else 'Error retrieving data'}</p>
                <p><em>This report was automatically generated by the AI Trading Bot based on technical analysis and news sentiment.</em></p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _create_trade_notification_html(self, ticker: str, action: str, 
                                       quantity: int, price: float, reasoning: str) -> str:
        """Create HTML content for trade notification"""
        
        action_color = "#90EE90" if action.upper() == "BUY" else "#FFB6C1"
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .trade-details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .action {{ background-color: {action_color}; padding: 10px; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <h1>🤖 AI Trading Bot Trade Notification</h1>
            
            <div class="trade-details">
                <h3>Trade Details</h3>
                <p><strong>Action:</strong> <span class="action">{action.upper()}</span></p>
                <p><strong>Ticker:</strong> {ticker}</p>
                <p><strong>Quantity:</strong> {quantity}</p>
                <p><strong>Price:</strong> ${price:.2f}</p>
                <p><strong>Total Value:</strong> ${quantity * price:.2f}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="trade-details">
                <h3>AI Reasoning</h3>
                <p>{reasoning}</p>
            </div>
            
            <p><em>This notification was automatically generated by the AI Trading Bot.</em></p>
        </body>
        </html>
        """
        
        return html_template
    
    def _create_alert_html(self, alert_type: str, message: str, details: Optional[Dict] = None) -> str:
        """Create HTML content for alert"""
        
        alert_color = "#FF6B6B" if alert_type.upper() == "ERROR" else "#FFA500"
        
        details_html = ""
        if details:
            details_html = "<h3>Details</h3><ul>"
            for key, value in details.items():
                details_html += f"<li><strong>{key}:</strong> {value}</li>"
            details_html += "</ul>"
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .alert {{ background-color: {alert_color}; color: white; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>🚨 AI Trading Bot Alert</h1>
            
            <div class="alert">
                <h3>{alert_type.upper()}</h3>
                <p>{message}</p>
            </div>
            
            {details_html}
            
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><em>This alert was automatically generated by the AI Trading Bot.</em></p>
        </body>
        </html>
        """
        
        return html_template
    
    def _send_email(self, msg: MIMEMultipart, email_config: Dict) -> bool:
        """Send email using SMTP"""
        try:
            # Create SMTP session
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            
            # Login
            server.login(email_config['sender_email'], email_config['sender_password'])
            
            # Send email
            text = msg.as_string()
            server.sendmail(email_config['sender_email'], email_config['recipient_emails'], text)
            
            # Close connection
            server.quit()
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error("SMTP error", error=str(e), smtp_server=email_config['smtp_server'])
            return False
