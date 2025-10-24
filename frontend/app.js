const API_BASE = "http://127.0.0.1:8000/api/";

async function loadCategories() {
  const res = await fetch(`${API_BASE}categories/`);
  const data = await res.json();
  const container = document.getElementById('categories');
  container.innerHTML = data.map(cat => `
    <div class="p-4 bg-white rounded-xl shadow hover:shadow-lg transition">
      <h3 class="font-semibold text-lg">${cat.name}</h3>
      <p class="text-gray-500">${cat.description || ''}</p>
    </div>
  `).join('');
}

document.addEventListener('DOMContentLoaded', loadCategories);
