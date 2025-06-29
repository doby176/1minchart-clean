from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pandas as pd
import mplfinance as mpf
import io
import base64
from datetime import datetime
import logging
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Set up rate limiter (disabled for testing)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Ticker and year to database mapping
TICKERS = ['QQQ', 'AAPL', 'MSFT', 'TSLA', 'ORCL', 'NVDA', 'MSTR', 'UBER', 'PLTR', 'META']
YEARS = range(2015, 2026)

def get_db_path(ticker, year):
    if ticker not in TICKERS or year not in YEARS:
        return None
    return f"sqlite:///data/split_dbs/stock_data_{ticker.lower()}_{year}.db"

@app.route('/')
def index():
    logging.debug("Rendering index.html")
    return render_template('index.html')

@app.route('/api/tickers', methods=['GET'])
def get_tickers():
    logging.debug("Fetching available tickers")
    try:
        return jsonify({'tickers': sorted(TICKERS)})
    except Exception as e:
        logging.error(f"Error fetching tickers: {str(e)}")
        return jsonify({'error': 'Failed to fetch tickers'}), 500

@app.route('/api/valid_dates', methods=['GET'])
def get_valid_dates():
    ticker = request.args.get('ticker')
    logging.debug(f"Fetching valid dates for ticker: {ticker}")
    if not ticker or ticker not in TICKERS:
        return jsonify({'error': 'Missing or invalid ticker'}), 400
    try:
        dates = set()
        for year in YEARS:
            db_path = get_db_path(ticker, year)
            if not db_path:
                continue
            engine = create_engine(db_path, echo=False)
            with engine.connect() as conn:
                query = text("SELECT DISTINCT DATE(timestamp) AS date FROM candles WHERE ticker = :ticker")
                year_dates = [row[0] for row in conn.execute(query, {"ticker": ticker}).fetchall()]
                dates.update(year_dates)
        return jsonify({'dates': sorted(list(dates))})
    except Exception as e:
        logging.error(f"Error fetching dates for {ticker}: {str(e)}")
        return jsonify({'error': 'Failed to fetch dates'}), 500

@app.route('/api/stock/chart', methods=['GET'])
def get_chart():
    try:
        ticker = request.args.get('ticker')
        date = request.args.get('date')
        logging.debug(f"Received request: ticker={ticker}, date={date}, raw query: {request.args}")
        logging.debug(f"Request URL: {request.url}")

        if not ticker or not date:
            return jsonify({'error': 'Missing ticker or date'}), 400
        if ticker not in TICKERS:
            return jsonify({'error': 'Invalid ticker'}), 400

        try:
            target_date = pd.to_datetime(date).date()
            year = target_date.year
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        db_path = get_db_path(ticker, year)
        if not db_path:
            return jsonify({'error': 'No database available for the selected ticker and year'}), 404

        # Query database
        try:
            engine = create_engine(db_path, echo=False)
            query = text("""
                SELECT timestamp, open, high, low, close, volume
                FROM candles
                WHERE ticker = :ticker AND DATE(timestamp) = :date
            """)
            df = pd.read_sql(
                query,
                engine,
                params={"ticker": ticker, "date": str(target_date)},
                parse_dates=['timestamp']
            )
            logging.debug(f"Loaded data shape: {df.shape}")
        except Exception as e:
            logging.error(f"Error querying database: {str(e)}")
            return jsonify({'error': 'Database query failed'}), 500

        if df.empty:
            return jsonify({'error': 'No data available for the selected date'}), 404

        # Ensure required columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'Invalid data format'}), 400

        # Set timestamp as index and sort
        df = df[required_columns].set_index('timestamp').sort_index()

        # Generate chart
        buf = io.BytesIO()
        try:
            mpf.plot(
                df,
                type='candle',
                style='yahoo',
                savefig=dict(fname=buf, dpi=100),
                warn_too_much_data=10000
            )
            buf.seek(0)
            img = base64.b64encode(buf.getvalue()).decode('utf-8')
            buf.close()
        except Exception as e:
            logging.error(f"Error generating chart: {str(e)}")
            return jsonify({'error': 'Failed to generate chart'}), 500

        return jsonify({'chart': f'data:image/png;base64,{img}'})
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)