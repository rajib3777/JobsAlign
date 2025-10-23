// app.js — single production-ready JS (modules not necessary; keep single file)
//
// Responsibilities:
// - Parallel fetch data from 13 apps: accounts, analytics, marketplace, payments,
//   recommendations, categories, referrals, reviews, notifications, subscriptions,
//   chats (ws), disputes, support.
// - Render to DOM with skeleton -> real content transitions
// - WebSocket preview for notifications & quick chat messages
// - Graceful fallback and client cache (sessionStorage) to reduce load
// - Small utilities: debounce, fetch wrapper, toast

const API_BASE = window.__API_BASE__ || (location.origin + '/api'); // change if needed

// ---------------- helpers ----------------
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const $id = id => document.getElementById(id);
const esc = s => (s==null?'':String(s)).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function toast(msg, err=false){
  const t = document.createElement('div');
  t.textContent = msg;
  t.className = `fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg text-sm ${err? 'bg-red-600 text-white' : 'bg-slate-900 text-white'}`;
  document.body.appendChild(t);
  setTimeout(()=> t.classList.add('opacity-0'), 2000);
  setTimeout(()=> t.remove(), 2800);
}

// fetch wrapper with timeout & token support
async function fetchJSON(path, {method='GET', body=null, token=null, timeout=9000} = {}){
  const controller = new AbortController();
  const id = setTimeout(()=> controller.abort(), timeout);
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (body && !(body instanceof FormData)) headers['Content-Type'] = 'application/json';
  try {
    const res = await fetch(API_BASE + path, {
      method,
      headers,
      body: body && !(body instanceof FormData) ? JSON.stringify(body) : body,
      signal: controller.signal,
      credentials: 'same-origin'
    });
    clearTimeout(id);
    if (res.status === 204) return null;
    const json = await res.json().catch(()=> null);
    if (!res.ok) throw json || {error:'http', status: res.status};
    return json;
  } catch (err) {
    clearTimeout(id);
    if (err.name === 'AbortError') throw {error:'timeout'};
    throw err;
  }
}

// debounce
function debounce(fn, wait=300){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), wait); }; }

// ---------------- rendering templates ----------------
function jobCard(j){
  return `
    <article class="p-5 bg-white rounded-2xl shadow-sm card-hover">
      <div class="flex items-start justify-between">
        <div class="max-w-[70%]">
          <h3 class="font-semibold text-lg">${esc(j.title)}</h3>
          <p class="text-sm text-slate-500 mt-1">${esc(j.short_description || '')}</p>
        </div>
        <div class="text-emerald-600 font-bold">${j.budget_min? '৳'+esc(j.budget_min): '৳—'}</div>
      </div>
      <div class="mt-4 flex items-center justify-between text-xs text-slate-400">
        <div>Posted • ${j.posted_days_ago ?? '—'} days</div>
        <a href="/pages/jobs.html?id=${j.id}" class="text-emerald-600">View →</a>
      </div>
    </article>`;
}

function freelancerItem(u){
  return `<div class="flex items-center gap-3">
    <div class="w-10 h-10 rounded-full bg-slate-100 overflow-hidden">${u.avatar? `<img src="${u.avatar}" alt="${esc(u.username)}">`:''}</div>
    <div><div class="font-semibold text-sm">${esc(u.username)}</div><div class="text-xs text-slate-400">${esc(u.title||'')}</div></div>
  </div>`;
}

function testimonialTpl(t){
  return `<blockquote class="p-4 bg-slate-50 rounded-lg text-sm">
    <p class="italic">“${esc(t.comment)}”</p>
    <div class="mt-2 text-xs text-slate-500">— ${esc(t.user_display||t.user||'Client')}</div>
  </blockquote>`;
}

function categoryChip(c){
  return `<div class="p-3 bg-white rounded-lg shadow-sm text-center text-sm">${esc(c.name)}</div>`;
}

// ---------------- main bootstrap ----------------
async function bootstrap(){
  // show skeletons already in HTML
  const token = localStorage.getItem('token') || null;

  // use cached responses (sessionStorage) to reduce visible loading
  const cached = (k, ttl=60) => {
    try {
      const raw = sessionStorage.getItem(k);
      if (!raw) return null;
      const obj = JSON.parse(raw);
      if ((Date.now() - obj.t) / 1000 > ttl) return null;
      return obj.v;
    } catch { return null; }
  };
  const setCache = (k,v) => sessionStorage.setItem(k, JSON.stringify({t: Date.now(), v}));

  // endpoints (13 apps)
  const endpoints = {
    accounts_me: '/accounts/me/',
    analytics_stats: '/analytics/stats/',
    featured_projects: '/marketplace/projects/?featured=true&limit=6',
    wallet: '/payments/wallet/',
    recommendations: '/recommendations/projects/?limit=6',
    categories: '/categories/top/?limit=9',
    referrals: '/referrals/me/',
    reviews_latest: '/reviews/latest/?limit=6',
    notifications_count: '/notifications/unread_count/',
    subscriptions: '/subscriptions/me/',
    support_recent: '/support/tickets/recent/',
    disputes_open: '/disputes/open/?limit=5',
    freelancers_top: '/freelancers/top/?limit=6'
  };

  // try cached fetches then network (parallel)
  const promises = Object.entries(endpoints).map(async ([key, path])=>{
    const c = cached(key);
    if (c) return [key, c];
    try {
      const res = await fetchJSON(path, { token }).catch(()=> null);
      setCache(key, res);
      return [key, res];
    } catch(err){
      console.warn('err', key, err);
      return [key, null];
    }
  });

  const results = await Promise.all(promises);
  const data = Object.fromEntries(results);

  // RENDER: analytics KPIs
  if (data.analytics_stats){
    $id('stat_projects').textContent = data.analytics_stats.total_projects ?? data.analytics_stats.projects ?? '—';
    $id('stat_freelancers').textContent = data.analytics_stats.total_freelancers ?? '—';
    $id('stat_paid').textContent = data.analytics_stats.total_paid ? `৳${data.analytics_stats.total_paid}` : '৳—';
  }

  // RENDER: featured project
  if (data.featured_projects && Array.isArray(data.featured_projects.results? data.featured_projects.results : data.featured_projects) ){
    const arr = data.featured_projects.results ?? data.featured_projects;
    if (arr.length){
      const job = arr[0];
      $id('featured_title').textContent = job.title || '—';
      $id('featured_price').textContent = job.budget_max? `৳${job.budget_max}` : '৳—';
      $id('featured_link').href = `/pages/jobs.html?id=${job.id}`;
      // reveal with animation
      setTimeout(()=> $id('featured').classList.add('visible'), 300);
    }
  }

  // RENDER jobs grid (recommendations fallback to featured list)
  let jobsList = data.recommendations || (data.featured_projects && (data.featured_projects.results ?? data.featured_projects));
  if (Array.isArray(jobsList) && jobsList.length){
    $id('jobsGrid').innerHTML = jobsList.map(jobCard).join('');
  } else {
    $id('jobsGrid').innerHTML = '<div class="p-6 bg-white rounded-2xl text-center">No jobs found</div>';
  }

  // RENDER freelancers
  if (data.freelancers_top && Array.isArray(data.freelancers_top)){
    $id('freelancers').innerHTML = data.freelancers_top.map(freelancerItem).join('');
  }

  // RENDER categories
  if (data.categories && Array.isArray(data.categories)){
    $id('categories').innerHTML = data.categories.map(categoryChip).join('');
  }

  // RENDER testimonials
  if (data.reviews_latest && Array.isArray(data.reviews_latest)){
    $id('testimonials').innerHTML = data.reviews_latest.map(testimonialTpl).join('');
  }

  // RENDER mini summary (accounts + wallet + subscriptions)
  const parts = [];
  if (data.accounts_me) parts.push(`Hi, ${data.accounts_me.username || data.accounts_me.email || 'User'}`);
  if (data.wallet && data.wallet.balance != null) parts.push(`Balance: ৳${data.wallet.balance}`);
  if (data.subscriptions && data.subscriptions.plan) parts.push(`Plan: ${data.subscriptions.plan}`);
  $id('miniSummary').textContent = parts.join(' • ') || 'Sign in to see personalized summary';

  // REFERRAL - attach copy functionality
  const copyBtn = $id('copyReferral');
  if (copyBtn){
    copyBtn.addEventListener('click', async ()=>{
      try {
        const ref = data.referrals || await fetchJSON('/referrals/me/', { token });
        const link = ref?.url || (location.origin + '/r/' + (ref?.code || 'yourcode'));
        await navigator.clipboard.writeText(link);
        toast('Referral link copied');
      } catch(e){
        console.error(e);
        toast('Could not copy referral', true);
      }
    });
  }

  // Notifications count live (if available)
  if (data.notifications_count && typeof data.notifications_count.unread === 'number'){
    // you might show badge in nav later
    console.log('unread notifications:', data.notifications_count.unread);
  }

  // WebSocket: notifications & chat preview
  try {
    const token = localStorage.getItem('token') || '';
    if (token){
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      const notifSocket = new WebSocket(`${proto}://${location.host}/ws/notifications/?token=${encodeURIComponent(token)}`);
      notifSocket.onmessage = e => {
        try{
          const payload = JSON.parse(e.data);
          // quick toast for incoming notification
          toast(payload.message || 'New notification');
        }catch{}
      };
      // chat preview socket (optional)
      const chatSocket = new WebSocket(`${proto}://${location.host}/ws/chats/preview/?token=${encodeURIComponent(token)}`);
      chatSocket.onmessage = e => {
        // integrate preview area if you build one
        console.log('chat preview', e.data);
      };
    }
  } catch (e){ console.warn('WS not initialized', e); }

  // lazy animate entrance: observe cards
  const io = new IntersectionObserver(entries=>{
    entries.forEach(en=>{
      if (en.isIntersecting){
        en.target.classList.add('animate-fade-up');
        io.unobserve(en.target);
      }
    });
  }, { threshold: 0.12 });
  $$('.card-hover, #categoriesCard, #testimonialsCard, #freelancersCard').forEach(el => io.observe(el));
}

// ---------------- event bindings ----------------
function attachEvents(){
  const searchBtn = $id('searchBtn');
  const q = $id('q');
  if (searchBtn){
    searchBtn.addEventListener('click', ()=> {
      const query = (q && q.value) ? q.value.trim() : '';
      location.href = `/pages/jobs.html?q=${encodeURIComponent(query)}`;
    });
  }

  // mobile menu toggle
  const mobile = $id('mobileMenu');
  if (mobile) mobile.addEventListener('click', ()=> {
    const nav = document.querySelector('nav');
    if (nav) nav.classList.toggle('hidden');
  });

  // header scrolled style
  const hdr = document.getElementById('siteHeader');
  window.addEventListener('scroll', ()=> {
    if (window.scrollY > 8) hdr.classList.add('shadow-lg');
    else hdr.classList.remove('shadow-lg');
  }, { passive: true });
}

// run
document.addEventListener('DOMContentLoaded', ()=> {
  attachEvents();
  bootstrap().catch(err => {
    console.error('bootstrap error', err);
    toast('Some data failed to load', true);
  });
});
