async function api(path, options = {}) {
  const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function renderActivities(rows) {
  const tbody = document.querySelector('#activityTable tbody');
  tbody.innerHTML = rows.map(r => `<tr><td>${r.activity_date}</td><td>${r.title}</td><td>${r.category}</td><td>${r.duration_minutes}</td><td>${r.notes || ''}</td></tr>`).join('');
}

function renderBudgets(rows) {
  const tbody = document.querySelector('#budgetTable tbody');
  tbody.innerHTML = rows.map(r => `<tr><td>${r.month}</td><td>${r.name}</td><td>${r.monthly_limit}</td><td>${r.spent}</td><td>${r.remaining}</td></tr>`).join('');
}

function renderSummary(s) {
  document.getElementById('summary').innerHTML = `
    <p>Total Activity Time: <strong>${s.total_activity_minutes} mins</strong></p>
    <p>Total Budget Limit: <strong>$${s.total_budget_limit}</strong></p>
    <p>Total Spent: <strong>$${s.total_budget_spent}</strong></p>
    <p>Total Remaining: <strong>$${s.total_budget_remaining}</strong></p>`;
  document.getElementById('dbPath').textContent = s.database_path;
}

async function refresh() {
  const [activities, budgets, summary] = await Promise.all([
    api('/api/activities'), api('/api/budgets'), api('/api/summary')
  ]);
  renderActivities(activities);
  renderBudgets(budgets);
  renderSummary(summary);
}

document.getElementById('activityForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  try {
    await api('/api/activities', { method: 'POST', body: JSON.stringify(Object.fromEntries(form.entries())) });
    e.target.reset();
    await refresh();
  } catch (err) { alert(err.message); }
});

document.getElementById('budgetForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  try {
    await api('/api/budgets', { method: 'POST', body: JSON.stringify(Object.fromEntries(form.entries())) });
    e.target.reset();
    await refresh();
  } catch (err) { alert(err.message); }
});

const now = new Date();
document.querySelector('input[name="activity_date"]').value = now.toISOString().slice(0, 10);
document.querySelector('input[name="month"]').value = now.toISOString().slice(0, 7);
refresh();
