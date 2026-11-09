/**
 * Dukaan Dost AI - Business Dashboard Engine
 * Live SQLite data binding, Chart.js visualizations, stock alerts, and real-time updates.
 */

document.addEventListener('DOMContentLoaded', () => {
  const formatCurrency = (val) => {
    const num = parseFloat(val || 0);
    return num.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
  };

  let salesChart = null;
  let categoryChart = null;

  async function loadDashboardData() {
    try {
      const res = await fetch('/api/dashboard');
      const data = await res.json();
      renderKPIs(data.stats);
      renderRecentSales(data.recent_sales);
      renderLowStockAlerts(data.low_stock_items);
      renderBestSellers(data.best_sellers);
      renderCharts(data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    }
  }

  function renderKPIs(stats) {
    if (!stats) return;

    const revEl = document.getElementById('kpiRevenue');
    if (revEl) revEl.textContent = formatCurrency(stats.revenue);

    const txEl = document.getElementById('kpiTransactions');
    if (txEl) txEl.textContent = `${stats.transactions} Orders`;

    const unitsEl = document.getElementById('kpiUnits');
    if (unitsEl) unitsEl.textContent = `${stats.units_sold} Units`;

    const profitEl = document.getElementById('kpiProfit');
    if (profitEl) profitEl.textContent = formatCurrency(stats.profit);

    const lowEl = document.getElementById('kpiLowStock');
    if (lowEl) lowEl.textContent = stats.low_stock;

    const valEl = document.getElementById('kpiRetailValue');
    if (valEl) valEl.textContent = formatCurrency(stats.retail_value);
  }

  function renderRecentSales(sales) {
    const tbody = document.getElementById('recentSalesBody');
    if (!tbody) return;

    if (!sales || sales.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-muted); padding: 2rem;">No recent transactions recorded today.</td></tr>';
      return;
    }

    tbody.innerHTML = sales.map(s => `
      <tr>
        <td style="font-weight: 700;">#${s.id}</td>
        <td>
          <div style="font-weight: 600; color: #fff;">${s.name}</div>
          <small style="color: var(--text-muted); font-size: 0.75rem;">${s.category || 'General'}</small>
        </td>
        <td>${s.quantity} ${s.unit}</td>
        <td style="font-weight: 700; color: var(--mint-glow);">${formatCurrency(s.total)}</td>
        <td style="color: var(--text-secondary); font-size: 0.8rem;">
          ${s.created_at ? s.created_at.split(' ')[1] || s.created_at : 'Just now'}
        </td>
      </tr>
    `).join('');
  }

  function renderLowStockAlerts(items) {
    const container = document.getElementById('lowStockList');
    if (!container) return;

    if (!items || items.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 2rem; color: var(--mint-glow);">
          <div style="font-size: 2rem; margin-bottom: 0.5rem;">✓</div>
          <strong>Healthy Inventory</strong>
          <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">All products are above their restock thresholds.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = items.map(p => `
      <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.85rem 0; border-bottom: 1px solid rgba(255,255,255,0.06);">
        <div>
          <div style="font-weight: 700; color: #fff;">${p.name}</div>
          <div style="font-size: 0.78rem; color: var(--gold-accent);">
            Only ${p.quantity} ${p.unit} remaining (Min: ${p.low_stock_threshold})
          </div>
        </div>
        <button class="btn-outline" style="padding: 0.35rem 0.85rem; font-size: 0.75rem;" onclick="quickRestock('${p.name}')">
          + Restock
        </button>
      </div>
    `).join('');
  }

  function renderBestSellers(items) {
    const container = document.getElementById('bestSellersList');
    if (!container || !items) return;

    container.innerHTML = items.map((p, i) => `
      <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.06);">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <span style="width: 24px; height: 24px; border-radius: 50%; background: rgba(139, 92, 246, 0.2); color: var(--purple-glow); display: grid; place-items: center; font-size: 0.75rem; font-weight: 800;">
            ${i + 1}
          </span>
          <div>
            <div style="font-weight: 700; color: #fff;">${p.name}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${p.category}</div>
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-weight: 800; color: var(--mint-glow);">${formatCurrency(p.revenue_generated)}</div>
          <div style="font-size: 0.75rem; color: var(--text-secondary);">${p.units_sold} ${p.unit} sold</div>
        </div>
      </div>
    `).join('');
  }

  function renderCharts(data) {
    if (typeof Chart === 'undefined') return;

    // Daily Sales Chart
    const salesCanvas = document.getElementById('salesTrendChart');
    if (salesCanvas && data.daily_trend) {
      const labels = data.daily_trend.map(d => {
        const parts = d.day.split('-');
        return `${parts[2]}/${parts[1]}`;
      });
      const revenues = data.daily_trend.map(d => d.revenue);

      if (salesChart) salesChart.destroy();

      const ctx = salesCanvas.getContext('2d');
      const gradient = ctx.createLinearGradient(0, 0, 0, 300);
      gradient.addColorStop(0, 'rgba(139, 92, 246, 0.45)');
      gradient.addColorStop(1, 'rgba(139, 92, 246, 0.0)');

      salesChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Daily Sales (₹)',
            data: revenues,
            borderColor: '#a855f7',
            borderWidth: 3,
            backgroundColor: gradient,
            fill: true,
            tension: 0.35,
            pointBackgroundColor: '#10b981',
            pointBorderColor: '#ffffff',
            pointRadius: 5,
            pointHoverRadius: 7
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#0f172a',
              titleColor: '#f8fafc',
              bodyColor: '#34d399',
              borderColor: '#8b5cf6',
              borderWidth: 1,
              callbacks: {
                label: (ctx) => ` Sales: ${formatCurrency(ctx.raw)}`
              }
            }
          },
          scales: {
            x: {
              grid: { color: 'rgba(255,255,255,0.05)' },
              ticks: { color: '#94a3b8' }
            },
            y: {
              grid: { color: 'rgba(255,255,255,0.05)' },
              ticks: {
                color: '#94a3b8',
                callback: (val) => '₹' + val.toLocaleString()
              }
            }
          }
        }
      });
    }

    // Category Distribution Chart
    const catCanvas = document.getElementById('categoryPieChart');
    if (catCanvas && data.category_dist) {
      const catLabels = data.category_dist.map(c => c.category);
      const catRevenues = data.category_dist.map(c => c.revenue);

      if (categoryChart) categoryChart.destroy();

      categoryChart = new Chart(catCanvas.getContext('2d'), {
        type: 'doughnut',
        data: {
          labels: catLabels,
          datasets: [{
            data: catRevenues,
            backgroundColor: [
              '#8b5cf6', '#10b981', '#f59e0b', '#06b6d4', '#ec4899', '#3b82f6'
            ],
            borderWidth: 2,
            borderColor: '#070913'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: { color: '#cbd5e1', font: { size: 11 } }
            }
          },
          cutout: '70%'
        }
      });
    }
  }

  window.quickRestock = function (productName) {
    const qty = prompt(`Enter quantity of ${productName} to restock:`, "10");
    if (qty && parseFloat(qty) > 0) {
      fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: `Add ${qty} ${productName}`, confirmed: true })
      }).then(r => r.json()).then(data => {
        alert(data.reply);
        loadDashboardData();
      });
    }
  };

  // Initial load & periodic polling
  loadDashboardData();
  window.addEventListener('inventoryUpdated', loadDashboardData);
  setInterval(loadDashboardData, 30000); // 30s auto-refresh
});
