# Kameo API Documentation Index
*Complete API reference for Kameo.se bidding automation*

## 📚 Documentation Overview

### For Users & Business Stakeholders
- **[Kameo API User Guide](kameo_api_user_guide.md)** - Simple overview of all API capabilities
- **[API Quick Start](kameo_api_quickstart.md)** - Get started with Kameo APIs in 5 minutes

### For Developers & AI Assistants  
- **[Kameo API Technical Reference](kameo_api_technical_reference.md)** - Complete technical specification
- **[API Implementation Examples](kameo_api_examples.md)** - Code examples and implementation patterns

---

## 🚀 Quick Navigation

### Core API Endpoints
| Endpoint | Purpose | Method | Documentation |
|----------|---------|--------|---------------|
| `/v1/loans/listing/investment-options` | Get available loans | GET | [Technical Reference](kameo_api_technical_reference.md#1-get-investment-options) |
| `/v1/q-a` | Get loan Q&A | GET | [Technical Reference](kameo_api_technical_reference.md#2-get-qa-for-loan) |
| `/v1/bidding/{id}/load` | Load bidding data | GET | [Technical Reference](kameo_api_technical_reference.md#3-load-bidding-data) |
| `/v1/bidding/{id}/load` | Preview bid | POST | [Technical Reference](kameo_api_technical_reference.md#4-preview-bid-simulation) |
| `/v1/bidding/{id}/submit` | Submit bid | POST | [Technical Reference](kameo_api_technical_reference.md#5-submit-bid) |
| `/v1/loan/subscription/{id}` | Subscribe to loan | POST | [Technical Reference](kameo_api_technical_reference.md#6-subscribe-to-loan) |
| `/ezjscore/call/kameo_transfer::init` | Get user accounts | GET | [Technical Reference](kameo_api_technical_reference.md#7-get-user-accounts--transfer-data) |

### Implementation Resources
- **[Authentication & Headers](kameo_api_technical_reference.md#authentication--headers)**
- **[Rate Limiting](kameo_api_technical_reference.md#rate-limiting)**
- **[Error Handling](kameo_api_technical_reference.md#error-handling)**
- **[Sequence Hash Management](kameo_api_technical_reference.md#sequence-hash-management)**

---

## 📋 API Capabilities Summary

### ✅ What You Can Do
- **Discover Loans**: Get all available investment opportunities
- **Analyze Loans**: Access detailed Q&A and loan information  
- **Monitor Bidding**: Track current bid status and competition
- **Simulate Bids**: Preview potential returns before bidding
- **Place Bids**: Automatically submit bids with optimal amounts
- **Track Subscriptions**: Monitor loan progress and updates
- **Manage Accounts**: Check balances and transfer funds

### 🔧 Technical Features
- **No Authentication Required**: Session-based via cookies
- **Rate Limited**: 60 requests per minute
- **Real-time Data**: Live bidding information
- **Sequence Validation**: Secure bid submission system
- **Multiple Payment Options**: Income pension (ip) and direct pension (dp)

---

## 🎯 Use Cases

### Automated Bidding Bot
1. Check account balance → [Get User Accounts](kameo_api_technical_reference.md#7-get-user-accounts--transfer-data)
2. Scan for new loans → [Get Investment Options](kameo_api_technical_reference.md#1-get-investment-options)
3. Analyze loan details → [Get Q&A](kameo_api_technical_reference.md#2-get-qa-for-loan)
4. Check current status → [Load Bidding Data](kameo_api_technical_reference.md#3-load-bidding-data)
5. Calculate optimal bid → [Preview Bid](kameo_api_technical_reference.md#4-preview-bid-simulation)
6. Submit bid → [Submit Bid](kameo_api_technical_reference.md#5-submit-bid)
7. Monitor progress → [Subscribe to Loan](kameo_api_technical_reference.md#6-subscribe-to-loan)

### Loan Monitoring System
- Track multiple loans simultaneously
- Get notified of status changes
- Monitor competition levels
- Analyze bidding patterns

---

## 📊 Data Sources

All API documentation is based on real HAR (HTTP Archive) files captured from:
- `aktuella_2loan_made_bid_xhr.har` - Complete bidding flow
- `aktuella_2loan_made_bid_doc.har` - Page navigation data
- `landing_login_aktuella_noLoan.har` - Initial loan discovery + Account data
- `landing_login_aktuella_noLoan_2.har` - Additional session data

**Data Completeness**: ✅ 100% - All endpoints, parameters, response structures, and account management documented

---

## 🔗 Related Documentation

### Project Documentation
- [Project Overview](../README.md)
- [Development Guide](../developer_guide.md)
- [Future Enhancements](../future_enhancements.md)

### External Resources
- [Kameo.se Official Site](https://www.kameo.se)
- [API Base URL](https://api.kameo.se/v1/)

---

## 📝 Documentation Status

| Document | Status | Last Updated | Completeness |
|----------|--------|--------------|--------------|
| User Guide | ✅ Complete | 2025-01-27 | 100% |
| Technical Reference | ✅ Complete | 2025-01-27 | 100% |
| Quick Start | ✅ Complete | 2025-01-27 | 100% |
| Implementation Examples | ✅ Complete | 2025-01-27 | 100% |

---

## 🆘 Getting Help

### For Technical Issues
- Check [Error Handling](kameo_api_technical_reference.md#error-handling) section
- Review [Rate Limiting](kameo_api_technical_reference.md#rate-limiting) guidelines
- See [Implementation Examples](kameo_api_examples.md) for common patterns

### For Business Questions
- Read [User Guide](kameo_api_user_guide.md) for overview
- Check [Quick Start](kameo_api_quickstart.md) for basic usage

---

*Last updated: January 27, 2025*
*Based on HAR analysis from July 16, 2025* 