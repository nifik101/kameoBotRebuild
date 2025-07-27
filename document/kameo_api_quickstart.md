# Kameo API Quick Start Guide
*Get started with Kameo.se APIs in 5 minutes*

## 🚀 5-Minute Setup

### Step 1: Test Basic Connection
```bash
# Test if you can access the API
curl -X GET "https://api.kameo.se/v1/loans/listing/investment-options?limit=1" \
  -H "accept-language: sv" \
  -H "origin: https://www.kameo.se" \
  -H "content-type: application/json"
```

### Step 1.5: Check Account Balance
```bash
# Check your account balance (requires login)
curl -X GET "https://www.kameo.se/ezjscore/call/kameo_transfer::init" \
  -H "accept: application/json, text/plain, */*" \
  -H "accept-language: en-GB,en;q=0.7" \
  -H "referer: https://www.kameo.se/investor/dashboard"
```

### Step 2: Get Available Loans
```bash
# Get first page of loans
curl -X GET "https://api.kameo.se/v1/loans/listing/investment-options?subscription_origin_sweden=1&subscription_origin_norway=0&subscription_origin_denmark=1&limit=5&page=1" \
  -H "accept-language: sv" \
  -H "origin: https://www.kameo.se" \
  -H "content-type: application/json"
```

### Step 3: Check Bidding Status
```bash
# Replace 4852 with actual loan ID from step 2
curl -X GET "https://api.kameo.se/v1/bidding/4852/load" \
  -H "accept-language: sv" \
  -H "origin: https://www.kameo.se" \
  -H "content-type: application/json"
```

### Step 4: Preview a Bid
```bash
# Preview a 3000 SEK bid
curl -X POST "https://api.kameo.se/v1/bidding/4852/load" \
  -H "accept-language: sv" \
  -H "origin: https://www.kameo.se" \
  -H "content-type: application/json" \
  -d '{
    "amount": "3000",
    "intention": "add",
    "sequence_hash": "",
    "payment_options": ["ip"]
  }'
```

### Step 5: Submit a Bid (Optional)
```bash
# Use sequence_hash from step 4 response
curl -X POST "https://api.kameo.se/v1/bidding/4852/submit" \
  -H "accept-language: sv" \
  -H "origin: https://www.kameo.se" \
  -H "content-type: application/json" \
  -d '{
    "amount": "3000",
    "intention": "add",
    "sequence_hash": "YOUR_SEQUENCE_HASH_HERE",
    "payment_options": ["ip"]
  }'
```

---

## 🐍 Python Quick Start

### Install Dependencies
```bash
pip install requests
```

### Basic Python Client
```python
import requests
import json

class KameoAPI:
    def __init__(self):
        self.base_url = "https://api.kameo.se/v1"
        self.headers = {
            "accept-language": "sv",
            "origin": "https://www.kameo.se",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
    
    def get_loans(self, limit=12, page=1):
        """Get available loans"""
        url = f"{self.base_url}/loans/listing/investment-options"
        params = {
            "subscription_origin_sweden": "1",
            "subscription_origin_norway": "0",
            "subscription_origin_denmark": "1",
            "limit": str(limit),
            "page": str(page)
        }
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def get_bidding_status(self, loan_id):
        """Get current bidding status for a loan"""
        url = f"{self.base_url}/bidding/{loan_id}/load"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def preview_bid(self, loan_id, amount, payment_option="ip"):
        """Preview a bid without submitting"""
        url = f"{self.base_url}/bidding/{loan_id}/load"
        data = {
            "amount": str(amount),
            "intention": "add",
            "sequence_hash": "",
            "payment_options": [payment_option]
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def submit_bid(self, loan_id, amount, sequence_hash, payment_option="ip"):
        """Submit an actual bid"""
        url = f"{self.base_url}/bidding/{loan_id}/submit"
        data = {
            "amount": str(amount),
            "intention": "add",
            "sequence_hash": sequence_hash,
            "payment_options": [payment_option]
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def get_accounts(self):
        """Get user account balances"""
        url = "https://www.kameo.se/ezjscore/call/kameo_transfer::init"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en;q=0.7",
            "referer": "https://www.kameo.se/investor/dashboard",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        return response.json()

# Usage example
api = KameoAPI()

# Check account balance
accounts = api.get_accounts()
sek_balance = next((acc['availableCash'] for acc in accounts['content']['data']['accounts'] 
                   if acc['currencyCode'] == 'SEK'), '0,00')
print(f"Available SEK: {sek_balance}")

# Get available loans
loans = api.get_loans(limit=5)
print(f"Found {len(loans['data'])} loans")

# Check first loan
if loans['data']:
    loan_id = loans['data'][0]['id']
    status = api.get_bidding_status(loan_id)
    print(f"Current bid: {status.get('current_bid', 'N/A')} SEK")
    
    # Preview a bid
    preview = api.preview_bid(loan_id, 3000)
    print(f"Estimated return: {preview.get('estimated_return', 'N/A')} SEK")
```

---

## 🔧 JavaScript/Node.js Quick Start

### Install Dependencies
```bash
npm install axios
```

### Basic JavaScript Client
```javascript
const axios = require('axios');

class KameoAPI {
    constructor() {
        this.baseURL = 'https://api.kameo.se/v1';
        this.headers = {
            'accept-language': 'sv',
            'origin': 'https://www.kameo.se',
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        };
    }

    async getLoans(limit = 12, page = 1) {
        const params = {
            subscription_origin_sweden: '1',
            subscription_origin_norway: '0',
            subscription_origin_denmark: '1',
            limit: limit.toString(),
            page: page.toString()
        };
        
        const response = await axios.get(`${this.baseURL}/loans/listing/investment-options`, {
            headers: this.headers,
            params
        });
        return response.data;
    }

    async getBiddingStatus(loanId) {
        const response = await axios.get(`${this.baseURL}/bidding/${loanId}/load`, {
            headers: this.headers
        });
        return response.data;
    }

    async previewBid(loanId, amount, paymentOption = 'ip') {
        const data = {
            amount: amount.toString(),
            intention: 'add',
            sequence_hash: '',
            payment_options: [paymentOption]
        };
        
        const response = await axios.post(`${this.baseURL}/bidding/${loanId}/load`, data, {
            headers: this.headers
        });
        return response.data;
    }

    async submitBid(loanId, amount, sequenceHash, paymentOption = 'ip') {
        const data = {
            amount: amount.toString(),
            intention: 'add',
            sequence_hash: sequenceHash,
            payment_options: [paymentOption]
        };
        
        const response = await axios.post(`${this.baseURL}/bidding/${loanId}/submit`, data, {
            headers: this.headers
        });
        return response.data;
    }
}

// Usage example
async function main() {
    const api = new KameoAPI();
    
    try {
        // Get available loans
        const loans = await api.getLoans(5);
        console.log(`Found ${loans.data.length} loans`);
        
        if (loans.data.length > 0) {
            const loanId = loans.data[0].id;
            
            // Check bidding status
            const status = await api.getBiddingStatus(loanId);
            console.log(`Current bid: ${status.current_bid || 'N/A'} SEK`);
            
            // Preview a bid
            const preview = await api.previewBid(loanId, 3000);
            console.log(`Estimated return: ${preview.estimated_return || 'N/A'} SEK`);
        }
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

---

## ⚠️ Important Notes

### Rate Limiting
- **60 requests per minute**
- Check `x-ratelimit-remaining` header
- Implement exponential backoff if needed

### Sequence Hash
- **Always preview before submitting**
- Hash expires after ~5 minutes
- Each preview generates new hash

### Payment Options
- **"ip"** = Income Pension (Inkomstpension)
- **"dp"** = Direct Pension (Direktpension)

### Error Handling
```python
try:
    response = api.get_loans()
except requests.exceptions.RequestException as e:
    print(f"API Error: {e}")
    # Check if rate limited
    if hasattr(e.response, 'status_code') and e.response.status_code == 429:
        print("Rate limit exceeded - wait 60 seconds")
```

---

## 🎯 Next Steps

1. **Read the [Technical Reference](kameo_api_technical_reference.md)** for complete API details
2. **Check [Implementation Examples](kameo_api_examples.md)** for advanced patterns
3. **Review [User Guide](kameo_api_user_guide.md)** for business context
4. **Start with monitoring** before implementing automated bidding

---

## 🆘 Troubleshooting

### Common Issues
- **429 Error**: Rate limit exceeded - wait 60 seconds
- **400 Error**: Invalid parameters - check request format
- **Sequence Hash Error**: Preview again to get fresh hash

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show all HTTP requests and responses
```

---

*Ready to automate your Kameo bidding? Check the [Technical Reference](kameo_api_technical_reference.md) for complete implementation details!* 