async function loadTickers() {
    try {
        const response = await fetch('/api/tickers');
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        const tickerSelect = document.getElementById('ticker-select');
        if (!tickerSelect) throw new Error('Ticker select element not found');
        tickerSelect.innerHTML = '<option value="">Select a ticker</option>';
        data.tickers.forEach(ticker => {
            const option = document.createElement('option');
            option.value = ticker;
            option.textContent = ticker;
            tickerSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading tickers:', error);
    }
}

window.onload = loadTickers;