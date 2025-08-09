from flask import Flask, request, jsonify, render_template_string

# Import CLI classes
from loan_collector import LoanCollector
from bidding_cli import BiddingCLI

app = Flask(__name__)

# Simple home page template
HOME_TEMPLATE = """
<!doctype html>
<title>Kameo Web Interface</title>
<h1>Kameo Web Interface</h1>
<ul>
  <li><a href='/fetch'>Fetch Loans</a></li>
  <li><a href='/analyze'>Analyze Fields</a></li>
  <li><a href='/stats'>Database Stats</a></li>
  <li><a href='/search?term=test'>Search Loans</a></li>
  <li><a href='/health'>Health Check</a></li>
  <li><a href='/bidding/list'>List Available Loans</a></li>
</ul>
"""

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/fetch')
def fetch_loans():
    max_pages = int(request.args.get('max_pages', 10))
    collector = LoanCollector()
    result = collector.fetch_and_save_loans(max_pages=max_pages)
    collector.close()
    return jsonify(result)

@app.route('/analyze')
def analyze_fields():
    collector = LoanCollector(save_raw_data=True)
    result = collector.analyze_fields()
    collector.close()
    return jsonify(result)

@app.route('/stats')
def stats():
    collector = LoanCollector()
    result = collector.get_statistics()
    collector.close()
    return jsonify(result)

@app.route('/search')
def search():
    term = request.args.get('term', '')
    collector = LoanCollector()
    result = [loan.dict() for loan in collector.search_loans(term)]
    collector.close()
    return jsonify(result)

@app.route('/health')
def health():
    collector = LoanCollector()
    result = collector.health_check()
    collector.close()
    return jsonify(result)

# Bidding endpoints
bidding_cli = BiddingCLI()

@app.route('/bidding/list')
def bidding_list():
    max_pages = int(request.args.get('max_pages', 3))
    loans = bidding_cli.bidding_service.get_available_loans(max_pages=max_pages)
    return jsonify(loans)

@app.route('/bidding/analyze/<int:loan_id>')
def bidding_analyze(loan_id):
    result = bidding_cli.bidding_service.analyze_loan_for_bidding(loan_id)
    return jsonify(result)

@app.route('/bidding/bid/<int:loan_id>', methods=['POST'])
def bidding_bid(loan_id):
    amount = int(request.json.get('amount', 0))
    payment_option = request.json.get('payment_option', 'ip')
    from src.services.bidding_service import BiddingRequest
    req = BiddingRequest(loan_id=loan_id, amount=amount, payment_option=payment_option)
    resp = bidding_cli.bidding_service.place_bid(req)
    return jsonify(resp.__dict__)

@app.route('/bidding/strategy/<int:loan_id>', methods=['POST'])
def bidding_strategy(loan_id):
    strategy = request.json or {}
    resp = bidding_cli.bidding_service.execute_bidding_strategy(loan_id, strategy)
    return jsonify(resp.__dict__)

if __name__ == '__main__':
    app.run(debug=True)
