from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from shopify_api import search_products_across_stores
import datetime
from sqlalchemy import func
import os

# --- App & DB Setup ---
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)
app = Flask(__name__, instance_path=instance_path)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'site.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    store_url = db.Column(db.String(200), unique=True, nullable=False)
    prices = db.relationship('PriceHistory', backref='product', lazy=True)
    # ADDED: Relationship to the Alert table
    alerts = db.relationship('Alert', backref='product', lazy=True)

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_price = db.Column(db.Float, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

# --- Main Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search_products():
    search_query = request.args.get('query', '')
    if not search_query: return jsonify({'error': 'Please provide a search query.'}), 400
    products_from_api = search_products_across_stores(search_query)
    for product_api in products_from_api:
        product_db = Product.query.filter_by(store_url=product_api['product_url']).first()
        if product_db:
            stats = db.session.query(
                func.max(PriceHistory.price).label('highest'),
                func.min(PriceHistory.price).label('lowest'),
                func.avg(PriceHistory.price).label('average')
            ).filter(PriceHistory.product_id == product_db.id).one()
            product_api['highest_price'] = stats.highest if stats.highest else 0
            product_api['lowest_price'] = stats.lowest if stats.lowest else 0
            product_api['average_price'] = stats.average if stats.average else 0
    return jsonify(products_from_api) if products_from_api else (jsonify({'message': 'No products found.'}), 404)

@app.route('/track', methods=['POST'])
def track_product():
    data = request.get_json()
    product_url, product_title, current_price = data.get('product_url'), data.get('product_title'), data.get('price')
    if not all([product_url, product_title, current_price is not None]):
        return jsonify({'error': 'Missing product data.'}), 400
    product = Product.query.filter_by(store_url=product_url).first()
    if not product:
        product = Product(title=product_title, store_url=product_url)
        db.session.add(product)
        db.session.commit()
    new_price_entry = PriceHistory(price=current_price, product_id=product.id)
    db.session.add(new_price_entry)
    db.session.commit()
    return jsonify({'success': f'Successfully tracked price for {product_title}'})

@app.route('/history', methods=['GET'])
def get_history():
    product_url = request.args.get('product_url')
    if not product_url: return jsonify({'error': 'Product URL is required.'}), 400
    product = Product.query.filter_by(store_url=product_url).first()
    if product:
        price_history = [{'price': e.price, 'timestamp': e.timestamp.strftime('%Y-%m-%d %H:%M:%S')} for e in sorted(product.prices, key=lambda p: p.timestamp)]
        return jsonify(price_history)
    return jsonify([]), 200

@app.route('/set_alert', methods=['POST'])
def set_alert():
    data = request.get_json()
    product_url, target_price = data.get('product_url'), data.get('target_price')
    if not product_url or not target_price: return jsonify({'error': 'Missing data.'}), 400
    product = Product.query.filter_by(store_url=product_url).first()
    if not product: return jsonify({'error': 'Product not tracked yet.'}), 404
    new_alert = Alert(target_price=float(target_price), product_id=product.id)
    db.session.add(new_alert)
    db.session.commit()
    return jsonify({'success': f'Alert set for {product.title} at target price of {target_price}'})

# NEW: Endpoint to check for price drop alerts
@app.route('/check_alerts', methods=['GET'])
def check_alerts():
    triggered_alerts = []
    all_alerts = Alert.query.all()
    
    for alert in all_alerts:
        # Find the most recently tracked price for this product
        latest_price_entry = PriceHistory.query.filter_by(product_id=alert.product_id).order_by(PriceHistory.timestamp.desc()).first()
        
        if latest_price_entry and latest_price_entry.price <= alert.target_price:
            triggered_alerts.append({
                'product_title': alert.product.title,
                'target_price': alert.target_price,
                'current_price': latest_price_entry.price
            })
            # In a real app, you would remove the alert after notifying
            # db.session.delete(alert)
    
    # db.session.commit()
    return jsonify(triggered_alerts)

if __name__ == '__main__':
    app.run(debug=True)