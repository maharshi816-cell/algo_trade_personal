from datetime import datetime, time
from typing import Optional


class RiskManager:
    """
    Manages trading risk by tracking daily PnL and enforcing daily loss limits.
    
    This class monitors cumulative profit/loss throughout the trading day and
    prevents new trades once the maximum daily loss threshold is breached.
    """
    
    def __init__(self, max_daily_loss: float):
        """
        Initialize the RiskManager.
        
        Parameters:
        -----------
        max_daily_loss : float
            Maximum allowed daily loss (in currency units, e.g., dollars).
            For example, -1000 means stop trading if daily loss exceeds $1000.
        
        Raises:
        -------
        ValueError
            If max_daily_loss is not negative (loss limit should be negative).
        """
        if max_daily_loss >= 0:
            raise ValueError("max_daily_loss must be negative (e.g., -1000)")
        
        self.max_daily_loss = max_daily_loss
        self.daily_pnl = 0.0
        self.trading_allowed = True
        self.session_date = datetime.now().date()
        self.trades = []
    
    def _check_date_reset(self):
        """
        Check if the trading day has changed and reset PnL if needed.
        This allows the risk manager to track PnL per trading day.
        """
        current_date = datetime.now().date()
        if current_date != self.session_date:
            self.reset_daily_pnl()
            self.session_date = current_date
    
    def reset_daily_pnl(self):
        """
        Reset daily PnL and re-enable trading.
        
        This method is typically called at the start of each trading day.
        """
        self.daily_pnl = 0.0
        self.trading_allowed = True
        self.trades = []
    
    def update_pnl(self, pnl: float, trade_id: Optional[str] = None) -> bool:
        """
        Update daily PnL after a trade execution.
        
        Parameters:
        -----------
        pnl : float
            Profit or loss from the trade (positive for profit, negative for loss)
        trade_id : str, optional
            Identifier for the trade (for tracking purposes)
        
        Returns:
        --------
        bool
            True if PnL was updated successfully, False if trade was rejected
            due to max daily loss limit being breached.
        
        Example:
        --------
        >>> risk_mgr = RiskManager(max_daily_loss=-1000)
        >>> risk_mgr.update_pnl(-500)  # Loss of $500
        True
        >>> risk_mgr.update_pnl(-600)  # Total loss would be $1100 > $1000 limit
        False
        """
        self._check_date_reset()
        
        # Check if trading is allowed before updating
        if not self.trading_allowed:
            return False
        
        # Calculate what the new PnL would be
        new_pnl = self.daily_pnl + pnl
        
        # Check if this trade would breach the max daily loss limit
        if new_pnl < self.max_daily_loss:
            # Reject the trade - max loss limit would be breached
            return False
        
        # Accept the trade and update PnL
        self.daily_pnl = new_pnl
        
        # Track the trade
        self.trades.append({
            'timestamp': datetime.now(),
            'pnl': pnl,
            'cumulative_pnl': self.daily_pnl,
            'trade_id': trade_id
        })
        
        # Check if we've just breached the limit
        if self.daily_pnl <= self.max_daily_loss:
            self.trading_allowed = False
        
        return True
    
    def is_trading_allowed(self) -> bool:
        """
        Check if trading is currently allowed.
        
        Returns:
        --------
        bool
            True if trading is allowed, False if max daily loss limit is breached.
        
        Example:
        --------
        >>> risk_mgr = RiskManager(max_daily_loss=-1000)
        >>> risk_mgr.is_trading_allowed()
        True
        >>> risk_mgr.daily_pnl = -1000
        >>> risk_mgr.trading_allowed = False
        >>> risk_mgr.is_trading_allowed()
        False
        """
        self._check_date_reset()
        return self.trading_allowed
    
    def get_daily_pnl(self) -> float:
        """
        Get the current daily PnL.
        
        Returns:
        --------
        float
            Current cumulative PnL for the trading day.
        
        Example:
        --------
        >>> risk_mgr = RiskManager(max_daily_loss=-1000)
        >>> risk_mgr.update_pnl(500)
        True
        >>> risk_mgr.get_daily_pnl()
        500.0
        """
        self._check_date_reset()
        return self.daily_pnl
    
    def get_remaining_loss_budget(self) -> float:
        """
        Get the remaining loss budget before hitting the daily loss limit.
        
        Returns:
        --------
        float
            Remaining loss that can be incurred. Negative value indicates
            how much deeper in loss we'd go if this were breached.
        
        Example:
        --------
        >>> risk_mgr = RiskManager(max_daily_loss=-1000)
        >>> risk_mgr.update_pnl(-600)
        True
        >>> risk_mgr.get_remaining_loss_budget()
        -400.0
        """
        self._check_date_reset()
        return self.max_daily_loss - self.daily_pnl
    
    def get_trade_history(self) -> list:
        """
        Get the history of all trades for the current trading day.
        
        Returns:
        --------
        list
            List of trade dictionaries with timestamp, pnl, cumulative_pnl, and trade_id.
        
        Example:
        --------
        >>> risk_mgr = RiskManager(max_daily_loss=-1000)
        >>> risk_mgr.update_pnl(500, trade_id="TRADE_001")
        True
        >>> history = risk_mgr.get_trade_history()
        >>> len(history)
        1
        """
        self._check_date_reset()
        return self.trades.copy()
    
    def get_status(self) -> dict:
        """
        Get a comprehensive status report of the risk manager.
        
        Returns:
        --------
        dict
            Dictionary containing:
            - trading_allowed: bool indicating if trading is currently allowed
            - daily_pnl: float current daily PnL
            - max_daily_loss: float configured maximum daily loss
            - remaining_loss_budget: float remaining loss budget
            - num_trades: int number of trades executed today
            - session_date: date of the current trading session
        
        Example:
        --------
        >>> risk_mgr = RiskManager(max_daily_loss=-1000)
        >>> risk_mgr.update_pnl(250)
        True
        >>> status = risk_mgr.get_status()
        >>> status['trading_allowed']
        True
        >>> status['remaining_loss_budget']
        -750.0
        """
        self._check_date_reset()
        return {
            'trading_allowed': self.trading_allowed,
            'daily_pnl': self.daily_pnl,
            'max_daily_loss': self.max_daily_loss,
            'remaining_loss_budget': self.get_remaining_loss_budget(),
            'num_trades': len(self.trades),
            'session_date': self.session_date
        }
