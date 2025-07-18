# Kameo API Implementation Examples
*Advanced patterns and real-world usage scenarios*

## 🏗️ Complete Python Implementation

### Full-Featured Kameo Client
```python
import requests
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Loan:
    id: int
    title: str
    amount: int
    interest_rate: float
    duration: int
    current_bids: int
    min_bid: int
    max_bid: int
    funded_percentage: float
    time_remaining: str

@dataclass
class BiddingStatus:
    loan_id: int
    current_bid: int
    min_bid: int
    max_bid: int
    total_bidders: int
    time_remaining: str
    interest_rate: float
    loan_amount: int
    funded_percentage: float

class KameoClient:
    def __init__(self, rate_limit_delay: float = 1.0):
        self.base_url = "https://api.kameo.se/v1"
        self.web_url = "https://www.kameo.se"
        self.headers = {
            "accept-language": "sv",
            "origin": "https://www.kameo.se",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        self.web_headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en;q=0.7",
            "referer": "https://www.kameo.se/investor/dashboard",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request with rate limiting and error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Check rate limiting
            remaining = response.headers.get('x-ratelimit-remaining')
            if remaining and int(remaining) < 5:
                logger.warning(f"Rate limit low: {remaining} requests remaining")
                time.sleep(60)  # Wait for rate limit reset
            
            # Add delay between requests
            time.sleep(self.rate_limit_delay)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response.status_code == 429:
                logger.info("Rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(method, endpoint, **kwargs)
            raise
    
    def get_loans(self, limit: int = 12, page: int = 1, countries: List[str] = None) -> List[Loan]:
        """Get available loans with filtering"""
        params = {
            "subscription_origin_sweden": "1" if not countries or "sweden" in countries else "0",
            "subscription_origin_norway": "1" if countries and "norway" in countries else "0",
            "subscription_origin_denmark": "1" if countries and "denmark" in countries else "0",
            "limit": str(limit),
            "page": str(page)
        }
        
        response = self._make_request("GET", "/loans/listing/investment-options", params=params)
        
        loans = []
        for loan_data in response.get('data', []):
            loan = Loan(
                id=loan_data['id'],
                title=loan_data['title'],
                amount=loan_data['amount'],
                interest_rate=loan_data['interest_rate'],
                duration=loan_data['duration'],
                current_bids=loan_data['current_bids'],
                min_bid=loan_data['min_bid'],
                max_bid=loan_data['max_bid'],
                funded_percentage=loan_data.get('funded_percentage', 0),
                time_remaining=loan_data.get('time_remaining', 'Unknown')
            )
            loans.append(loan)
        
        return loans
    
    def get_bidding_status(self, loan_id: int) -> BiddingStatus:
        """Get current bidding status for a loan"""
        response = self._make_request("GET", f"/bidding/{loan_id}/load")
        
        return BiddingStatus(
            loan_id=response['loan_id'],
            current_bid=response['current_bid'],
            min_bid=response['min_bid'],
            max_bid=response['max_bid'],
            total_bidders=response['total_bidders'],
            time_remaining=response['time_remaining'],
            interest_rate=response['interest_rate'],
            loan_amount=response['loan_amount'],
            funded_percentage=response['funded_percentage']
        )
    
    def preview_bid(self, loan_id: int, amount: int, payment_option: str = "ip") -> Dict:
        """Preview a bid without submitting"""
        data = {
            "amount": str(amount),
            "intention": "add",
            "sequence_hash": "",
            "payment_options": [payment_option]
        }
        
        return self._make_request("POST", f"/bidding/{loan_id}/load", json=data)
    
    def submit_bid(self, loan_id: int, amount: int, sequence_hash: str, payment_option: str = "ip") -> Dict:
        """Submit an actual bid"""
        data = {
            "amount": str(amount),
            "intention": "add",
            "sequence_hash": sequence_hash,
            "payment_options": [payment_option]
        }
        
        return self._make_request("POST", f"/bidding/{loan_id}/submit", json=data)
    
    def subscribe_to_loan(self, loan_id: int) -> Dict:
        """Subscribe to loan updates"""
        data = {
            "data": {
                "subscription": {
                    "subscription_is_open": True,
                    "subscribed_amount": 0,
                    "total_amount": 0,
                    "investment_status": 11,
                    "investment_status_text": "Förhandsteckning"
                }
            }
        }
        
        return self._make_request("POST", f"/loan/subscription/{loan_id}", json=data)
    
    def get_accounts(self) -> Dict:
        """Get user account balances and transfer data"""
        url = f"{self.web_url}/ezjscore/call/kameo_transfer::init"
        
        try:
            response = self.session.get(url, headers=self.web_headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get accounts: {e}")
            raise
    
    def get_available_balance(self, currency: str = "SEK") -> float:
        """Get available balance for specified currency"""
        try:
            accounts = self.get_accounts()
            for account in accounts['content']['data']['accounts']:
                if account['currencyCode'] == currency:
                    return float(account['availableCash'].replace(' ', '').replace(',', '.'))
            return 0.0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0

# Usage example
def main():
    client = KameoClient(rate_limit_delay=1.0)
    
    # Check account balance
    balance = client.get_available_balance("SEK")
    print(f"Available SEK: {balance:,.2f}")
    
    # Get Swedish loans only
    loans = client.get_loans(limit=5, countries=["sweden"])
    print(f"Found {len(loans)} Swedish loans")
    
    for loan in loans:
        print(f"Loan {loan.id}: {loan.title}")
        print(f"  Amount: {loan.amount:,} SEK")
        print(f"  Interest: {loan.interest_rate}%")
        print(f"  Current bids: {loan.current_bids}")
        print(f"  Funded: {loan.funded_percentage}%")
        print()

if __name__ == "__main__":
    main()
```

---

## 💰 Account Management System

### Balance Monitoring & Transfer Management
```python
import json
from datetime import datetime
from typing import Dict, List, Optional

class AccountManager:
    def __init__(self, client: KameoClient):
        self.client = client
        self.logger = logging.getLogger(__name__)
    
    def get_all_accounts(self) -> Dict:
        """Get all user accounts with balances"""
        try:
            accounts_data = self.client.get_accounts()
            return accounts_data['content']['data']
        except Exception as e:
            self.logger.error(f"Failed to get accounts: {e}")
            return {}
    
    def get_account_summary(self) -> Dict:
        """Get summary of all accounts"""
        accounts_data = self.get_all_accounts()
        summary = {
            'total_accounts': len(accounts_data.get('accounts', [])),
            'currencies': {},
            'total_available': 0.0,
            'total_reserved': 0.0,
            'xsrf_token': accounts_data.get('xsrfToken', '')
        }
        
        for account in accounts_data.get('accounts', []):
            currency = account['currencyCode']
            available = float(account['availableCash'].replace(' ', '').replace(',', '.'))
            reserved = float(account['reservedCash'].replace(' ', '').replace(',', '.'))
            
            if currency not in summary['currencies']:
                summary['currencies'][currency] = {
                    'available': 0.0,
                    'reserved': 0.0,
                    'accounts': []
                }
            
            summary['currencies'][currency]['available'] += available
            summary['currencies'][currency]['reserved'] += reserved
            summary['currencies'][currency]['accounts'].append({
                'accountNo': account['accountNo'],
                'available': available,
                'reserved': reserved
            })
            
            summary['total_available'] += available
            summary['total_reserved'] += reserved
        
        return summary
    
    def check_sufficient_balance(self, amount: float, currency: str = "SEK") -> bool:
        """Check if sufficient balance exists for bidding"""
        try:
            available = self.client.get_available_balance(currency)
            return available >= amount
        except Exception as e:
            self.logger.error(f"Error checking balance: {e}")
            return False
    
    def get_bidding_budget(self, currency: str = "SEK", reserve_percentage: float = 0.1) -> float:
        """Calculate available budget for bidding with reserve"""
        try:
            available = self.client.get_available_balance(currency)
            reserve = available * reserve_percentage
            return available - reserve
        except Exception as e:
            self.logger.error(f"Error calculating budget: {e}")
            return 0.0
    
    def log_account_status(self):
        """Log current account status"""
        try:
            summary = self.get_account_summary()
            self.logger.info(f"Account Summary:")
            self.logger.info(f"  Total Accounts: {summary['total_accounts']}")
            self.logger.info(f"  Total Available: {summary['total_available']:,.2f}")
            self.logger.info(f"  Total Reserved: {summary['total_reserved']:,.2f}")
            
            for currency, data in summary['currencies'].items():
                self.logger.info(f"  {currency}: {data['available']:,.2f} available, {data['reserved']:,.2f} reserved")
                
        except Exception as e:
            self.logger.error(f"Error logging account status: {e}")

# Usage example
def account_example():
    client = KameoClient()
    account_manager = AccountManager(client)
    
    # Get account summary
    summary = account_manager.get_account_summary()
    print("Account Summary:")
    print(json.dumps(summary, indent=2))
    
    # Check if we can bid 5000 SEK
    can_bid = account_manager.check_sufficient_balance(5000, "SEK")
    print(f"Can bid 5000 SEK: {can_bid}")
    
    # Get bidding budget with 10% reserve
    budget = account_manager.get_bidding_budget("SEK", 0.1)
    print(f"Bidding budget: {budget:,.2f} SEK")
    
    # Log account status
    account_manager.log_account_status()

if __name__ == "__main__":
    account_example()
```

---

## 🤖 Automated Bidding Bot

### Smart Bidding Strategy
```python
import asyncio
from typing import List, Optional
import random

class AutomatedBiddingBot:
    def __init__(self, client: KameoClient, max_bid_amount: int = 10000):
        self.client = client
        self.max_bid_amount = max_bid_amount
        self.bid_history = []
        self.account_manager = AccountManager(client)
    
    def calculate_optimal_bid(self, loan: Loan, status: BiddingStatus) -> Optional[int]:
        """Calculate optimal bid amount based on strategy"""
        
        # Strategy 1: Minimum bid to get in
        if status.current_bid == 0:
            return status.min_bid
        
        # Strategy 2: Beat current bid by small margin
        current_bid = status.current_bid
        optimal_bid = current_bid + random.randint(100, 500)
        
        # Strategy 3: Don't exceed max bid amount
        if optimal_bid > self.max_bid_amount:
            return None
        
        # Strategy 4: Don't bid if too many competitors
        if status.total_bidders > 20:
            return None
        
        return optimal_bid
    
    def should_bid_on_loan(self, loan: Loan, status: BiddingStatus) -> bool:
        """Determine if we should bid on this loan"""
        
        # Check if loan is attractive
        if loan.interest_rate < 7.0:
            return False  # Too low interest
        
        if loan.funded_percentage > 90:
            return False  # Almost fully funded
        
        if status.total_bidders > 25:
            return False  # Too much competition
        
        if loan.duration > 24:
            return False  # Too long duration
        
        return True
    
    async def monitor_and_bid(self, check_interval: int = 300):
        """Monitor loans and place bids automatically"""
        
        while True:
            try:
                logger.info("Scanning for new loan opportunities...")
                
                # Check account balance first
                available_balance = self.client.get_available_balance("SEK")
                logger.info(f"Available balance: {available_balance:,.2f} SEK")
                
                if available_balance < 1000:
                    logger.warning("Insufficient balance for bidding")
                    await asyncio.sleep(check_interval)
                    continue
                
                # Get all available loans
                loans = self.client.get_loans(limit=20)
                
                for loan in loans:
                    # Get current bidding status
                    status = self.client.get_bidding_status(loan.id)
                    
                    # Check if we should bid
                    if not self.should_bid_on_loan(loan, status):
                        continue
                    
                    # Calculate optimal bid
                    optimal_bid = self.calculate_optimal_bid(loan, status)
                    if not optimal_bid:
                        continue
                    
                    # Check if we have sufficient balance
                    if not self.account_manager.check_sufficient_balance(optimal_bid, "SEK"):
                        logger.warning(f"Insufficient balance for bid {optimal_bid} SEK")
                        continue
                    
                    logger.info(f"Considering bid on loan {loan.id}: {optimal_bid} SEK")
                    
                    # Preview the bid
                    preview = self.client.preview_bid(loan.id, optimal_bid)
                    
                    # Check if bid is still attractive
                    estimated_return = preview.get('estimated_return', 0)
                    if estimated_return < optimal_bid * 0.05:  # Less than 5% return
                        logger.info(f"Bid not attractive enough: {estimated_return} SEK return")
                        continue
                    
                    # Submit the bid
                    sequence_hash = preview.get('sequence_hash')
                    if sequence_hash:
                        result = self.client.submit_bid(loan.id, optimal_bid, sequence_hash)
                        logger.info(f"Bid submitted successfully: {result}")
                        
                        # Record bid
                        self.bid_history.append({
                            'loan_id': loan.id,
                            'amount': optimal_bid,
                            'timestamp': datetime.now(),
                            'result': result
                        })
                
                # Wait before next check
                logger.info(f"Waiting {check_interval} seconds before next scan...")
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

# Usage
async def run_bot():
    client = KameoClient()
    bot = AutomatedBiddingBot(client, max_bid_amount=5000)
    await bot.monitor_and_bid(check_interval=600)  # Check every 10 minutes

# asyncio.run(run_bot())
```

---

## 📊 Loan Analysis & Monitoring

### Advanced Loan Analyzer
```python
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

class LoanAnalyzer:
    def __init__(self, client: KameoClient):
        self.client = client
        self.loan_data = []
    
    def collect_loan_data(self, days: int = 7):
        """Collect loan data over time for analysis"""
        
        for day in range(days):
            logger.info(f"Collecting data for day {day + 1}/{days}")
            
            loans = self.client.get_loans(limit=50)
            
            for loan in loans:
                try:
                    status = self.client.get_bidding_status(loan.id)
                    
                    self.loan_data.append({
                        'date': datetime.now() - timedelta(days=day),
                        'loan_id': loan.id,
                        'title': loan.title,
                        'amount': loan.amount,
                        'interest_rate': loan.interest_rate,
                        'duration': loan.duration,
                        'current_bid': status.current_bid,
                        'total_bidders': status.total_bidders,
                        'funded_percentage': status.funded_percentage,
                        'time_remaining': status.time_remaining
                    })
                    
                except Exception as e:
                    logger.error(f"Error collecting data for loan {loan.id}: {e}")
    
    def analyze_loans(self) -> pd.DataFrame:
        """Analyze collected loan data"""
        
        df = pd.DataFrame(self.loan_data)
        
        # Calculate metrics
        analysis = {
            'total_loans': len(df),
            'avg_interest_rate': df['interest_rate'].mean(),
            'avg_duration': df['duration'].mean(),
            'avg_bidders': df['total_bidders'].mean(),
            'avg_funded_percentage': df['funded_percentage'].mean(),
            'high_interest_loans': len(df[df['interest_rate'] > 8.0]),
            'low_competition_loans': len(df[df['total_bidders'] < 10])
        }
        
        return analysis
    
    def find_best_opportunities(self, min_interest: float = 7.5, max_bidders: int = 15) -> List[Dict]:
        """Find the best loan opportunities"""
        
        df = pd.DataFrame(self.loan_data)
        
        # Filter for good opportunities
        opportunities = df[
            (df['interest_rate'] >= min_interest) &
            (df['total_bidders'] <= max_bidders) &
            (df['funded_percentage'] < 80)
        ].sort_values('interest_rate', ascending=False)
        
        return opportunities.to_dict('records')
    
    def plot_interest_distribution(self):
        """Plot interest rate distribution"""
        
        df = pd.DataFrame(self.loan_data)
        
        plt.figure(figsize=(10, 6))
        plt.hist(df['interest_rate'], bins=20, alpha=0.7, color='blue')
        plt.xlabel('Interest Rate (%)')
        plt.ylabel('Number of Loans')
        plt.title('Distribution of Loan Interest Rates')
        plt.grid(True, alpha=0.3)
        plt.show()
    
    def plot_bidder_competition(self):
        """Plot bidder competition analysis"""
        
        df = pd.DataFrame(self.loan_data)
        
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        plt.scatter(df['interest_rate'], df['total_bidders'], alpha=0.6)
        plt.xlabel('Interest Rate (%)')
        plt.ylabel('Number of Bidders')
        plt.title('Interest Rate vs Competition')
        
        plt.subplot(2, 2, 2)
        plt.scatter(df['amount'], df['total_bidders'], alpha=0.6)
        plt.xlabel('Loan Amount (SEK)')
        plt.ylabel('Number of Bidders')
        plt.title('Loan Amount vs Competition')
        
        plt.subplot(2, 2, 3)
        plt.hist(df['total_bidders'], bins=15, alpha=0.7, color='green')
        plt.xlabel('Number of Bidders')
        plt.ylabel('Frequency')
        plt.title('Distribution of Bidders')
        
        plt.subplot(2, 2, 4)
        plt.scatter(df['funded_percentage'], df['total_bidders'], alpha=0.6)
        plt.xlabel('Funded Percentage (%)')
        plt.ylabel('Number of Bidders')
        plt.title('Funding Progress vs Competition')
        
        plt.tight_layout()
        plt.show()

# Usage
def analyze_market():
    client = KameoClient()
    analyzer = LoanAnalyzer(client)
    
    # Collect data for 7 days
    analyzer.collect_loan_data(days=7)
    
    # Analyze the data
    analysis = analyzer.analyze_loans()
    print("Market Analysis:")
    for key, value in analysis.items():
        print(f"  {key}: {value}")
    
    # Find best opportunities
    opportunities = analyzer.find_best_opportunities()
    print(f"\nFound {len(opportunities)} good opportunities")
    
    # Plot analysis
    analyzer.plot_interest_distribution()
    analyzer.plot_bidder_competition()
```

---

## 🔄 Real-time Monitoring System

### WebSocket-like Monitoring
```python
import threading
import time
from collections import defaultdict

class RealTimeMonitor:
    def __init__(self, client: KameoClient):
        self.client = client
        self.monitored_loans = defaultdict(dict)
        self.callbacks = []
        self.running = False
    
    def add_callback(self, callback):
        """Add callback for loan updates"""
        self.callbacks.append(callback)
    
    def monitor_loan(self, loan_id: int, check_interval: int = 30):
        """Start monitoring a specific loan"""
        self.monitored_loans[loan_id] = {
            'check_interval': check_interval,
            'last_check': None,
            'last_status': None
        }
    
    def stop_monitoring(self, loan_id: int):
        """Stop monitoring a specific loan"""
        if loan_id in self.monitored_loans:
            del self.monitored_loans[loan_id]
    
    def _check_loan_updates(self):
        """Check for updates on monitored loans"""
        
        current_time = time.time()
        
        for loan_id, loan_info in self.monitored_loans.items():
            
            # Check if it's time to check this loan
            if (loan_info['last_check'] is None or 
                current_time - loan_info['last_check'] >= loan_info['check_interval']):
                
                try:
                    # Get current status
                    status = self.client.get_bidding_status(loan_id)
                    
                    # Check if status changed
                    if loan_info['last_status'] is not None:
                        old_status = loan_info['last_status']
                        
                        # Detect changes
                        changes = []
                        if status.current_bid != old_status.current_bid:
                            changes.append(f"Bid changed: {old_status.current_bid} → {status.current_bid}")
                        
                        if status.total_bidders != old_status.total_bidders:
                            changes.append(f"Bidders changed: {old_status.total_bidders} → {status.total_bidders}")
                        
                        if status.funded_percentage != old_status.funded_percentage:
                            changes.append(f"Funding changed: {old_status.funded_percentage}% → {status.funded_percentage}%")
                        
                        # Trigger callbacks if changes detected
                        if changes:
                            for callback in self.callbacks:
                                callback(loan_id, status, changes)
                    
                    # Update loan info
                    loan_info['last_status'] = status
                    loan_info['last_check'] = current_time
                    
                except Exception as e:
                    logger.error(f"Error checking loan {loan_id}: {e}")
    
    def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        
        def monitor_loop():
            while self.running:
                self._check_loan_updates()
                time.sleep(10)  # Check every 10 seconds
        
        # Start monitoring in background thread
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring_all(self):
        """Stop all monitoring"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()

# Usage example
def loan_update_callback(loan_id: int, status: BiddingStatus, changes: List[str]):
    """Callback function for loan updates"""
    print(f"Loan {loan_id} updates:")
    for change in changes:
        print(f"  - {change}")
    print(f"  Current bid: {status.current_bid} SEK")
    print(f"  Total bidders: {status.total_bidders}")
    print()

def monitor_specific_loans():
    client = KameoClient()
    monitor = RealTimeMonitor(client)
    
    # Add callback
    monitor.add_callback(loan_update_callback)
    
    # Monitor specific loans
    monitor.monitor_loan(4852, check_interval=60)  # Check every minute
    monitor.monitor_loan(4853, check_interval=120)  # Check every 2 minutes
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        monitor.stop_monitoring_all()
```

---

## 🧪 Testing & Validation

### Comprehensive Test Suite
```python
import unittest
from unittest.mock import Mock, patch
import json

class TestKameoClient(unittest.TestCase):
    
    def setUp(self):
        self.client = KameoClient()
    
    @patch('requests.Session.request')
    def test_get_loans(self, mock_request):
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 4852,
                    'title': 'Test Loan',
                    'amount': 1000000,
                    'interest_rate': 8.5,
                    'duration': 12,
                    'current_bids': 5,
                    'min_bid': 1000,
                    'max_bid': 50000
                }
            ]
        }
        mock_response.headers = {'x-ratelimit-remaining': '50'}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Test
        loans = self.client.get_loans(limit=1)
        
        # Assertions
        self.assertEqual(len(loans), 1)
        self.assertEqual(loans[0].id, 4852)
        self.assertEqual(loans[0].title, 'Test Loan')
    
    @patch('requests.Session.request')
    def test_rate_limiting(self, mock_request):
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429")
        mock_request.return_value = mock_response
        
        # Test that rate limiting is handled
        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.get_loans()

class TestBiddingBot(unittest.TestCase):
    
    def setUp(self):
        self.client = Mock()
        self.bot = AutomatedBiddingBot(self.client)
    
    def test_calculate_optimal_bid(self):
        # Test loan and status
        loan = Loan(
            id=4852,
            title="Test",
            amount=1000000,
            interest_rate=8.5,
            duration=12,
            current_bids=5,
            min_bid=1000,
            max_bid=50000,
            funded_percentage=50,
            time_remaining="2 days"
        )
        
        status = BiddingStatus(
            loan_id=4852,
            current_bid=5000,
            min_bid=1000,
            max_bid=50000,
            total_bidders=10,
            time_remaining="2 days",
            interest_rate=8.5,
            loan_amount=1000000,
            funded_percentage=50
        )
        
        # Test optimal bid calculation
        optimal_bid = self.bot.calculate_optimal_bid(loan, status)
        
        # Assertions
        self.assertIsNotNone(optimal_bid)
        self.assertGreater(optimal_bid, status.current_bid)
        self.assertLessEqual(optimal_bid, self.bot.max_bid_amount)

if __name__ == '__main__':
    unittest.main()
```

---

## 📈 Performance Optimization

### Caching and Optimization
```python
from functools import lru_cache
import redis
import pickle

class OptimizedKameoClient(KameoClient):
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        super().__init__()
        self.redis_client = redis.from_url(redis_url)
        self.cache_ttl = 300  # 5 minutes
    
    @lru_cache(maxsize=100)
    def get_loan_cached(self, loan_id: int) -> Dict:
        """Get loan data with caching"""
        cache_key = f"loan:{loan_id}"
        
        # Try to get from cache
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            return pickle.loads(cached_data)
        
        # Get from API
        status = self.get_bidding_status(loan_id)
        
        # Cache the result
        self.redis_client.setex(
            cache_key, 
            self.cache_ttl, 
            pickle.dumps(status)
        )
        
        return status
    
    def batch_get_loans(self, loan_ids: List[int]) -> List[Dict]:
        """Get multiple loans efficiently"""
        results = []
        
        for loan_id in loan_ids:
            try:
                result = self.get_loan_cached(loan_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Error getting loan {loan_id}: {e}")
                results.append(None)
        
        return results
```

---

*These examples provide a complete foundation for building sophisticated Kameo automation systems. Check the [Technical Reference](kameo_api_technical_reference.md) for complete API details!* 