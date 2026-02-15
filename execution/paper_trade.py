from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum


class TradeStatus(Enum):
    """Enumeration for trade status states."""
    OPEN = "OPEN"
    CLOSED_PROFIT = "CLOSED_PROFIT"
    CLOSED_LOSS = "CLOSED_LOSS"
    CLOSED_STOPPED = "CLOSED_STOPPED"


class Trade:
    """
    Represents a single trade with entry, exit, and PnL tracking.
    """
    
    def __init__(
        self,
        trade_id: str,
        entry_price: float,
        stop_loss: float,
        target_price: float,
        quantity: float = 1.0,
        entry_time: Optional[datetime] = None
    ):
        """
        Initialize a trade.
        
        Parameters:
        -----------
        trade_id : str
            Unique identifier for the trade
        entry_price : float
            Price at which the trade was entered
        stop_loss : float
            Stop loss price (must be below entry_price for long trades)
        target_price : float
            Target profit price (must be above entry_price for long trades)
        quantity : float
            Number of units/shares traded (default: 1.0)
        entry_time : datetime, optional
            Timestamp of trade entry (default: current time)
        """
        self.trade_id = trade_id
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.target_price = target_price
        self.quantity = quantity
        self.entry_time = entry_time or datetime.now()
        
        self.exit_price: Optional[float] = None
        self.exit_time: Optional[datetime] = None
        self.status: TradeStatus = TradeStatus.OPEN
        self.pnl: Optional[float] = None
        self.pnl_percent: Optional[float] = None
        self.exit_reason: Optional[str] = None
    
    def close_at_target(self, exit_time: Optional[datetime] = None):
        """
        Close trade at target price (profit).
        
        Parameters:
        -----------
        exit_time : datetime, optional
            Timestamp of trade exit (default: current time)
        """
        self.exit_price = self.target_price
        self.exit_time = exit_time or datetime.now()
        self.status = TradeStatus.CLOSED_PROFIT
        self.exit_reason = "TARGET_HIT"
        self._calculate_pnl()
    
    def close_at_stop_loss(self, exit_time: Optional[datetime] = None):
        """
        Close trade at stop loss price (loss).
        
        Parameters:
        -----------
        exit_time : datetime, optional
            Timestamp of trade exit (default: current time)
        """
        self.exit_price = self.stop_loss
        self.exit_time = exit_time or datetime.now()
        self.status = TradeStatus.CLOSED_STOPPED
        self.exit_reason = "STOP_LOSS_HIT"
        self._calculate_pnl()
    
    def close_at_price(
        self,
        exit_price: float,
        exit_time: Optional[datetime] = None,
        reason: str = "MANUAL_EXIT"
    ):
        """
        Close trade at a specific price.
        
        Parameters:
        -----------
        exit_price : float
            Price at which to exit the trade
        exit_time : datetime, optional
            Timestamp of trade exit (default: current time)
        reason : str
            Reason for closing the trade (default: "MANUAL_EXIT")
        """
        self.exit_price = exit_price
        self.exit_time = exit_time or datetime.now()
        self.exit_reason = reason
        self._calculate_pnl()
        
        # Determine status based on exit price
        if exit_price >= self.target_price:
            self.status = TradeStatus.CLOSED_PROFIT
        elif exit_price <= self.stop_loss:
            self.status = TradeStatus.CLOSED_STOPPED
        else:
            self.status = TradeStatus.CLOSED_LOSS
    
    def _calculate_pnl(self):
        """Calculate profit/loss based on entry and exit prices."""
        if self.exit_price is None:
            return
        
        price_diff = self.exit_price - self.entry_price
        self.pnl = price_diff * self.quantity
        self.pnl_percent = (price_diff / self.entry_price) * 100
    
    def is_open(self) -> bool:
        """Check if trade is still open."""
        return self.status == TradeStatus.OPEN
    
    def get_details(self) -> Dict:
        """
        Get detailed information about the trade.
        
        Returns:
        --------
        dict
            Dictionary containing all trade details
        """
        return {
            'trade_id': self.trade_id,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time,
            'stop_loss': self.stop_loss,
            'target_price': self.target_price,
            'quantity': self.quantity,
            'status': self.status.value,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'exit_reason': self.exit_reason
        }


class PaperTrader:
    """
    Simulates trading with entry prices, fixed stop loss, and fixed targets.
    
    Tracks all trades and their PnL for backtesting and strategy evaluation.
    """
    
    def __init__(self):
        """Initialize the PaperTrader."""
        self.trades: List[Trade] = []
        self.open_trades: Dict[str, Trade] = {}
        self.closed_trades: List[Trade] = []
        self.total_pnl = 0.0
    
    def enter_trade(
        self,
        trade_id: str,
        entry_price: float,
        stop_loss: float,
        target_price: float,
        quantity: float = 1.0,
        entry_time: Optional[datetime] = None
    ) -> Trade:
        """
        Enter a new trade.
        
        Parameters:
        -----------
        trade_id : str
            Unique identifier for the trade
        entry_price : float
            Price at which to enter the trade
        stop_loss : float
            Stop loss price (should be below entry_price for long trades)
        target_price : float
            Target profit price (should be above entry_price for long trades)
        quantity : float
            Number of units/shares to trade (default: 1.0)
        entry_time : datetime, optional
            Timestamp of trade entry (default: current time)
        
        Returns:
        --------
        Trade
            The created Trade object
        
        Raises:
        -------
        ValueError
            If trade_id already exists or if parameters are invalid
        
        Example:
        --------
        >>> trader = PaperTrader()
        >>> trade = trader.enter_trade(
        ...     trade_id="TRADE_001",
        ...     entry_price=100.0,
        ...     stop_loss=95.0,
        ...     target_price=110.0,
        ...     quantity=10
        ... )
        >>> trade.is_open()
        True
        """
        # Validate trade_id is unique
        if trade_id in self.open_trades or any(t.trade_id == trade_id for t in self.closed_trades):
            raise ValueError(f"Trade with ID '{trade_id}' already exists")
        
        # Validate parameters
        if entry_price <= 0:
            raise ValueError("entry_price must be positive")
        if stop_loss <= 0:
            raise ValueError("stop_loss must be positive")
        if target_price <= 0:
            raise ValueError("target_price must be positive")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if stop_loss >= entry_price:
            raise ValueError("stop_loss must be below entry_price for long trades")
        if target_price <= entry_price:
            raise ValueError("target_price must be above entry_price for long trades")
        
        # Create and store trade
        trade = Trade(
            trade_id=trade_id,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            quantity=quantity,
            entry_time=entry_time
        )
        
        self.trades.append(trade)
        self.open_trades[trade_id] = trade
        
        return trade
    
    def exit_trade_at_target(
        self,
        trade_id: str,
        exit_time: Optional[datetime] = None
    ) -> bool:
        """
        Exit a trade at its target price.
        
        Parameters:
        -----------
        trade_id : str
            ID of the trade to exit
        exit_time : datetime, optional
            Timestamp of trade exit (default: current time)
        
        Returns:
        --------
        bool
            True if trade was closed successfully, False if trade not found
        
        Example:
        --------
        >>> trader = PaperTrader()
        >>> trader.enter_trade("T001", 100.0, 95.0, 110.0)
        >>> trader.exit_trade_at_target("T001")
        True
        """
        if trade_id not in self.open_trades:
            return False
        
        trade = self.open_trades[trade_id]
        trade.close_at_target(exit_time)
        self._move_to_closed(trade_id)
        return True
    
    def exit_trade_at_stop_loss(
        self,
        trade_id: str,
        exit_time: Optional[datetime] = None
    ) -> bool:
        """
        Exit a trade at its stop loss price.
        
        Parameters:
        -----------
        trade_id : str
            ID of the trade to exit
        exit_time : datetime, optional
            Timestamp of trade exit (default: current time)
        
        Returns:
        --------
        bool
            True if trade was closed successfully, False if trade not found
        
        Example:
        --------
        >>> trader = PaperTrader()
        >>> trader.enter_trade("T001", 100.0, 95.0, 110.0)
        >>> trader.exit_trade_at_stop_loss("T001")
        True
        """
        if trade_id not in self.open_trades:
            return False
        
        trade = self.open_trades[trade_id]
        trade.close_at_stop_loss(exit_time)
        self._move_to_closed(trade_id)
        return True
    
    def exit_trade_at_price(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: Optional[datetime] = None,
        reason: str = "MANUAL_EXIT"
    ) -> bool:
        """
        Exit a trade at a specific price.
        
        Parameters:
        -----------
        trade_id : str
            ID of the trade to exit
        exit_price : float
            Price at which to exit the trade
        exit_time : datetime, optional
            Timestamp of trade exit (default: current time)
        reason : str
            Reason for closing the trade (default: "MANUAL_EXIT")
        
        Returns:
        --------
        bool
            True if trade was closed successfully, False if trade not found
        
        Example:
        --------
        >>> trader = PaperTrader()
        >>> trader.enter_trade("T001", 100.0, 95.0, 110.0)
        >>> trader.exit_trade_at_price("T001", 105.0)
        True
        """
        if trade_id not in self.open_trades:
            return False
        
        trade = self.open_trades[trade_id]
        trade.close_at_price(exit_price, exit_time, reason)
        self._move_to_closed(trade_id)
        return True
    
    def _move_to_closed(self, trade_id: str):
        """Move a trade from open to closed list and update total PnL."""
        trade = self.open_trades.pop(trade_id)
        self.closed_trades.append(trade)
        
        if trade.pnl is not None:
            self.total_pnl += trade.pnl
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """
        Get a trade by its ID.
        
        Parameters:
        -----------
        trade_id : str
            ID of the trade to retrieve
        
        Returns:
        --------
        Trade or None
            The Trade object if found, None otherwise
        """
        if trade_id in self.open_trades:
            return self.open_trades[trade_id]
        
        for trade in self.closed_trades:
            if trade.trade_id == trade_id:
                return trade
        
        return None
    
    def get_open_trades(self) -> List[Trade]:
        """
        Get all currently open trades.
        
        Returns:
        --------
        list
            List of open Trade objects
        """
        return list(self.open_trades.values())
    
    def get_closed_trades(self) -> List[Trade]:
        """
        Get all closed trades.
        
        Returns:
        --------
        list
            List of closed Trade objects
        """
        return self.closed_trades.copy()
    
    def get_all_trades(self) -> List[Trade]:
        """
        Get all trades (open and closed).
        
        Returns:
        --------
        list
            List of all Trade objects
        """
        return self.trades.copy()
    
    def get_pnl_list(self) -> List[float]:
        """
        Get list of PnL values for all closed trades.
        
        Returns:
        --------
        list
            List of PnL values (only from closed trades)
        
        Example:
        --------
        >>> trader = PaperTrader()
        >>> trader.enter_trade("T001", 100.0, 95.0, 110.0, quantity=10)
        >>> trader.exit_trade_at_target("T001")
        >>> pnl_list = trader.get_pnl_list()
        >>> pnl_list
        [100.0]
        """
        return [trade.pnl for trade in self.closed_trades if trade.pnl is not None]
    
    def get_total_pnl(self) -> float:
        """
        Get total PnL from all closed trades.
        
        Returns:
        --------
        float
            Cumulative profit/loss
        
        Example:
        --------
        >>> trader = PaperTrader()
        >>> trader.enter_trade("T001", 100.0, 95.0, 110.0, quantity=10)
        >>> trader.exit_trade_at_target("T001")
        >>> trader.get_total_pnl()
        100.0
        """
        return self.total_pnl
    
    def get_win_rate(self) -> float:
        """
        Get win rate as a percentage.
        
        Returns:
        --------
        float
            Percentage of winning trades (0-100), or 0 if no closed trades
        
        Example:
        --------
        >>> trader = PaperTrader()
        >>> trader.enter_trade("T001", 100.0, 95.0, 110.0)
        >>> trader.exit_trade_at_target("T001")
        >>> trader.enter_trade("T002", 100.0, 95.0, 110.0)
        >>> trader.exit_trade_at_stop_loss("T002")
        >>> trader.get_win_rate()
        50.0
        """
        if not self.closed_trades:
            return 0.0
        
        winning_trades = sum(1 for trade in self.closed_trades if trade.pnl is not None and trade.pnl > 0)
        return (winning_trades / len(self.closed_trades)) * 100
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive trading statistics.
        
        Returns:
        --------
        dict
            Dictionary containing:
            - total_trades: int total number of trades
            - open_trades: int number of currently open trades
            - closed_trades: int number of closed trades
            - total_pnl: float cumulative profit/loss
            - win_rate: float winning percentage
            - avg_win: float average profit per winning trade
            - avg_loss: float average loss per losing trade
            - profit_factor: float ratio of gross profit to gross loss
        
        Example:
        --------
        >>> trader = PaperTrader()
        >>> trader.enter_trade("T001", 100.0, 95.0, 110.0, quantity=10)
        >>> trader.exit_trade_at_target("T001")
        >>> stats = trader.get_statistics()
        >>> stats['total_pnl']
        100.0
        """
        closed_pnls = self.get_pnl_list()
        
        if not closed_pnls:
            return {
                'total_trades': len(self.trades),
                'open_trades': len(self.open_trades),
                'closed_trades': len(self.closed_trades),
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0
            }
        
        winning_pnls = [pnl for pnl in closed_pnls if pnl > 0]
        losing_pnls = [pnl for pnl in closed_pnls if pnl < 0]
        
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0.0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0.0
        
        gross_profit = sum(winning_pnls)
        gross_loss = abs(sum(losing_pnls))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        return {
            'total_trades': len(self.trades),
            'open_trades': len(self.open_trades),
            'closed_trades': len(self.closed_trades),
            'total_pnl': self.total_pnl,
            'win_rate': self.get_win_rate(),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }
