let trendChartInstance = null;
let currentAbortController = null;
const PALETTE = ['#14b8a6', '#f43f5e', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899', '#22c55e', '#64748b'];

function initChart() {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'bottom', align: 'start', labels: { usePointStyle: true, boxWidth: 6, font: { weight: '600', size: 10 } } },
                tooltip: { 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    titleFont: { size: 13, weight: 'bold' },
                    bodyFont: { size: 12 },
                    padding: 12,
                    cornerRadius: 12,
                    callbacks: {
                        label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw}% Positive`
                    }
                }
            },
            scales: {
                y: { min: 0, max: 100, ticks: { callback: v => v + '%' }, grid: { color: 'rgba(0,0,0,0.05)' }, border: { dash: [4, 4] } },
                x: { grid: { display: false } }
            }
        }
    });
}

function updateChart(data, selectedAspects) {
    if (!trendChartInstance) initChart();
    
    const periods = [...new Set(data.map(d => d.period))].sort();
    
    const datasets = selectedAspects.map((aspect, idx) => {
        const color = PALETTE[idx % PALETTE.length];
        
        // Fill mapping: ensure we have values for all periods (null for gaps)
        const periodValues = periods.map(p => {
            const entry = data.find(d => d.period === p && d.aspect_category === aspect);
            if (!entry) return null;
            const total = (entry.positive || 0) + (entry.negative || 0) + (entry.neutral || 0);
            return total > 0 ? Math.round((entry.positive / total) * 100) : null;
        });

        return {
            label: aspect,
            data: periodValues,
            borderColor: color,
            backgroundColor: color + '15',
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2.5,
            spanGaps: true
        };
    });

    trendChartInstance.data.labels = periods;
    trendChartInstance.data.datasets = datasets;
    trendChartInstance.update();
}

async function fetchHeatmap(productId) {
    if (!productId) return;
    try {
        const res = await fetch(`/analytics/product/${productId}/heatmap`);
        const json = await res.json();
        drawHeatmap(json);
    } catch (e) { console.error("Heatmap fetch error", e); }
}

function drawHeatmap(data) {
    const svg = document.getElementById('heatmapSvg');
    if (!svg || data.aspects.length === 0) return;
    
    // Clear svg
    svg.innerHTML = '';
    
    // Config
    const rowHeight = 40;
    const colWidth = 60;
    const labelWidth = 120;
    const topMargin = 30;
    
    svg.setAttribute('height', (data.aspects.length * rowHeight) + topMargin + 40);
    svg.setAttribute('width', (data.periods.length * colWidth) + labelWidth + 40);

    // X Labels
    data.periods.forEach((p, i) => {
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute('x', labelWidth + (i * colWidth) + (colWidth/2));
        text.setAttribute('y', 20);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('class', 'text-[10px] font-bold fill-gray-400');
        // Extract week/month from period "2026-W08"
        text.textContent = p.split('-')[1];
        svg.appendChild(text);
    });

    // Grid
    data.aspects.forEach((aspect, r) => {
        // Label
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute('x', 10);
        label.setAttribute('y', topMargin + (r * rowHeight) + (rowHeight/2) + 5);
        label.setAttribute('class', 'text-xs font-bold fill-gray-600');
        label.textContent = aspect;
        svg.appendChild(label);

        // Cells
        data.periods.forEach((period, c) => {
            const [ratio, count] = data.cells[r][c];
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute('x', labelWidth + (c * colWidth));
            rect.setAttribute('y', topMargin + (r * rowHeight));
            rect.setAttribute('width', colWidth - 4);
            rect.setAttribute('height', rowHeight - 4);
            rect.setAttribute('rx', 6);
            rect.setAttribute('class', 'heatmap-cell transition-all duration-300');
            
            // Color interpolation (0 = gray-100, 100 = teal-600)
            const color = (ratio > 70) ? `rgb(13, 148, 136)` : 
                          (ratio > 50) ? `rgb(45, 212, 191)` :
                          (ratio > 30) ? `rgb(153, 246, 228)` : `rgb(241, 245, 249)`;
            
            rect.setAttribute('fill', color);
            rect.setAttribute('opacity', count < 5 ? 0.3 : 1);
            
            // Tooltip events
            rect.onmouseover = (ev) => showHeatmapTooltip(ev, aspect, ratio, count);
            rect.onmouseout = () => { window.__trendAppTooltip = false; };
            
            svg.appendChild(rect);
        });
    });
}

function showHeatmapTooltip(ev, category, ratio, count) {
    // This communicates with Alpine app state
    const el = document.querySelector('[x-data="trendApp()"]');
    if (!el) return;
    const app = el.__x.$data;
    app.tooltip = {
        show: true,
        x: ev.clientX,
        y: ev.clientY,
        category,
        ratio,
        count
    };
}

// Global hook for Alpine
window.updateChart = updateChart;
window.fetchHeatmap = fetchHeatmap;
