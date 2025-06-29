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
        alert('Failed to load tickers.');
    }
}

async function loadValidDates(ticker) {
    const dateInput = document.getElementById('date');
    dateInput.disabled = !ticker;
    dateInput.value = ''; // Clear date input when ticker changes
    if (!ticker) return;

    try {
        const response = await fetch(`/api/valid_dates?ticker=${ticker}`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        if (data.error) {
            alert(data.error);
            return;
        }
        dateInput.setAttribute('min', data.dates[0]);
        dateInput.setAttribute('max', data.dates[data.dates.length - 1]);
    } catch (error) {
        console.error('Error loading valid dates:', error);
        alert('Failed to load valid dates.');
    }
}

document.getElementById('stock-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const ticker = document.getElementById('ticker-select').value;
    const date = document.getElementById('date').value;
    const chartContainer = document.getElementById('chart-container');

    if (!ticker || !date) {
        chartContainer.innerHTML = '<p>Please select a ticker and date.</p>';
        return;
    }

    try {
        const response = await fetch(`/api/stock/chart?ticker=${ticker}&date=${date}`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        if (data.error) {
            chartContainer.innerHTML = `<p>Error: ${data.error}</p>`;
            return;
        }
        chartContainer.innerHTML = `<img src="${data.chart}" alt="Stock Chart">`;
    } catch (error) {
        console.error('Error loading chart:', error);
        chartContainer.innerHTML = '<p>Failed to load chart. Please try again.</p>';
    }
});

document.getElementById('ticker-select').addEventListener('change', function() {
    loadValidDates(this.value);
});

window.onload = loadTickers;