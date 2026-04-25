let trafficChart;

async function fetchData() {
    const start = getCombinedDateTime('start');
    const end = getCombinedDateTime('end');
    
    let url = '/api/traffic';
    const params = new URLSearchParams();
    if (start) params.append('start', start);
    if (end) params.append('end', end);
    
    if (params.toString()) url += '?' + params.toString();

    try {
        const response = await fetch(url);
        const data = await response.json();
        updateChart(data);
        updateStats(data);
    } catch (error) {
        showToast('Veri çekme hatası: ' + error.message);
    }
}

async function exportCSV() {
    const start = getCombinedDateTime('start');
    const end = getCombinedDateTime('end');
    
    let url = '/api/export-csv';
    const params = new URLSearchParams();
    if (start) params.append('start', start);
    if (end) params.append('end', end);
    
    if (params.toString()) url += '?' + params.toString();

    try {
        const response = await fetch(url);
        const result = await response.json();
        if (result.success) {
            showToast(result.message);
        } else {
            showToast('Hata: ' + result.message);
        }
    } catch (error) {
        showToast('Dışa aktarma hatası: ' + error.message);
    }
}

function getCombinedDateTime(prefix) {
    const date = document.getElementById(prefix + 'Date').value;
    const time = document.getElementById(prefix + 'Time').value;
    return (date && time) ? `${date}T${time}` : date;
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

function updateChart(data) {
    const ctx = document.getElementById('trafficChart').getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');

    const labels = data.map(item => item.traffic_index_date);
    const values = data.map(item => item.traffic_index);

    if (trafficChart) trafficChart.destroy();

    trafficChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Trafik İndeksi',
                data: values,
                borderColor: '#818cf8',
                backgroundColor: gradient,
                borderWidth: 4,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 8,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#6366f1',
                pointHoverBorderWidth: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'hour', displayFormats: { hour: 'HH:mm', day: 'MMM D' } },
                    grid: { display: false },
                    ticks: { color: '#64748b' }
                },
                y: {
                    min: 0, max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.03)' },
                    ticks: { color: '#64748b' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0f172a',
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        label: function(context) { return `Yoğunluk: %${context.parsed.y}`; }
                    }
                }
            }
        }
    });
}

function updateStats(data) {
    if (!data.length) return;
    const values = data.map(item => item.traffic_index);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const max = Math.max(...values);
    const min = Math.min(...values);

    animateValue('avgIndex', avg);
    animateValue('maxIndex', max);
    animateValue('minIndex', min);
}

function animateValue(id, value) {
    const obj = document.getElementById(id);
    const end = Math.round(value);
    const duration = 800;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * end);
        if (progress < 1) window.requestAnimationFrame(step);
    };
    window.requestAnimationFrame(step);
}

// Initial setup
const now = new Date();
const yesterday = new Date(now.getTime() - (24 * 60 * 60 * 1000));

document.getElementById('startDate').value = yesterday.toISOString().split('T')[0];
document.getElementById('startTime').value = yesterday.toTimeString().slice(0, 5);
document.getElementById('endDate').value = now.toISOString().split('T')[0];
document.getElementById('endTime').value = now.toTimeString().slice(0, 5);

document.getElementById('updateBtn').addEventListener('click', fetchData);
document.getElementById('exportBtn').addEventListener('click', exportCSV);

fetchData();
