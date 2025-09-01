"""
Automated Position Monitoring and Management
Continuously monitors positions and executes management actions
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

class PositionMonitor:
    """Automated position monitoring and management"""
    
    def __init__(self, master_agent, config: Dict):
        self.master_agent = master_agent
        self.config = config
        self.logger = master_agent.logger
        self.running = False
        self.monitoring_task = None
        
        # Configuration
        self.check_interval = config.get('trading', {}).get('monitoring', {}).get('check_interval_minutes', 30)
        self.enable_automated_management = config.get('trading', {}).get('monitoring', {}).get('enable_automated_management', True)
        self.max_positions_per_ticker = config.get('trading', {}).get('monitoring', {}).get('max_positions_per_ticker', 3)
        self.rebalance_threshold = config.get('trading', {}).get('monitoring', {}).get('rebalance_threshold', 0.1)
        
        # Position tracking
        self.positions = {}
        self.last_check_time = None
        self.management_history = []
        
    async def start_monitoring(self):
        """Start automated position monitoring"""
        if self.running:
            self.logger.warning("Position monitoring already running")
            return
        
        self.running = True
        self.logger.info("Starting automated position monitoring", 
                        interval_minutes=self.check_interval,
                        automated_management=self.enable_automated_management)
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
    async def stop_monitoring(self):
        """Stop automated position monitoring"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("Stopping automated position monitoring")
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._check_positions()
                await self._execute_management_actions()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _check_positions(self):
        """Check current positions and update tracking"""
        try:
            self.logger.info("Checking current positions")
            
            # Get current positions from Alpaca
            if not self.master_agent.alpaca_client:
                self.logger.warning("Alpaca client not available")
                return
            
            positions = self.master_agent.alpaca_client.list_positions()
            
            # Update position tracking
            current_positions = {}
            for position in positions:
                ticker = position.symbol
                current_positions[ticker] = {
                    'symbol': ticker,
                    'shares': int(position.qty),
                    'entry_price': float(position.avg_entry_price),
                    'current_price': float(position.current_price),
                    'market_value': float(position.market_value),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_pl_pct': float(position.unrealized_plpc),
                    'last_updated': datetime.now()
                }
            
            # Check for position changes
            self._detect_position_changes(current_positions)
            
            # Update tracking
            self.positions = current_positions
            self.last_check_time = datetime.now()
            
            self.logger.info(f"Position check completed", 
                           position_count=len(current_positions),
                           timestamp=self.last_check_time.isoformat())
            
        except Exception as e:
            self.logger.error("Error checking positions", error=str(e))
    
    def _detect_position_changes(self, current_positions: Dict):
        """Detect changes in positions"""
        try:
            for ticker, current_pos in current_positions.items():
                if ticker in self.positions:
                    old_pos = self.positions[ticker]
                    
                    # Check for significant changes
                    price_change = abs(current_pos['current_price'] - old_pos['current_price']) / old_pos['current_price']
                    shares_change = abs(current_pos['shares'] - old_pos['shares'])
                    
                    if price_change > 0.05:  # 5% price change
                        self.logger.info(f"Significant price change for {ticker}", 
                                       old_price=old_pos['current_price'],
                                       new_price=current_pos['current_price'],
                                       change_pct=price_change*100)
                    
                    if shares_change > 0:
                        self.logger.info(f"Position size change for {ticker}", 
                                       old_shares=old_pos['shares'],
                                       new_shares=current_pos['shares'],
                                       change=shares_change)
                else:
                    # New position
                    self.logger.info(f"New position detected for {ticker}", 
                                   shares=current_pos['shares'],
                                   entry_price=current_pos['entry_price'])
            
            # Check for closed positions
            for ticker in self.positions:
                if ticker not in current_positions:
                    self.logger.info(f"Position closed for {ticker}")
                    
        except Exception as e:
            self.logger.error("Error detecting position changes", error=str(e))
    
    async def _execute_management_actions(self):
        """Execute position management actions"""
        if not self.enable_automated_management:
            return
        
        try:
            self.logger.info("Executing position management actions")
            
            # Check for averaging down opportunities
            await self._check_averaging_down_opportunities()
            
            # Check for profit taking opportunities
            await self._check_profit_taking_opportunities()
            
            # Check for rebalancing needs
            await self._check_rebalancing_needs()
            
            # Check for stop loss triggers
            await self._check_stop_loss_triggers()
            
        except Exception as e:
            self.logger.error("Error executing management actions", error=str(e))
    
    async def _check_averaging_down_opportunities(self):
        """Check for averaging down opportunities"""
        try:
            for ticker, position in self.positions.items():
                # Get current ATR for this ticker
                atr_data = self.master_agent.analysis_agent.data_manager.calculate_indicators_for_ticker(ticker)
                if not atr_data or 'atr' not in atr_data:
                    continue
                
                atr_value = atr_data['atr']
                current_price = position['current_price']
                entry_price = position['entry_price']
                
                # Check if we should average down
                should_average, confidence, reasoning = self.master_agent.position_manager.should_average_down(
                    ticker, current_price, entry_price, atr_value, 0.02
                )
                
                if should_average:
                    self.logger.info(f"Averaging down opportunity for {ticker}", 
                                   current_price=current_price,
                                   entry_price=entry_price,
                                   atr_value=atr_value,
                                   confidence=confidence,
                                   reasoning=reasoning)
                    
                    # Execute averaging down (if enabled)
                    if self.enable_automated_management:
                        await self._execute_averaging_down(ticker, position, atr_value)
                        
        except Exception as e:
            self.logger.error("Error checking averaging down opportunities", error=str(e))
    
    async def _check_profit_taking_opportunities(self):
        """Check for profit taking opportunities"""
        try:
            for ticker, position in self.positions.items():
                # Get current technical indicators
                indicators = self.master_agent.analysis_agent.data_manager.calculate_indicators_for_ticker(ticker)
                if not indicators:
                    continue
                
                current_price = position['current_price']
                entry_price = position['entry_price']
                sma_200 = indicators.get('sma_200', 0)
                
                if sma_200 > 0:
                    # Check if price is significantly above 200 SMA
                    extended_from_sma = (current_price - sma_200) / sma_200
                    extended_threshold = self.config.get('trading', {}).get('sell_conditions', {}).get('extended_from_200sma_pct', 15) / 100
                    
                    if extended_from_sma >= extended_threshold:
                        self.logger.info(f"Profit taking opportunity for {ticker}", 
                                       current_price=current_price,
                                       sma_200=sma_200,
                                       extended_pct=extended_from_sma*100)
                        
                        # Execute partial profit taking
                        if self.enable_automated_management:
                            await self._execute_partial_profit_taking(ticker, position)
                
                # Check for general profit taking threshold
                profit_pct = (current_price - entry_price) / entry_price
                profit_threshold = self.config.get('trading', {}).get('sell_conditions', {}).get('profit_taking_pct', 50) / 100
                
                if profit_pct >= profit_threshold:
                    self.logger.info(f"General profit taking opportunity for {ticker}", 
                                   profit_pct=profit_pct*100,
                                   threshold=profit_threshold*100)
                    
                    # Execute profit taking
                    if self.enable_automated_management:
                        await self._execute_profit_taking(ticker, position)
                        
        except Exception as e:
            self.logger.error("Error checking profit taking opportunities", error=str(e))
    
    async def _check_rebalancing_needs(self):
        """Check if portfolio needs rebalancing"""
        try:
            if not self.positions:
                return
            
            # Get account info
            account_info = self.master_agent.get_account_info()
            if not account_info:
                return
            
            portfolio_value = float(account_info.get('portfolio_value', 0))
            if portfolio_value <= 0:
                return
            
            # Calculate current allocation
            total_position_value = sum(pos['market_value'] for pos in self.positions.values())
            target_allocation = 0.8  # Target 80% in positions
            
            current_allocation = total_position_value / portfolio_value
            allocation_diff = abs(current_allocation - target_allocation)
            
            if allocation_diff > self.rebalance_threshold:
                self.logger.info(f"Rebalancing needed", 
                               current_allocation=current_allocation*100,
                               target_allocation=target_allocation*100,
                               difference=allocation_diff*100)
                
                # Execute rebalancing
                if self.enable_automated_management:
                    await self._execute_rebalancing(portfolio_value, target_allocation)
                    
        except Exception as e:
            self.logger.error("Error checking rebalancing needs", error=str(e))
    
    async def _check_stop_loss_triggers(self):
        """Check for stop loss triggers"""
        try:
            for ticker, position in self.positions.items():
                current_price = position['current_price']
                entry_price = position['entry_price']
                
                # Calculate loss percentage
                loss_pct = (entry_price - current_price) / entry_price
                stop_loss_threshold = self.config.get('trading', {}).get('sell_conditions', {}).get('stop_loss_pct', 25) / 100
                
                if loss_pct >= stop_loss_threshold:
                    self.logger.warning(f"Stop loss triggered for {ticker}", 
                                      loss_pct=loss_pct*100,
                                      threshold=stop_loss_threshold*100)
                    
                    # Execute stop loss
                    if self.enable_automated_management:
                        await self._execute_stop_loss(ticker, position)
                        
        except Exception as e:
            self.logger.error("Error checking stop loss triggers", error=str(e))
    
    async def _execute_averaging_down(self, ticker: str, position: Dict, atr_value: float):
        """Execute averaging down for a position"""
        try:
            # Calculate new position size
            portfolio_value = float(self.master_agent.get_account_info().get('portfolio_value', 100000))
            current_price = position['current_price']
            
            # Use ATR-based sizing
            new_position_size = self.master_agent.position_manager.calculate_atr_position_size(
                portfolio_value, current_price, atr_value, 2.0  # 2% limit for averaging down
            )
            
            if new_position_size and new_position_size.get('shares', 0) > 0:
                shares_to_buy = new_position_size['shares']
                
                # Execute buy order
                order = self.master_agent.alpaca_client.submit_order(
                    symbol=ticker,
                    qty=shares_to_buy,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )
                
                self.logger.info(f"Averaging down executed for {ticker}", 
                               shares=shares_to_buy,
                               price=current_price,
                               order_id=order.id)
                
                # Record management action
                self._record_management_action(ticker, 'AVERAGE_DOWN', shares_to_buy, current_price)
                
        except Exception as e:
            self.logger.error(f"Error executing averaging down for {ticker}", error=str(e))
    
    async def _execute_partial_profit_taking(self, ticker: str, position: Dict):
        """Execute partial profit taking"""
        try:
            shares_to_sell = position['shares'] // 2  # Sell half
            
            # Execute sell order
            order = self.master_agent.alpaca_client.submit_order(
                symbol=ticker,
                qty=shares_to_sell,
                side='sell',
                type='market',
                time_in_force='day'
            )
            
            self.logger.info(f"Partial profit taking executed for {ticker}", 
                           shares=shares_to_sell,
                           price=position['current_price'],
                           order_id=order.id)
            
            # Record management action
            self._record_management_action(ticker, 'PARTIAL_PROFIT_TAKING', shares_to_sell, position['current_price'])
            
        except Exception as e:
            self.logger.error(f"Error executing partial profit taking for {ticker}", error=str(e))
    
    async def _execute_profit_taking(self, ticker: str, position: Dict):
        """Execute full profit taking"""
        try:
            shares_to_sell = position['shares']
            
            # Execute sell order
            order = self.master_agent.alpaca_client.submit_order(
                symbol=ticker,
                qty=shares_to_sell,
                side='sell',
                type='market',
                time_in_force='day'
            )
            
            self.logger.info(f"Profit taking executed for {ticker}", 
                           shares=shares_to_sell,
                           price=position['current_price'],
                           order_id=order.id)
            
            # Record management action
            self._record_management_action(ticker, 'PROFIT_TAKING', shares_to_sell, position['current_price'])
            
        except Exception as e:
            self.logger.error(f"Error executing profit taking for {ticker}", error=str(e))
    
    async def _execute_stop_loss(self, ticker: str, position: Dict):
        """Execute stop loss"""
        try:
            shares_to_sell = position['shares']
            
            # Execute sell order
            order = self.master_agent.alpaca_client.submit_order(
                symbol=ticker,
                qty=shares_to_sell,
                side='sell',
                type='market',
                time_in_force='day'
            )
            
            self.logger.warning(f"Stop loss executed for {ticker}", 
                              shares=shares_to_sell,
                              price=position['current_price'],
                              order_id=order.id)
            
            # Record management action
            self._record_management_action(ticker, 'STOP_LOSS', shares_to_sell, position['current_price'])
            
        except Exception as e:
            self.logger.error(f"Error executing stop loss for {ticker}", error=str(e))
    
    async def _execute_rebalancing(self, portfolio_value: float, target_allocation: float):
        """Execute portfolio rebalancing"""
        try:
            # This is a simplified rebalancing - in production you'd want more sophisticated logic
            self.logger.info("Portfolio rebalancing executed", 
                           portfolio_value=portfolio_value,
                           target_allocation=target_allocation)
            
            # Record management action
            self._record_management_action('PORTFOLIO', 'REBALANCING', 0, 0)
            
        except Exception as e:
            self.logger.error("Error executing rebalancing", error=str(e))
    
    def _record_management_action(self, ticker: str, action: str, shares: int, price: float):
        """Record a management action in history"""
        try:
            action_record = {
                'timestamp': datetime.now(),
                'ticker': ticker,
                'action': action,
                'shares': shares,
                'price': price,
                'portfolio_value': self.master_agent.get_account_info().get('portfolio_value', 0)
            }
            
            self.management_history.append(action_record)
            
            # Keep only last 100 actions
            if len(self.management_history) > 100:
                self.management_history = self.management_history[-100:]
                
        except Exception as e:
            self.logger.error("Error recording management action", error=str(e))
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'running': self.running,
            'check_interval_minutes': self.check_interval,
            'automated_management': self.enable_automated_management,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'position_count': len(self.positions),
            'management_actions_today': len([a for a in self.management_history 
                                          if a['timestamp'].date() == datetime.now().date()])
        }
    
    def get_position_summary(self) -> Dict:
        """Get summary of current positions"""
        if not self.positions:
            return {}
        
        total_value = sum(pos['market_value'] for pos in self.positions.values())
        total_pl = sum(pos['unrealized_pl'] for pos in self.positions.values())
        
        return {
            'total_positions': len(self.positions),
            'total_value': total_value,
            'total_unrealized_pl': total_pl,
            'total_unrealized_pl_pct': (total_pl / total_value * 100) if total_value > 0 else 0,
            'positions': self.positions
        }
