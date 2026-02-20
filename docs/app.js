/* Tiger Marketing CRM - Static GitHub Pages App
   All data stored in localStorage for phone/offline access */

// ===== DATA LAYER =====
const DB = {
    get(key) { return JSON.parse(localStorage.getItem('tm_' + key) || '[]'); },
    set(key, data) { localStorage.setItem('tm_' + key, JSON.stringify(data)); },
    nextId(key) {
        const items = this.get(key);
        return items.length ? Math.max(...items.map(i => i.id)) + 1 : 1;
    }
};

// Seed reference data on first load
function seedData() {
    if (localStorage.getItem('tm_seeded')) return;

    DB.set('stores', [
        {id:1, rank:1, name:"Kroger", category:"Grocery/Supermarket", address:"300 North Dean Road", city:"Auburn", zip:"36830", neighborhood:"Near Moores Mill / Cloverleaf"},
        {id:2, rank:2, name:"Publix", category:"Grocery/Supermarket", address:"138 South Gay Street", city:"Auburn", zip:"36830", neighborhood:"Downtown Auburn"},
        {id:3, rank:3, name:"Auburn Hardware", category:"Hardware Store", address:"117 East Magnolia Avenue", city:"Auburn", zip:"36830", neighborhood:"Downtown Auburn"},
        {id:4, rank:4, name:"Russell Building Supply", category:"Hardware Store", address:"141 Bragg Avenue", city:"Auburn", zip:"36830", neighborhood:"Near University Estates"},
        {id:5, rank:5, name:"fab'rik", category:"Clothing Store", address:"140 North College Street", city:"Auburn", zip:"36830", neighborhood:"Downtown Auburn"},
        {id:6, rank:6, name:"Elisabet Boutique", category:"Clothing Store", address:"124 North College Street", city:"Auburn", zip:"36830", neighborhood:"Downtown Auburn"},
        {id:7, rank:7, name:"Ellie Clothing", category:"Clothing Store", address:"113 North College Street", city:"Auburn", zip:"36830", neighborhood:"Downtown Auburn"},
        {id:8, rank:8, name:"Johnston & Malone Book Store", category:"Bookstore", address:"115 South College Street", city:"Auburn", zip:"36830", neighborhood:"Downtown Auburn"},
        {id:9, rank:9, name:"Woodley Enterprises", category:"Computer Store", address:"557 Temple Street", city:"Auburn", zip:"36830", neighborhood:"Near Grove Hill"},
        {id:10, rank:10, name:"Z&Z Tobacco & Spirits", category:"Liquor Store", address:"203 Opelika Road", city:"Auburn", zip:"36830", neighborhood:"Near Yarbrough Farms"}
    ]);

    DB.set('neighborhoods', [
        {id:1, rank:1, type:"NEIGHBORHOOD", name:"Moores Mill", zip:"36830", medianHome:553072, features:"Top 15% income in America. Golf course community, country club, custom homes. 40% have advanced degrees."},
        {id:2, rank:2, type:"NEIGHBORHOOD", name:"Cloverleaf / Windsor Forest", zip:"36830", medianHome:null, features:"Ranked 2nd most expensive Auburn neighborhood."},
        {id:3, rank:3, type:"NEIGHBORHOOD", name:"Willow Creek Farms", zip:"36830", medianHome:null, features:"Ranked 3rd most expensive. Upscale family neighborhood."},
        {id:4, rank:4, type:"NEIGHBORHOOD", name:"Yarbrough Farms / AU Club", zip:"36830", medianHome:null, features:"Premium prices. Proximity to AU campus. High demand."},
        {id:5, rank:5, type:"NEIGHBORHOOD", name:"Downtown Auburn", zip:"36830", medianHome:null, features:"Premium location near university. High demand, walkable."},
        {id:6, rank:6, type:"NEIGHBORHOOD", name:"University Estates", zip:"36830", medianHome:null, features:"Faculty and professional housing near campus."},
        {id:7, rank:7, type:"NEIGHBORHOOD", name:"Granite Hills / Head Estates", zip:"36830", medianHome:null, features:"Established upscale area."},
        {id:8, rank:8, type:"NEIGHBORHOOD", name:"Grove Hill", zip:"36830", medianHome:null, features:"Homes $300K-$500K range. Established neighborhood."},
        {id:9, rank:9, type:"NEIGHBORHOOD", name:"Stone Creek / Cobblestone", zip:"36832", medianHome:null, features:"Ranked 9th most expensive Auburn neighborhood."},
        {id:10, rank:10, type:"NEIGHBORHOOD", name:"Asheton Lakes", zip:"36830", medianHome:null, features:"HOA community with lake amenities."}
    ]);

    DB.set('zipcodes', [
        {id:1, rank:1, name:"Auburn (Primary)", zip:"36830", medianIncome:70188, avgIncome:103989, pctOver200k:12.9, features:"Highest income Auburn zip. 45-64 age bracket earns $22K median."},
        {id:2, rank:2, name:"Opelika (West)", zip:"36804", medianIncome:null, avgIncome:null, pctOver200k:null, features:"Top 1 most expensive homes in Auburn metro."},
        {id:3, rank:3, name:"Auburn (University)", zip:"36832", medianIncome:42717, avgIncome:69895, pctOver200k:6.0, features:"Heavy student population lowers median. Still has pockets of wealth."},
        {id:4, rank:4, name:"Opelika (East)", zip:"36801", medianIncome:null, avgIncome:null, pctOver200k:null, features:"Top 2 most expensive homes in Auburn metro."},
        {id:5, rank:5, name:"Waverly", zip:"36879", medianIncome:93029, avgIncome:null, pctOver200k:null, features:"Higher median income than Auburn 36830. Rural luxury estates."},
        {id:6, rank:6, name:"Salem", zip:"36874", medianIncome:null, avgIncome:null, pctOver200k:null, features:"Growing area. 5yr home value up 39.7%."}
    ]);

    localStorage.setItem('tm_seeded', '1');
}

// ===== HELPERS =====
function $(id) { return document.getElementById(id); }
function fmt$(n) { return n ? '$' + Number(n).toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '-'; }
function fmtDate(d) {
    if (!d) return '-';
    const dt = new Date(d);
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
function today() { return new Date().toISOString().split('T')[0]; }
function now() { return new Date().toISOString(); }
function badgeClass(val) { return 'badge badge-' + (val || '').toLowerCase().replace(/\s+/g, '-'); }

function flash(msg, type) {
    const el = $('flash-area');
    el.innerHTML = `<div class="flash ${type}">${type === 'success' ? '\u2705' : '\u274C'} ${msg}</div>`;
    setTimeout(() => el.innerHTML = '', 4000);
}

function getContactName(contactId) {
    if (!contactId) return '-';
    const c = DB.get('contacts').find(x => x.id == contactId);
    return c ? (c.firstName + ' ' + c.lastName) : '-';
}

function getDealName(dealId) {
    if (!dealId) return '-';
    const d = DB.get('deals').find(x => x.id == dealId);
    return d ? d.name : '-';
}

function populateContactSelect(selectId, selectedId) {
    const sel = $(selectId);
    const contacts = DB.get('contacts');
    sel.innerHTML = '<option value="">-- Select Contact --</option>';
    contacts.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.firstName + ' ' + c.lastName + (c.company ? ' (' + c.company + ')' : '');
        if (c.id == selectedId) opt.selected = true;
        sel.appendChild(opt);
    });
}

function populateDealSelect(selectId, selectedId) {
    const sel = $(selectId);
    const deals = DB.get('deals');
    sel.innerHTML = '<option value="">-- None --</option>';
    deals.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.textContent = d.name;
        if (d.id == selectedId) opt.selected = true;
        sel.appendChild(opt);
    });
}

// ===== NAVIGATION =====
let currentPage = 'dashboard';

function showPage(page, opts) {
    currentPage = page;
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(p => p.style.display = 'none');

    // Update sidebar
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.querySelector(`[data-page="${page}"]`);
    if (navItem) navItem.classList.add('active');

    // Close mobile sidebar
    $('sidebar').classList.remove('open');
    $('sidebar-overlay').classList.remove('open');

    const titles = {
        'dashboard': ['Dashboard', 'Tiger Marketing Overview'],
        'contacts': ['Contacts', 'Manage your leads and customers'],
        'contact-form': ['New Contact', 'Add a new contact'],
        'contact-detail': ['Contact Details', ''],
        'deals': ['Deals', 'Sales pipeline'],
        'deal-form': ['New Deal', 'Create a new deal'],
        'tasks': ['Tasks', 'Track your to-dos'],
        'task-form': ['New Task', 'Create a task'],
        'interactions': ['Interactions', 'Communication log'],
        'interaction-form': ['New Interaction', 'Log a communication'],
        'campaigns': ['Campaigns', 'Marketing campaigns'],
        'campaign-form': ['New Campaign', 'Create a campaign'],
        'territories': ['Territories', 'Auburn area intel'],
        'stores': ['Top Stores', 'Neighborhood store targets']
    };

    const [title, subtitle] = titles[page] || [page, ''];
    $('page-title').textContent = title;
    $('page-subtitle').textContent = subtitle;

    // Header action buttons
    const actions = {
        'contacts': '<button class="btn btn-primary" onclick="showPage(\'contact-form\')">+ <span class="btn-text">New Contact</span></button>',
        'deals': '<button class="btn btn-primary" onclick="showPage(\'deal-form\')">+ <span class="btn-text">New Deal</span></button>',
        'tasks': '<button class="btn btn-primary" onclick="showPage(\'task-form\')">+ <span class="btn-text">New Task</span></button>',
        'interactions': '<button class="btn btn-primary" onclick="showPage(\'interaction-form\')">+ <span class="btn-text">Log Interaction</span></button>',
        'campaigns': '<button class="btn btn-primary" onclick="showPage(\'campaign-form\')">+ <span class="btn-text">New Campaign</span></button>'
    };
    $('header-actions').innerHTML = actions[page] || '';

    // Show page and render
    const pageEl = $('page-' + page);
    if (pageEl) pageEl.style.display = '';

    // Render page data
    switch(page) {
        case 'dashboard': renderDashboard(); break;
        case 'contacts': renderContacts(); break;
        case 'contact-form': initContactForm(opts); break;
        case 'contact-detail': renderContactDetail(opts); break;
        case 'deals': renderDeals(); break;
        case 'deal-form': initDealForm(opts); break;
        case 'tasks': renderTasks(); break;
        case 'task-form': initTaskForm(opts); break;
        case 'interactions': renderInteractions(); break;
        case 'interaction-form': initInteractionForm(opts); break;
        case 'campaigns': renderCampaigns(); break;
        case 'campaign-form': initCampaignForm(opts); break;
        case 'territories': renderTerritories(); break;
        case 'stores': renderStores(); break;
    }

    updateNavCounts();
    window.scrollTo(0, 0);
}

function toggleSidebar() {
    $('sidebar').classList.toggle('open');
    $('sidebar-overlay').classList.toggle('open');
}

function updateNavCounts() {
    const contacts = DB.get('contacts');
    $('nav-contacts-count').textContent = contacts.length;

    const tasks = DB.get('tasks');
    const pending = tasks.filter(t => t.status !== 'Completed').length;
    const el = $('nav-tasks-count');
    el.textContent = pending;
    el.style.display = pending > 0 ? '' : 'none';
}

// ===== DASHBOARD =====
function renderDashboard() {
    const contacts = DB.get('contacts');
    const deals = DB.get('deals');
    const tasks = DB.get('tasks');
    const interactions = DB.get('interactions');
    const campaigns = DB.get('campaigns');

    const newLeads = contacts.filter(c => c.leadStatus === 'New').length;
    const activeDeals = deals.filter(d => !['Won','Lost'].includes(d.stage)).length;
    const pipelineValue = deals.filter(d => !['Won','Lost'].includes(d.stage)).reduce((s,d) => s + (Number(d.amount)||0), 0);
    const wonRevenue = deals.filter(d => d.stage === 'Won').reduce((s,d) => s + (Number(d.amount)||0), 0);
    const openTasks = tasks.filter(t => t.status !== 'Completed').length;
    const overdueTasks = tasks.filter(t => t.status !== 'Completed' && t.dueDate && t.dueDate < today()).length;

    $('dashboard-stats').innerHTML = `
        <div class="stat-card accent"><div class="label">Total Contacts</div><div class="value">${contacts.length}</div></div>
        <div class="stat-card green"><div class="label">New Leads</div><div class="value">${newLeads}</div></div>
        <div class="stat-card purple"><div class="label">Active Deals</div><div class="value">${activeDeals}</div></div>
        <div class="stat-card yellow"><div class="label">Pipeline Value</div><div class="value money">${pipelineValue.toLocaleString()}</div></div>
        <div class="stat-card green"><div class="label">Won Revenue</div><div class="value money">${wonRevenue.toLocaleString()}</div></div>
        <div class="stat-card ${overdueTasks > 0 ? 'red' : 'orange'}"><div class="label">Open Tasks</div><div class="value">${openTasks}${overdueTasks > 0 ? ' <span style="font-size:14px;color:var(--red)">(' + overdueTasks + ' overdue)</span>' : ''}</div></div>
    `;

    // Recent contacts
    const recentContacts = [...contacts].sort((a,b) => (b.createdDate||'').localeCompare(a.createdDate||'')).slice(0,5);
    const rcBody = $('dash-recent-contacts').querySelector('tbody');
    if (recentContacts.length === 0) {
        rcBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No contacts yet</td></tr>';
    } else {
        rcBody.innerHTML = recentContacts.map(c => `
            <tr onclick="showPage('contact-detail',{id:${c.id}})" style="cursor:pointer">
                <td><a>${c.firstName} ${c.lastName}</a></td>
                <td><span class="${badgeClass(c.leadStatus)}">${c.leadStatus||'-'}</span></td>
                <td>${c.contactType||'-'}</td>
                <td>${fmtDate(c.createdDate)}</td>
            </tr>`).join('');
    }

    // Recent deals
    const recentDeals = [...deals].sort((a,b) => (b.createdDate||'').localeCompare(a.createdDate||'')).slice(0,5);
    const rdBody = $('dash-recent-deals').querySelector('tbody');
    if (recentDeals.length === 0) {
        rdBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No deals yet</td></tr>';
    } else {
        rdBody.innerHTML = recentDeals.map(d => `
            <tr>
                <td>${d.name}</td>
                <td>${getContactName(d.contactId)}</td>
                <td><span class="${badgeClass(d.stage)}">${d.stage}</span></td>
                <td>${fmt$(d.amount)}</td>
            </tr>`).join('');
    }

    // Upcoming tasks
    const upcoming = tasks.filter(t => t.status !== 'Completed').sort((a,b) => (a.dueDate||'9').localeCompare(b.dueDate||'9')).slice(0,5);
    const utBody = $('dash-upcoming-tasks').querySelector('tbody');
    if (upcoming.length === 0) {
        utBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No tasks</td></tr>';
    } else {
        utBody.innerHTML = upcoming.map(t => {
            const overdue = t.dueDate && t.dueDate < today() ? 'overdue' : t.status.toLowerCase().replace(/\s/g,'-');
            return `
            <tr>
                <td>${t.description}</td>
                <td>${fmtDate(t.dueDate)}</td>
                <td><span class="${badgeClass(t.priority)}">${t.priority}</span></td>
                <td><span class="${badgeClass(overdue)}">${t.dueDate && t.dueDate < today() ? 'Overdue' : t.status}</span></td>
            </tr>`;
        }).join('');
    }
}

// ===== CONTACTS =====
function renderContacts() {
    let contacts = DB.get('contacts');
    const search = ($('contact-search')?.value || '').toLowerCase();
    const statusFilter = $('contact-status-filter')?.value;
    const typeFilter = $('contact-type-filter')?.value;

    if (search) contacts = contacts.filter(c =>
        (c.firstName + ' ' + c.lastName + ' ' + (c.company||'') + ' ' + (c.email||'') + ' ' + (c.phone||'')).toLowerCase().includes(search)
    );
    if (statusFilter) contacts = contacts.filter(c => c.leadStatus === statusFilter);
    if (typeFilter) contacts = contacts.filter(c => c.contactType === typeFilter);

    contacts.sort((a,b) => (b.createdDate||'').localeCompare(a.createdDate||''));

    const tbody = $('contacts-table').querySelector('tbody');
    if (contacts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="icon">\u{1F465}</div><p>No contacts found</p><button class="btn btn-primary" onclick="showPage('contact-form')">+ Add Contact</button></div></td></tr>`;
    } else {
        tbody.innerHTML = contacts.map(c => `
            <tr>
                <td><a onclick="showPage('contact-detail',{id:${c.id}})">${c.firstName} ${c.lastName}</a></td>
                <td>${c.company||'-'}</td>
                <td>${c.phone||'-'}</td>
                <td><span class="${badgeClass(c.leadStatus)}">${c.leadStatus||'-'}</span></td>
                <td><span class="${badgeClass(c.contactType)}">${c.contactType||'-'}</span></td>
                <td>${fmt$(c.estimatedValue)}</td>
                <td class="action-links">
                    <a onclick="showPage('contact-form',{id:${c.id}})">Edit</a>
                    <a class="text-red" onclick="deleteContact(${c.id})">Del</a>
                </td>
            </tr>`).join('');
    }
}

function initContactForm(opts) {
    const form = $('contact-form');
    form.reset();
    $('cf-id').value = '';
    $('cf-city').value = 'Auburn';
    $('cf-state').value = 'AL';
    $('cf-assigned').value = 'Jason';

    if (opts && opts.id) {
        const c = DB.get('contacts').find(x => x.id == opts.id);
        if (c) {
            $('page-title').textContent = 'Edit Contact';
            $('page-subtitle').textContent = c.firstName + ' ' + c.lastName;
            $('cf-id').value = c.id;
            $('cf-first').value = c.firstName || '';
            $('cf-last').value = c.lastName || '';
            $('cf-company').value = c.company || '';
            $('cf-title').value = c.jobTitle || '';
            $('cf-email').value = c.email || '';
            $('cf-phone').value = c.phone || '';
            $('cf-address').value = c.address || '';
            $('cf-city').value = c.city || 'Auburn';
            $('cf-state').value = c.state || 'AL';
            $('cf-zip').value = c.zip || '';
            $('cf-neighborhood').value = c.neighborhood || '';
            $('cf-type').value = c.contactType || 'Lead';
            $('cf-source').value = c.leadSource || 'Door Knock';
            $('cf-status').value = c.leadStatus || 'New';
            $('cf-services').value = c.interestServices || '';
            $('cf-property').value = c.propertyType || 'Residential';
            $('cf-value').value = c.estimatedValue || '';
            $('cf-rating').value = c.rating || '';
            $('cf-assigned').value = c.assignedTo || 'Jason';
            $('cf-notes').value = c.notes || '';
        }
    }
}

function saveContact(e) {
    e.preventDefault();
    const contacts = DB.get('contacts');
    const id = $('cf-id').value;

    const data = {
        firstName: $('cf-first').value,
        lastName: $('cf-last').value,
        company: $('cf-company').value,
        jobTitle: $('cf-title').value,
        email: $('cf-email').value,
        phone: $('cf-phone').value,
        address: $('cf-address').value,
        city: $('cf-city').value,
        state: $('cf-state').value,
        zip: $('cf-zip').value,
        neighborhood: $('cf-neighborhood').value,
        contactType: $('cf-type').value,
        leadSource: $('cf-source').value,
        leadStatus: $('cf-status').value,
        interestServices: $('cf-services').value,
        propertyType: $('cf-property').value,
        estimatedValue: $('cf-value').value ? parseFloat($('cf-value').value) : null,
        rating: $('cf-rating').value ? parseInt($('cf-rating').value) : null,
        assignedTo: $('cf-assigned').value,
        notes: $('cf-notes').value,
        updatedDate: now()
    };

    if (id) {
        const idx = contacts.findIndex(c => c.id == id);
        if (idx >= 0) { contacts[idx] = { ...contacts[idx], ...data }; }
    } else {
        data.id = DB.nextId('contacts');
        data.createdDate = now();
        contacts.push(data);
    }

    DB.set('contacts', contacts);
    flash(id ? 'Contact updated!' : 'Contact created!', 'success');
    showPage('contacts');
}

function deleteContact(id) {
    if (!confirm('Delete this contact?')) return;
    let contacts = DB.get('contacts');
    contacts = contacts.filter(c => c.id != id);
    DB.set('contacts', contacts);
    flash('Contact deleted.', 'success');
    renderContacts();
    updateNavCounts();
}

// ===== CONTACT DETAIL =====
function renderContactDetail(opts) {
    if (!opts || !opts.id) { showPage('contacts'); return; }
    const c = DB.get('contacts').find(x => x.id == opts.id);
    if (!c) { showPage('contacts'); return; }

    $('page-title').textContent = c.firstName + ' ' + c.lastName;
    $('page-subtitle').textContent = c.company || c.contactType || '';

    const deals = DB.get('deals').filter(d => d.contactId == c.id);
    const tasks = DB.get('tasks').filter(t => t.contactId == c.id);
    const interactions = DB.get('interactions').filter(i => i.contactId == c.id);

    const stars = c.rating ? '\u2B50'.repeat(c.rating) : '-';

    $('contact-detail-content').innerHTML = `
        <div class="detail-header">
            <div>
                <div class="name">${c.firstName} ${c.lastName}</div>
                <div class="meta">${c.company || ''} ${c.jobTitle ? '- ' + c.jobTitle : ''}</div>
            </div>
            <div class="action-links">
                <button class="btn btn-primary btn-sm" onclick="showPage('contact-form',{id:${c.id}})">Edit</button>
                <button class="btn btn-success btn-sm" onclick="showPage('interaction-form',{contactId:${c.id}})">Log Interaction</button>
                <button class="btn btn-secondary btn-sm" onclick="showPage('deal-form',{contactId:${c.id}})">+ Deal</button>
                <button class="btn btn-secondary btn-sm" onclick="showPage('task-form',{contactId:${c.id}})">+ Task</button>
            </div>
        </div>

        <div class="card">
            <div class="card-header"><h3>Contact Info</h3></div>
            <div class="card-body">
                <div class="detail-info-grid">
                    <div class="detail-field"><div class="label">Email</div><div class="value">${c.email || '-'}</div></div>
                    <div class="detail-field"><div class="label">Phone</div><div class="value">${c.phone || '-'}</div></div>
                    <div class="detail-field"><div class="label">Address</div><div class="value">${c.address || '-'}, ${c.city||''} ${c.state||''} ${c.zip||''}</div></div>
                    <div class="detail-field"><div class="label">Neighborhood</div><div class="value">${c.neighborhood || '-'}</div></div>
                    <div class="detail-field"><div class="label">Status</div><div class="value"><span class="${badgeClass(c.leadStatus)}">${c.leadStatus||'-'}</span></div></div>
                    <div class="detail-field"><div class="label">Type</div><div class="value"><span class="${badgeClass(c.contactType)}">${c.contactType||'-'}</span></div></div>
                    <div class="detail-field"><div class="label">Lead Source</div><div class="value">${c.leadSource || '-'}</div></div>
                    <div class="detail-field"><div class="label">Property Type</div><div class="value">${c.propertyType || '-'}</div></div>
                    <div class="detail-field"><div class="label">Interested In</div><div class="value">${c.interestServices || '-'}</div></div>
                    <div class="detail-field"><div class="label">Est. Value</div><div class="value">${fmt$(c.estimatedValue)}</div></div>
                    <div class="detail-field"><div class="label">Rating</div><div class="value">${stars}</div></div>
                    <div class="detail-field"><div class="label">Assigned To</div><div class="value">${c.assignedTo || '-'}</div></div>
                </div>
                ${c.notes ? '<div class="detail-field"><div class="label">Notes</div><div class="value">' + c.notes + '</div></div>' : ''}
            </div>
        </div>

        <div class="two-col">
            <div class="card">
                <div class="card-header"><h3>Deals (${deals.length})</h3></div>
                <div class="table-wrap"><table><thead><tr><th>Deal</th><th>Stage</th><th>Amount</th></tr></thead><tbody>
                    ${deals.length === 0 ? '<tr><td colspan="3" class="text-center text-muted">No deals</td></tr>' :
                    deals.map(d => `<tr><td>${d.name}</td><td><span class="${badgeClass(d.stage)}">${d.stage}</span></td><td>${fmt$(d.amount)}</td></tr>`).join('')}
                </tbody></table></div>
            </div>
            <div class="card">
                <div class="card-header"><h3>Tasks (${tasks.length})</h3></div>
                <div class="table-wrap"><table><thead><tr><th>Task</th><th>Due</th><th>Status</th></tr></thead><tbody>
                    ${tasks.length === 0 ? '<tr><td colspan="3" class="text-center text-muted">No tasks</td></tr>' :
                    tasks.map(t => `<tr><td>${t.description}</td><td>${fmtDate(t.dueDate)}</td><td><span class="${badgeClass(t.status)}">${t.status}</span></td></tr>`).join('')}
                </tbody></table></div>
            </div>
        </div>

        <div class="card">
            <div class="card-header"><h3>Interactions (${interactions.length})</h3></div>
            <div class="table-wrap"><table><thead><tr><th>Date</th><th>Type</th><th>Direction</th><th>Subject</th><th>Outcome</th></tr></thead><tbody>
                ${interactions.length === 0 ? '<tr><td colspan="5" class="text-center text-muted">No interactions</td></tr>' :
                interactions.sort((a,b) => (b.createdDate||'').localeCompare(a.createdDate||'')).map(i => `
                <tr><td>${fmtDate(i.createdDate)}</td><td>${i.type}</td><td>${i.direction}</td><td>${i.subject||'-'}</td><td>${i.outcome||'-'}</td></tr>`).join('')}
            </tbody></table></div>
        </div>
    `;
}

// ===== DEALS =====
function renderDeals() {
    const deals = DB.get('deals');
    const stages = ['Prospect','Quoted','Negotiation','Scheduled','Won','Lost'];

    const active = deals.filter(d => !['Won','Lost'].includes(d.stage));
    const pipelineVal = active.reduce((s,d) => s + (Number(d.amount)||0), 0);
    const wonVal = deals.filter(d => d.stage === 'Won').reduce((s,d) => s + (Number(d.amount)||0), 0);
    const wonCount = deals.filter(d => d.stage === 'Won').length;

    $('deal-stats').innerHTML = `
        <div class="stat-card accent"><div class="label">Total Deals</div><div class="value">${deals.length}</div></div>
        <div class="stat-card purple"><div class="label">Active</div><div class="value">${active.length}</div></div>
        <div class="stat-card yellow"><div class="label">Pipeline</div><div class="value money">${pipelineVal.toLocaleString()}</div></div>
        <div class="stat-card green"><div class="label">Won</div><div class="value">${wonCount} (${fmt$(wonVal)})</div></div>
    `;

    const tbody = $('deals-table').querySelector('tbody');
    if (deals.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="icon">\u{1F4B0}</div><p>No deals yet</p><button class="btn btn-primary" onclick="showPage('deal-form')">+ Add Deal</button></div></td></tr>`;
    } else {
        const sorted = [...deals].sort((a,b) => stages.indexOf(a.stage) - stages.indexOf(b.stage));
        tbody.innerHTML = sorted.map(d => `
            <tr>
                <td>${d.name}</td>
                <td>${getContactName(d.contactId)}</td>
                <td>${d.serviceType||'-'}</td>
                <td><span class="${badgeClass(d.stage)}">${d.stage}</span></td>
                <td>${fmt$(d.amount)}</td>
                <td>${d.probability ? d.probability + '%' : '-'}</td>
                <td>${fmtDate(d.closeDate)}</td>
                <td class="action-links">
                    <a onclick="showPage('deal-form',{id:${d.id}})">Edit</a>
                    <a class="text-red" onclick="deleteDeal(${d.id})">Del</a>
                </td>
            </tr>`).join('');
    }
}

function initDealForm(opts) {
    $('deal-form').reset();
    $('df-id').value = '';
    populateContactSelect('df-contact', opts?.contactId);

    if (opts && opts.id) {
        const d = DB.get('deals').find(x => x.id == opts.id);
        if (d) {
            $('page-title').textContent = 'Edit Deal';
            $('page-subtitle').textContent = d.name;
            $('df-id').value = d.id;
            $('df-name').value = d.name || '';
            populateContactSelect('df-contact', d.contactId);
            $('df-service').value = d.serviceType || '';
            $('df-stage').value = d.stage || 'Prospect';
            $('df-amount').value = d.amount || '';
            $('df-prob').value = d.probability || '';
            $('df-close').value = d.closeDate || '';
            $('df-recurring').value = d.recurring || '';
            $('df-notes').value = d.notes || '';
        }
    }
}

function saveDeal(e) {
    e.preventDefault();
    const deals = DB.get('deals');
    const id = $('df-id').value;

    const data = {
        name: $('df-name').value,
        contactId: $('df-contact').value ? parseInt($('df-contact').value) : null,
        serviceType: $('df-service').value,
        stage: $('df-stage').value,
        amount: $('df-amount').value ? parseFloat($('df-amount').value) : null,
        probability: $('df-prob').value ? parseInt($('df-prob').value) : null,
        closeDate: $('df-close').value || null,
        recurring: $('df-recurring').value || null,
        notes: $('df-notes').value,
        updatedDate: now()
    };

    if (id) {
        const idx = deals.findIndex(d => d.id == id);
        if (idx >= 0) deals[idx] = { ...deals[idx], ...data };
    } else {
        data.id = DB.nextId('deals');
        data.createdDate = now();
        deals.push(data);
    }

    DB.set('deals', deals);
    flash(id ? 'Deal updated!' : 'Deal created!', 'success');
    showPage('deals');
}

function deleteDeal(id) {
    if (!confirm('Delete this deal?')) return;
    DB.set('deals', DB.get('deals').filter(d => d.id != id));
    flash('Deal deleted.', 'success');
    renderDeals();
}

// ===== TASKS =====
function renderTasks() {
    let tasks = DB.get('tasks');
    const statusFilter = $('task-status-filter')?.value;
    if (statusFilter) tasks = tasks.filter(t => t.status === statusFilter);

    // Sort: pending/in-progress first, then by due date
    tasks.sort((a,b) => {
        const aComp = a.status === 'Completed' ? 1 : 0;
        const bComp = b.status === 'Completed' ? 1 : 0;
        if (aComp !== bComp) return aComp - bComp;
        return (a.dueDate||'9').localeCompare(b.dueDate||'9');
    });

    const tbody = $('tasks-table').querySelector('tbody');
    if (tasks.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="icon">\u2705</div><p>No tasks</p><button class="btn btn-primary" onclick="showPage('task-form')">+ Add Task</button></div></td></tr>`;
    } else {
        tbody.innerHTML = tasks.map(t => {
            const overdue = t.status !== 'Completed' && t.dueDate && t.dueDate < today();
            const statusBadge = overdue ? 'overdue' : t.status.toLowerCase().replace(/\s/g, '-');
            return `
            <tr${t.status === 'Completed' ? ' style="opacity:0.5"' : ''}>
                <td>${t.description}</td>
                <td>${t.taskType||'-'}</td>
                <td>${getContactName(t.contactId)}</td>
                <td>${fmtDate(t.dueDate)}</td>
                <td><span class="${badgeClass(t.priority)}">${t.priority||'Normal'}</span></td>
                <td><span class="${badgeClass(statusBadge)}">${overdue ? 'Overdue' : t.status}</span></td>
                <td class="action-links">
                    ${t.status !== 'Completed' ? `<a class="text-green" onclick="completeTask(${t.id})">Done</a>` : ''}
                    <a onclick="showPage('task-form',{id:${t.id}})">Edit</a>
                    <a class="text-red" onclick="deleteTask(${t.id})">Del</a>
                </td>
            </tr>`;
        }).join('');
    }
}

function initTaskForm(opts) {
    $('task-form').reset();
    $('tf-id').value = '';
    $('tf-assigned').value = 'Jason';
    populateContactSelect('tf-contact', opts?.contactId);
    populateDealSelect('tf-deal', opts?.dealId);

    if (opts && opts.id) {
        const t = DB.get('tasks').find(x => x.id == opts.id);
        if (t) {
            $('page-title').textContent = 'Edit Task';
            $('tf-id').value = t.id;
            $('tf-desc').value = t.description || '';
            $('tf-type').value = t.taskType || 'Follow Up';
            populateContactSelect('tf-contact', t.contactId);
            populateDealSelect('tf-deal', t.dealId);
            $('tf-due').value = t.dueDate || '';
            $('tf-priority').value = t.priority || 'Normal';
            $('tf-assigned').value = t.assignedTo || 'Jason';
        }
    }
}

function saveTask(e) {
    e.preventDefault();
    const tasks = DB.get('tasks');
    const id = $('tf-id').value;

    const data = {
        description: $('tf-desc').value,
        taskType: $('tf-type').value,
        contactId: $('tf-contact').value ? parseInt($('tf-contact').value) : null,
        dealId: $('tf-deal').value ? parseInt($('tf-deal').value) : null,
        dueDate: $('tf-due').value || null,
        priority: $('tf-priority').value,
        assignedTo: $('tf-assigned').value,
        status: 'Pending',
        updatedDate: now()
    };

    if (id) {
        const idx = tasks.findIndex(t => t.id == id);
        if (idx >= 0) { data.status = tasks[idx].status; tasks[idx] = { ...tasks[idx], ...data }; }
    } else {
        data.id = DB.nextId('tasks');
        data.createdDate = now();
        tasks.push(data);
    }

    DB.set('tasks', tasks);
    flash(id ? 'Task updated!' : 'Task created!', 'success');
    showPage('tasks');
}

function completeTask(id) {
    const tasks = DB.get('tasks');
    const idx = tasks.findIndex(t => t.id == id);
    if (idx >= 0) {
        tasks[idx].status = 'Completed';
        tasks[idx].completedDate = now();
        DB.set('tasks', tasks);
        flash('Task completed!', 'success');
        renderTasks();
        updateNavCounts();
    }
}

function deleteTask(id) {
    if (!confirm('Delete this task?')) return;
    DB.set('tasks', DB.get('tasks').filter(t => t.id != id));
    flash('Task deleted.', 'success');
    renderTasks();
    updateNavCounts();
}

// ===== INTERACTIONS =====
function renderInteractions() {
    const interactions = DB.get('interactions').sort((a,b) => (b.createdDate||'').localeCompare(a.createdDate||''));

    const tbody = $('interactions-table').querySelector('tbody');
    if (interactions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="icon">\u{1F4DE}</div><p>No interactions logged</p><button class="btn btn-primary" onclick="showPage('interaction-form')">+ Log Interaction</button></div></td></tr>`;
    } else {
        tbody.innerHTML = interactions.map(i => `
            <tr>
                <td>${fmtDate(i.createdDate)}</td>
                <td>${getContactName(i.contactId)}</td>
                <td>${i.type}</td>
                <td>${i.direction}</td>
                <td>${i.subject||'-'}</td>
                <td>${i.outcome||'-'}</td>
            </tr>`).join('');
    }
}

function initInteractionForm(opts) {
    $('interaction-form').reset();
    $('if-id').value = '';
    populateContactSelect('if-contact', opts?.contactId);
}

function saveInteraction(e) {
    e.preventDefault();
    const interactions = DB.get('interactions');

    const data = {
        id: DB.nextId('interactions'),
        contactId: $('if-contact').value ? parseInt($('if-contact').value) : null,
        type: $('if-type').value,
        direction: $('if-direction').value,
        subject: $('if-subject').value,
        notes: $('if-notes').value,
        outcome: $('if-outcome').value,
        followUpDate: $('if-followup').value || null,
        createdDate: now()
    };

    interactions.push(data);
    DB.set('interactions', interactions);
    flash('Interaction logged!', 'success');
    showPage('interactions');
}

// ===== CAMPAIGNS =====
function renderCampaigns() {
    const campaigns = DB.get('campaigns').sort((a,b) => (b.createdDate||'').localeCompare(a.createdDate||''));

    const tbody = $('campaigns-table').querySelector('tbody');
    if (campaigns.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="icon">\u{1F3AF}</div><p>No campaigns</p><button class="btn btn-primary" onclick="showPage('campaign-form')">+ Add Campaign</button></div></td></tr>`;
    } else {
        tbody.innerHTML = campaigns.map(c => `
            <tr>
                <td>${c.name}</td>
                <td>${c.campaignType||'-'}</td>
                <td>${c.targetArea||'-'}</td>
                <td>${fmt$(c.budget)}</td>
                <td>${c.leadsGenerated||0}</td>
                <td>${fmt$(c.revenueGenerated)}</td>
                <td><span class="${badgeClass(c.status)}">${c.status||'-'}</span></td>
                <td class="action-links">
                    <a onclick="showPage('campaign-form',{id:${c.id}})">Edit</a>
                    <a class="text-red" onclick="deleteCampaign(${c.id})">Del</a>
                </td>
            </tr>`).join('');
    }
}

function initCampaignForm(opts) {
    $('campaign-form').reset();
    $('cpf-id').value = '';
    $('cpf-leads').value = '0';
    $('cpf-deals').value = '0';
    $('cpf-revenue').value = '0';

    if (opts && opts.id) {
        const c = DB.get('campaigns').find(x => x.id == opts.id);
        if (c) {
            $('page-title').textContent = 'Edit Campaign';
            $('cpf-id').value = c.id;
            $('cpf-name').value = c.name || '';
            $('cpf-type').value = c.campaignType || '';
            $('cpf-area').value = c.targetArea || '';
            $('cpf-budget').value = c.budget || '';
            $('cpf-start').value = c.startDate || '';
            $('cpf-end').value = c.endDate || '';
            $('cpf-status').value = c.status || 'Planned';
            $('cpf-leads').value = c.leadsGenerated || 0;
            $('cpf-deals').value = c.dealsWon || 0;
            $('cpf-revenue').value = c.revenueGenerated || 0;
            $('cpf-notes').value = c.notes || '';
        }
    }
}

function saveCampaign(e) {
    e.preventDefault();
    const campaigns = DB.get('campaigns');
    const id = $('cpf-id').value;

    const data = {
        name: $('cpf-name').value,
        campaignType: $('cpf-type').value,
        targetArea: $('cpf-area').value,
        budget: $('cpf-budget').value ? parseFloat($('cpf-budget').value) : null,
        startDate: $('cpf-start').value || null,
        endDate: $('cpf-end').value || null,
        status: $('cpf-status').value,
        leadsGenerated: parseInt($('cpf-leads').value) || 0,
        dealsWon: parseInt($('cpf-deals').value) || 0,
        revenueGenerated: parseFloat($('cpf-revenue').value) || 0,
        notes: $('cpf-notes').value,
        updatedDate: now()
    };

    if (id) {
        const idx = campaigns.findIndex(c => c.id == id);
        if (idx >= 0) campaigns[idx] = { ...campaigns[idx], ...data };
    } else {
        data.id = DB.nextId('campaigns');
        data.createdDate = now();
        campaigns.push(data);
    }

    DB.set('campaigns', campaigns);
    flash(id ? 'Campaign updated!' : 'Campaign created!', 'success');
    showPage('campaigns');
}

function deleteCampaign(id) {
    if (!confirm('Delete this campaign?')) return;
    DB.set('campaigns', DB.get('campaigns').filter(c => c.id != id));
    flash('Campaign deleted.', 'success');
    renderCampaigns();
}

// ===== TERRITORIES =====
function renderTerritories() {
    const neighborhoods = DB.get('neighborhoods');
    const zipcodes = DB.get('zipcodes');

    const nBody = $('neighborhoods-table').querySelector('tbody');
    nBody.innerHTML = neighborhoods.map(n => `
        <tr>
            <td>${n.rank}</td>
            <td><strong>${n.name}</strong></td>
            <td>${n.zip}</td>
            <td>${n.medianHome ? fmt$(n.medianHome) : '-'}</td>
            <td class="text-secondary" style="font-size:13px;max-width:300px">${n.features||'-'}</td>
        </tr>`).join('');

    const zBody = $('zipcodes-table').querySelector('tbody');
    zBody.innerHTML = zipcodes.map(z => `
        <tr>
            <td>${z.rank}</td>
            <td><strong>${z.name}</strong></td>
            <td>${z.zip}</td>
            <td>${z.medianIncome ? fmt$(z.medianIncome) : '-'}</td>
            <td>${z.avgIncome ? fmt$(z.avgIncome) : '-'}</td>
            <td>${z.pctOver200k ? z.pctOver200k + '%' : '-'}</td>
            <td class="text-secondary" style="font-size:13px;max-width:300px">${z.features||'-'}</td>
        </tr>`).join('');
}

// ===== STORES =====
function renderStores() {
    const stores = DB.get('stores');
    const tbody = $('stores-table').querySelector('tbody');
    tbody.innerHTML = stores.map(s => `
        <tr>
            <td>${s.rank}</td>
            <td><strong>${s.name}</strong></td>
            <td>${s.category}</td>
            <td>${s.address}, ${s.city} ${s.zip}</td>
            <td>${s.neighborhood}</td>
        </tr>`).join('');
}

// ===== INIT =====
seedData();
showPage('dashboard');
