from flask import Flask, request, redirect, send_file, Response, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import string, random, datetime, io, base64
import pandas as pd
import qrcode
from urllib.parse import urlparse

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///url.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db = SQLAlchemy(app)

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(1000), nullable=False)
    short_code = db.Column(db.String(8), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.String(1000), nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not URL.query.filter_by(short_code=code).first():
            return code

def is_valid_url(url):
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and result.netloc != ""
    except Exception:
        return False

def make_qr_data_uri(url):
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    data = base64.b64encode(bio.read()).decode('utf-8')
    return f"data:image/png;base64,{data}"

def url_to_dict(u, host_prefix=''):
    return {
        'id': u.id,
        'long_url': u.long_url,
        'short_code': u.short_code,
        'short_url': host_prefix + u.short_code,
        'title': u.title,
        'description': u.description,
        'tags': u.tags,
        'clicks': u.clicks,
        'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }

@app.route('/api/urls')
def api_urls():
    urls = URL.query.order_by(URL.created_at.desc()).limit(100).all()
    host = request.host_url or ''
    return jsonify([url_to_dict(u, host_prefix=host) for u in urls])

@app.route('/api/add', methods=['POST'])
def api_add():
    data = request.get_json() or {}
    long_url = data.get('long_url')
    title = data.get('title')
    description = data.get('description')
    tags = data.get('tags')
    custom_code = data.get('custom_code')

    if not long_url or not is_valid_url(long_url):
        return jsonify({'error':'Invalid URL'}), 400

    existing = URL.query.filter_by(long_url=long_url).first()
    if existing:
        url_entry = existing
    else:
        if custom_code:
            if URL.query.filter_by(short_code=custom_code).first():
                return jsonify({'error':'Custom code taken'}), 400
            short_code = custom_code
        else:
            short_code = generate_short_code()
        url_entry = URL(long_url=long_url, short_code=short_code, title=title, description=description, tags=tags)
        db.session.add(url_entry)
        db.session.commit()

    short_url = request.host_url + url_entry.short_code
    qr_data = make_qr_data_uri(short_url)
    return jsonify({'short_url': short_url, 'qr_data_uri': qr_data})

@app.route('/api/search')
def api_search():
    q = request.args.get('q','').strip()
    if not q:
        return jsonify([])
    like = f"%{q}%"
    results = URL.query.filter(
        (URL.title.ilike(like)) |
        (URL.description.ilike(like)) |
        (URL.tags.ilike(like)) |
        (URL.long_url.ilike(like))
    ).order_by(URL.created_at.desc()).all()
    host = request.host_url or ''
    return jsonify([url_to_dict(u, host_prefix=host) for u in results])

@app.route('/api/export')
def api_export():
    all_urls = URL.query.order_by(URL.created_at.desc()).all()
    data = [
        {
            'title': u.title,
            'long_url': u.long_url,
            'short_url': request.host_url + u.short_code,
            'tags': u.tags,
            'description': u.description,
            'clicks': u.clicks,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for u in all_urls
    ]
    df = pd.DataFrame(data)
    csv_io = io.StringIO()
    df.to_csv(csv_io, index=False)
    csv_io.seek(0)
    return Response(
        csv_io.getvalue(),
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename=links_export.csv"}
    )

@app.route('/qr/<short_code>')
def qr(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first_or_404()
    short_url = request.host_url + url_entry.short_code
    qr_img = qrcode.make(short_url)
    bio = io.BytesIO()
    qr_img.save(bio, format='PNG')
    bio.seek(0)
    return send_file(bio, mimetype='image/png')

@app.route('/<short_code>')
def redirect_short_url(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first_or_404()
    try:
        url_entry.clicks = (url_entry.clicks or 0) + 1
        db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_entry.long_url)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
