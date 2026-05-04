async function api(path, options = {}) {
  const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

const money = (v) => `$${Number(v).toFixed(2)}`;

function renderActivities(rows) {
  document.querySelector('#activityTable tbody').innerHTML = rows.map(r => `<tr><td>${r.activity_date}</td><td>${r.title}</td><td>${r.category}</td><td>${r.duration_minutes}</td><td>${r.notes || ''}</td></tr>`).join('');
}
function renderBudgets(rows) {
  document.querySelector('#budgetTable tbody').innerHTML = rows.map(r => `<tr><td>${r.month}</td><td>${r.name}</td><td>${money(r.monthly_limit)}</td><td>${money(r.spent)}</td><td>${money(r.remaining)}</td></tr>`).join('');
  const select = document.getElementById('budgetSelect');
  select.innerHTML = '<option value="">No linked budget</option>' + rows.map(r => `<option value="${r.id}">${r.name} (${r.month})</option>`).join('');
}
function renderExpenses(rows) {
  document.querySelector('#expenseTable tbody').innerHTML = rows.map(r => `<tr><td>${r.expense_date}</td><td>${r.title}</td><td>${r.budget_name || '-'}</td><td>${money(r.amount)}</td><td>${r.notes || ''}</td></tr>`).join('');
}
function renderSummary(s) {
  document.getElementById('minutesVal').textContent = s.total_activity_minutes;
  document.getElementById('limitVal').textContent = money(s.total_budget_limit);
  document.getElementById('remainingVal').textContent = money(s.total_budget_remaining);
  document.getElementById('dbPath').textContent = `Portable DB: ${s.database_path}`;
}

async function refresh() {
  const [activities, budgets, expenditures, summary] = await Promise.all([
    api('/api/activities'), api('/api/budgets'), api('/api/expenditures'), api('/api/summary')
  ]);
  renderActivities(activities); renderBudgets(budgets); renderExpenses(expenditures); renderSummary(summary);
}

function bindForm(formId, endpoint) {
  document.getElementById(formId).addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const payload = Object.fromEntries(new FormData(e.target).entries());
      await api(endpoint, { method: 'POST', body: JSON.stringify(payload) });
      e.target.reset();
      const now = new Date();
      document.querySelector('input[name="activity_date"]').value = now.toISOString().slice(0, 10);
      document.querySelector('input[name="expense_date"]').value = now.toISOString().slice(0, 10);
      document.querySelector('input[name="month"]').value = now.toISOString().slice(0, 7);
      await refresh();
    } catch (err) { alert(err.message); }
  });
}

const now = new Date();
document.querySelector('input[name="activity_date"]').value = now.toISOString().slice(0, 10);
document.querySelector('input[name="expense_date"]').value = now.toISOString().slice(0, 10);
document.querySelector('input[name="month"]').value = now.toISOString().slice(0, 7);
bindForm('activityForm', '/api/activities');
bindForm('budgetForm', '/api/budgets');
bindForm('expenseForm', '/api/expenditures');
refresh();
