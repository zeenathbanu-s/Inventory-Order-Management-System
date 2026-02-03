const API_BASE_URL = 'http://localhost:8000/api';

// Global variables
let currentEditingProduct = null;
let products = [];
let orders = [];
let users = [];
let currentUser = null;
let salesChart = null;
let salesTrendChart = null;
let categoryChart = null;
let inventoryChart = null;
let topProductsChart = null;

// Check authentication and get user info
async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        // Show login form instead of redirecting
        showLoginForm();
        return false;
    }
    
    // Get current user info
    try {
        currentUser = await apiCall('/auth/me');
        if (currentUser) {
            document.getElementById('welcomeMessage').textContent = `Welcome, ${currentUser.username} (${currentUser.role})`;
            setupRoleBasedUI();
            hideLoginForm();
            return true;
        } else {
            localStorage.removeItem('access_token');
            showLoginForm();
            return false;
        }
    } catch (error) {
        localStorage.removeItem('access_token');
        showLoginForm();
        return false;
    }
}

// Show login form
function showLoginForm() {
    const loginHtml = `
        <div id="quickLogin" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9999; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; padding: 2rem; border-radius: 10px; text-align: center;">
                <h2>Quick Login</h2>
                <p>Please login to view the dashboard</p>
                <input type="text" id="quickUsername" placeholder="Username" value="admin" style="width: 200px; padding: 0.5rem; margin: 0.5rem; border: 1px solid #ddd; border-radius: 5px;">
                <br>
                <input type="password" id="quickPassword" placeholder="Password" value="admin123" style="width: 200px; padding: 0.5rem; margin: 0.5rem; border: 1px solid #ddd; border-radius: 5px;">
                <br>
                <button onclick="quickLogin()" style="background: #667eea; color: white; padding: 0.5rem 1rem; border: none; border-radius: 5px; cursor: pointer;">Login</button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loginHtml);
}

// Hide login form
function hideLoginForm() {
    const loginForm = document.getElementById('quickLogin');
    if (loginForm) {
        loginForm.remove();
    }
}

// Quick login function
async function quickLogin() {
    const username = document.getElementById('quickUsername').value;
    const password = document.getElementById('quickPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            hideLoginForm();
            location.reload(); // Reload to initialize properly
        } else {
            alert('Login failed. Please check your credentials.');
        }
    } catch (error) {
        alert('Login error: ' + error.message);
    }
}

// Setup UI based on user role
function setupRoleBasedUI() {
    const usersNavBtn = document.getElementById('usersNavBtn');
    
    // Show users section only for admin and manager
    if (currentUser.role === 'admin' || currentUser.role === 'manager') {
        usersNavBtn.style.display = 'block';
    }
    
    // Hide certain buttons based on permissions
    if (currentUser.role === 'staff') {
        // Staff can only view, not create/edit/delete
        const restrictedButtons = document.querySelectorAll('#addProductBtn, #addOrderBtn, #addUserBtn');
        restrictedButtons.forEach(btn => {
            if (btn) btn.style.display = 'none';
        });
    }
}

// API helper function
async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };

    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, finalOptions);
        
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            window.location.href = '/';
            return null;
        }

        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text);
            throw new Error('Server returned non-JSON response');
        }

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        
        // Show user-friendly error message
        if (error.message.includes('Failed to fetch')) {
            alert('Error: Cannot connect to server. Please check if the server is running.');
        } else if (error.message.includes('non-JSON response')) {
            alert('Error: Server returned an invalid response. Please check server logs.');
        } else {
            alert('Error: ' + error.message);
        }
        return null;
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Dashboard initializing...');
    
    if (!await checkAuth()) {
        console.log('Authentication failed, redirecting...');
        return;
    }

    console.log('Authentication successful, setting up dashboard...');

    // Set current date
    const currentDateElement = document.getElementById('currentDate');
    if (currentDateElement) {
        currentDateElement.textContent = new Date().toLocaleDateString();
    }
    
    // Update last updated time
    const updateLastUpdated = () => {
        const lastUpdatedElement = document.getElementById('lastUpdated');
        if (lastUpdatedElement) {
            lastUpdatedElement.textContent = new Date().toLocaleTimeString();
        }
    };
    updateLastUpdated();
    setInterval(updateLastUpdated, 60000);

    // Navigation
    const navButtons = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.dashboard-section');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetSection = btn.dataset.section;
            
            // Update active nav button
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update active section
            sections.forEach(s => s.classList.remove('active'));
            const targetSectionElement = document.getElementById(`${targetSection}-section`);
            if (targetSectionElement) {
                targetSectionElement.classList.add('active');
            }
            
            // Load data for the active section
            if (targetSection === 'dashboard') {
                loadDashboardStats();
            } else if (targetSection === 'products') {
                loadProducts();
            } else if (targetSection === 'orders') {
                loadOrders();
            } else if (targetSection === 'reports') {
                loadReports();
            } else if (targetSection === 'users') {
                loadUsers();
            }
        });
    });

    // Logout functionality
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        });
    }

    // Modal functionality
    setupModals();
    
    // Load initial dashboard data
    console.log('Loading initial dashboard data...');
    await loadDashboardStats();
    
    // Add refresh functionality
    const refreshBtn = document.createElement('button');
    refreshBtn.textContent = '🔄 Refresh';
    refreshBtn.className = 'secondary-btn';
    refreshBtn.style.marginLeft = '1rem';
    refreshBtn.onclick = loadDashboardStats;
    
    const dashboardHeader = document.querySelector('#dashboard-section .section-header');
    if (dashboardHeader) {
        dashboardHeader.appendChild(refreshBtn);
    }
});

// Setup modal functionality
function setupModals() {
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close');

    // Close modal when clicking X
    closeButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.modal').style.display = 'none';
        });
    });

    // Close modal when clicking outside
    modals.forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Product modal
    const addProductBtn = document.getElementById('addProductBtn');
    if (addProductBtn) {
        addProductBtn.addEventListener('click', () => {
            currentEditingProduct = null;
            document.getElementById('productModalTitle').textContent = 'Add Product';
            document.getElementById('productForm').reset();
            document.getElementById('imagePreview').innerHTML = '';
            document.getElementById('productModal').style.display = 'block';
        });
    }

    const cancelProductBtn = document.getElementById('cancelProductBtn');
    if (cancelProductBtn) {
        cancelProductBtn.addEventListener('click', () => {
            document.getElementById('productModal').style.display = 'none';
        });
    }

    const productForm = document.getElementById('productForm');
    if (productForm) {
        productForm.addEventListener('submit', handleProductSubmit);
    }

    // Image preview
    const productImage = document.getElementById('productImage');
    if (productImage) {
        productImage.addEventListener('change', handleImagePreview);
    }

    // Order modal
    const addOrderBtn = document.getElementById('addOrderBtn');
    if (addOrderBtn) {
        addOrderBtn.addEventListener('click', () => {
            loadProductsForOrder();
            document.getElementById('orderForm').reset();
            resetOrderItems();
            document.getElementById('orderModal').style.display = 'block';
        });
    }

    const cancelOrderBtn = document.getElementById('cancelOrderBtn');
    if (cancelOrderBtn) {
        cancelOrderBtn.addEventListener('click', () => {
            document.getElementById('orderModal').style.display = 'none';
        });
    }

    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', handleOrderSubmit);
    }

    const addItemBtn = document.getElementById('addItemBtn');
    if (addItemBtn) {
        addItemBtn.addEventListener('click', addOrderItem);
    }

    // User modal
    const addUserBtn = document.getElementById('addUserBtn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', () => {
            document.getElementById('userForm').reset();
            document.getElementById('userModal').style.display = 'block';
        });
    }

    const cancelUserBtn = document.getElementById('cancelUserBtn');
    if (cancelUserBtn) {
        cancelUserBtn.addEventListener('click', () => {
            document.getElementById('userModal').style.display = 'none';
        });
    }

    const userForm = document.getElementById('userForm');
    if (userForm) {
        userForm.addEventListener('submit', handleUserSubmit);
    }

    // Reports controls
    const refreshReports = document.getElementById('refreshReports');
    if (refreshReports) {
        refreshReports.addEventListener('click', loadReports);
    }
}

// Dashboard functionality
async function loadDashboardStats() {
    try {
        console.log('Loading dashboard stats...');
        const stats = await apiCall('/reports/dashboard-stats');
        console.log('Dashboard stats received:', stats);
        
        if (stats) {
            // Update KPI cards
            document.getElementById('totalProducts').textContent = stats.total_products || 0;
            document.getElementById('totalOrders').textContent = stats.total_orders || 0;
            document.getElementById('pendingOrders').textContent = stats.pending_orders || 0;
            document.getElementById('lowStockCount').textContent = stats.low_stock_alerts ? stats.low_stock_alerts.length : 0;

            // Update badges
            const recentOrdersBadge = document.getElementById('recentOrdersBadge');
            const lowStockBadge = document.getElementById('lowStockBadge');
            
            if (recentOrdersBadge) {
                recentOrdersBadge.textContent = stats.recent_orders ? stats.recent_orders.length : 0;
            }
            if (lowStockBadge) {
                lowStockBadge.textContent = stats.low_stock_alerts ? stats.low_stock_alerts.length : 0;
            }

            // Recent orders
            const recentOrdersList = document.getElementById('recentOrdersList');
            if (recentOrdersList) {
                recentOrdersList.innerHTML = '';
                if (stats.recent_orders && stats.recent_orders.length > 0) {
                    stats.recent_orders.forEach(order => {
                        const orderItem = document.createElement('div');
                        orderItem.className = 'widget-item';
                        orderItem.innerHTML = `
                            <div class="widget-item-info">
                                <div class="widget-item-title">${order.order_number}</div>
                                <div class="widget-item-subtitle">${order.customer_name} • ${new Date(order.created_at).toLocaleDateString()}</div>
                            </div>
                            <div class="widget-item-value">$${order.total_amount.toFixed(2)}</div>
                        `;
                        recentOrdersList.appendChild(orderItem);
                    });
                } else {
                    recentOrdersList.innerHTML = '<div class="widget-item">No recent orders</div>';
                }
            }

            // Low stock alerts
            const lowStockList = document.getElementById('lowStockList');
            if (lowStockList) {
                lowStockList.innerHTML = '';
                if (stats.low_stock_alerts && stats.low_stock_alerts.length > 0) {
                    stats.low_stock_alerts.forEach(product => {
                        const alertItem = document.createElement('div');
                        alertItem.className = 'widget-item alert-item';
                        alertItem.innerHTML = `
                            <div class="widget-item-info">
                                <div class="widget-item-title">${product.name}</div>
                                <div class="widget-item-subtitle">SKU: ${product.sku} • Threshold: ${product.low_stock_threshold || 10}</div>
                            </div>
                            <div class="widget-item-value">${product.stock_quantity} left</div>
                        `;
                        lowStockList.appendChild(alertItem);
                    });
                } else {
                    lowStockList.innerHTML = '<div class="widget-item">All products in stock</div>';
                }
            }

            // Load sales chart for dashboard
            loadDashboardSalesChart();
            
            // Load top products
            loadTopProducts();
        } else {
            console.error('No stats data received');
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Load dashboard sales chart
async function loadDashboardSalesChart() {
    const salesData = await apiCall('/reports/sales?days=30');
    if (salesData && salesData.sales_by_month) {
        const ctx = document.getElementById('salesChart').getContext('2d');
        
        if (salesChart) {
            salesChart.destroy();
        }
        
        salesChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: salesData.sales_by_month.map(item => item.month),
                datasets: [{
                    label: 'Sales ($)',
                    data: salesData.sales_by_month.map(item => item.sales),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

// Load top products for dashboard
async function loadTopProducts() {
    const salesData = await apiCall('/reports/sales?days=30');
    if (salesData && salesData.top_products) {
        const topProductsList = document.getElementById('topProductsList');
        topProductsList.innerHTML = '';
        
        salesData.top_products.slice(0, 5).forEach((product, index) => {
            const productItem = document.createElement('div');
            productItem.className = 'widget-item';
            productItem.innerHTML = `
                <div class="widget-item-info">
                    <div class="widget-item-title">#${index + 1} ${product.name}</div>
                    <div class="widget-item-subtitle">Revenue generated</div>
                </div>
                <div class="widget-item-value">$${product.sales.toFixed(2)}</div>
            `;
            topProductsList.appendChild(productItem);
        });
    }
}

// Products functionality
async function loadProducts() {
    const data = await apiCall('/products');
    if (data) {
        products = data;
        renderProductsTable();
    }
}

function renderProductsTable() {
    const tbody = document.querySelector('#productsTable tbody');
    tbody.innerHTML = '';

    products.forEach(product => {
        const row = document.createElement('tr');
        const stockWarning = product.stock_quantity <= product.low_stock_threshold;
        const outOfStock = product.stock_quantity === 0;
        
        let stockDisplay = product.stock_quantity;
        if (outOfStock) {
            stockDisplay = `<span class="out-of-stock-warning">Out of Stock</span>`;
        } else if (stockWarning) {
            stockDisplay = `<span class="low-stock-warning">${product.stock_quantity}</span>`;
        }

        const imageDisplay = product.image_url ? 
            `<img src="${product.image_url}" alt="${product.name}" class="product-image">` : 
            'No image';

        const canEdit = currentUser.role === 'admin' || currentUser.role === 'manager';
        const actions = canEdit ? `
            <button class="action-btn edit-btn" onclick="editProduct('${product.id}')">Edit</button>
            <button class="action-btn delete-btn" onclick="deleteProduct('${product.id}')">Delete</button>
        ` : 'View only';

        row.innerHTML = `
            <td>${product.sku}</td>
            <td>${product.name}</td>
            <td>${product.category || 'N/A'}</td>
            <td>$${product.price.toFixed(2)}</td>
            <td>${stockDisplay}</td>
            <td>${product.low_stock_threshold}</td>
            <td>${imageDisplay}</td>
            <td>${actions}</td>
        `;
        tbody.appendChild(row);
    });
}

function handleImagePreview(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('imagePreview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px; border-radius: 5px;">`;
        };
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '';
    }
}

async function handleProductSubmit(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('productName').value,
        sku: document.getElementById('productSku').value,
        description: document.getElementById('productDescription').value,
        category: document.getElementById('productCategory').value,
        price: parseFloat(document.getElementById('productPrice').value),
        stock_quantity: parseInt(document.getElementById('productStock').value),
        low_stock_threshold: parseInt(document.getElementById('productThreshold').value) || 10
    };

    // Handle image upload (simplified - in production, you'd upload to a file server)
    const imageFile = document.getElementById('productImage').files[0];
    if (imageFile) {
        // For demo purposes, we'll use a placeholder URL
        formData.image_url = `/static/images/${imageFile.name}`;
    }

    let result;
    if (currentEditingProduct) {
        // Update existing product
        const updateData = { ...formData };
        delete updateData.sku; // SKU cannot be updated
        result = await apiCall(`/products/${currentEditingProduct}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    } else {
        // Create new product
        result = await apiCall('/products', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    }

    if (result) {
        document.getElementById('productModal').style.display = 'none';
        loadProducts();
    }
}

function editProduct(productId) {
    const product = products.find(p => p.id === productId);
    if (product) {
        currentEditingProduct = productId;
        document.getElementById('productModalTitle').textContent = 'Edit Product';
        document.getElementById('productName').value = product.name;
        document.getElementById('productSku').value = product.sku;
        document.getElementById('productSku').disabled = true;
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productCategory').value = product.category || '';
        document.getElementById('productPrice').value = product.price;
        document.getElementById('productStock').value = product.stock_quantity;
        document.getElementById('productThreshold').value = product.low_stock_threshold || 10;
        
        // Show current image if exists
        const preview = document.getElementById('imagePreview');
        if (product.image_url) {
            preview.innerHTML = `<img src="${product.image_url}" alt="Current image" style="max-width: 200px; max-height: 200px; border-radius: 5px;">`;
        }
        
        document.getElementById('productModal').style.display = 'block';
    }
}

async function deleteProduct(productId) {
    if (confirm('Are you sure you want to delete this product?')) {
        const result = await apiCall(`/products/${productId}`, {
            method: 'DELETE'
        });
        if (result) {
            loadProducts();
        }
    }
}

// Orders functionality
async function loadOrders() {
    const data = await apiCall('/orders');
    if (data) {
        orders = data;
        renderOrdersTable();
    }
}

function renderOrdersTable() {
    const tbody = document.querySelector('#ordersTable tbody');
    tbody.innerHTML = '';

    orders.forEach(order => {
        const row = document.createElement('tr');
        const date = new Date(order.created_at).toLocaleDateString();
        
        const canManage = currentUser.role === 'admin' || currentUser.role === 'manager';
        const actions = canManage ? `
            <button class="action-btn status-btn" onclick="updateOrderStatus('${order.id}')">Update Status</button>
            <button class="action-btn delete-btn" onclick="deleteOrder('${order.id}')">Delete</button>
        ` : 'View only';
        
        row.innerHTML = `
            <td>${order.order_number}</td>
            <td>${order.customer_name}</td>
            <td>${order.customer_email}</td>
            <td>$${order.total_amount.toFixed(2)}</td>
            <td><span class="status-badge status-${order.status}">${order.status}</span></td>
            <td>${date}</td>
            <td>${actions}</td>
        `;
        tbody.appendChild(row);
    });
}

async function loadProductsForOrder() {
    if (products.length === 0) {
        await loadProducts();
    }
    updateProductSelects();
}

function updateProductSelects() {
    const selects = document.querySelectorAll('.product-select');
    selects.forEach(select => {
        select.innerHTML = '<option value="">Select Product</option>';
        products.forEach(product => {
            if (product.stock_quantity > 0) {
                select.innerHTML += `<option value="${product.id}">${product.name} (Stock: ${product.stock_quantity})</option>`;
            }
        });
    });
}

function resetOrderItems() {
    const orderItems = document.getElementById('orderItems');
    orderItems.innerHTML = `
        <div class="order-item">
            <select class="product-select" required>
                <option value="">Select Product</option>
            </select>
            <input type="number" class="quantity-input" placeholder="Quantity" min="1" required>
            <button type="button" class="remove-item-btn" onclick="removeOrderItem(this)">Remove</button>
        </div>
    `;
    updateProductSelects();
}

function addOrderItem() {
    const orderItems = document.getElementById('orderItems');
    const newItem = document.createElement('div');
    newItem.className = 'order-item';
    newItem.innerHTML = `
        <select class="product-select" required>
            <option value="">Select Product</option>
        </select>
        <input type="number" class="quantity-input" placeholder="Quantity" min="1" required>
        <button type="button" class="remove-item-btn" onclick="removeOrderItem(this)">Remove</button>
    `;
    orderItems.appendChild(newItem);
    
    const newSelect = newItem.querySelector('.product-select');
    products.forEach(product => {
        if (product.stock_quantity > 0) {
            newSelect.innerHTML += `<option value="${product.id}">${product.name} (Stock: ${product.stock_quantity})</option>`;
        }
    });
}

function removeOrderItem(button) {
    const orderItems = document.getElementById('orderItems');
    if (orderItems.children.length > 1) {
        button.parentElement.remove();
    } else {
        alert('At least one item is required');
    }
}

async function handleOrderSubmit(e) {
    e.preventDefault();
    
    const customerName = document.getElementById('customerName').value;
    const customerEmail = document.getElementById('customerEmail').value;
    
    const items = [];
    const orderItems = document.querySelectorAll('.order-item');
    
    for (const item of orderItems) {
        const productId = item.querySelector('.product-select').value;
        const quantity = parseInt(item.querySelector('.quantity-input').value);
        
        if (productId && quantity) {
            items.push({ product_id: productId, quantity });
        }
    }
    
    if (items.length === 0) {
        alert('Please add at least one item to the order');
        return;
    }
    
    const orderData = {
        customer_name: customerName,
        customer_email: customerEmail,
        items
    };
    
    const result = await apiCall('/orders', {
        method: 'POST',
        body: JSON.stringify(orderData)
    });
    
    if (result) {
        document.getElementById('orderModal').style.display = 'none';
        loadOrders();
        loadProducts();
        loadDashboardStats();
    }
}

async function updateOrderStatus(orderId) {
    const order = orders.find(o => o.id === orderId);
    if (!order) return;
    
    const statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'];
    const currentIndex = statuses.indexOf(order.status);
    const nextStatus = statuses[(currentIndex + 1) % statuses.length];
    
    const newStatus = prompt(`Current status: ${order.status}\nEnter new status (${statuses.join(', ')}):`, nextStatus);
    
    if (newStatus && statuses.includes(newStatus.toLowerCase())) {
        const result = await apiCall(`/orders/${orderId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status: newStatus.toLowerCase() })
        });
        
        if (result) {
            loadOrders();
        }
    } else if (newStatus) {
        alert('Invalid status. Please use one of: ' + statuses.join(', '));
    }
}

async function deleteOrder(orderId) {
    if (confirm('Are you sure you want to delete this order? This will restore the stock quantities.')) {
        const result = await apiCall(`/orders/${orderId}`, {
            method: 'DELETE'
        });
        if (result) {
            loadOrders();
            loadProducts();
            loadDashboardStats();
        }
    }
}

// Reports functionality
async function loadReports() {
    const period = document.getElementById('reportPeriod').value;
    
    // Load sales analytics
    const salesData = await apiCall(`/reports/sales?days=${period}`);
    if (salesData) {
        document.getElementById('totalRevenue').textContent = `$${salesData.total_sales.toFixed(2)}`;
        document.getElementById('totalOrdersReport').textContent = salesData.total_orders;
        
        // Calculate average order value
        const avgOrderValue = salesData.total_orders > 0 ? salesData.total_sales / salesData.total_orders : 0;
        document.getElementById('avgOrderValue').textContent = `$${avgOrderValue.toFixed(2)}`;
        
        // Load charts
        loadSalesTrendChart(salesData);
        loadTopProductsChart(salesData.top_products);
    }
    
    // Load inventory analytics
    const inventoryData = await apiCall('/reports/inventory');
    if (inventoryData) {
        document.getElementById('totalProductsReport').textContent = inventoryData.total_products;
        document.getElementById('inventoryValue').textContent = `$${inventoryData.total_inventory_value.toFixed(2)}`;
        document.getElementById('lowStockItems').textContent = inventoryData.low_stock_products.length;
        
        // Load inventory charts
        loadInventoryChart(inventoryData);
        loadCategoryChart();
        
        // Load top products table
        loadTopProductsTable(inventoryData);
    }
}

// Load sales trend chart
function loadSalesTrendChart(salesData) {
    const ctx = document.getElementById('salesTrendChart').getContext('2d');
    
    if (salesTrendChart) {
        salesTrendChart.destroy();
    }
    
    // Generate sample daily data (in real app, this would come from API)
    const days = [];
    const salesValues = [];
    const orderCounts = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        days.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        salesValues.push(Math.random() * 5000 + 1000);
        orderCounts.push(Math.floor(Math.random() * 20) + 5);
    }
    
    salesTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: days,
            datasets: [{
                label: 'Daily Sales ($)',
                data: salesValues,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true,
                yAxisID: 'y'
            }, {
                label: 'Orders Count',
                data: orderCounts,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4,
                fill: false,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            aspectRatio: 2,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

// Load category distribution chart
async function loadCategoryChart() {
    const products = await apiCall('/products');
    if (products) {
        const categoryData = {};
        products.forEach(product => {
            const category = product.category || 'Uncategorized';
            if (categoryData[category]) {
                categoryData[category] += product.price * product.stock_quantity;
            } else {
                categoryData[category] = product.price * product.stock_quantity;
            }
        });
        
        const ctx = document.getElementById('categoryChart').getContext('2d');
        
        if (categoryChart) {
            categoryChart.destroy();
        }
        
        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(categoryData),
                datasets: [{
                    data: Object.values(categoryData),
                    backgroundColor: [
                        '#667eea',
                        '#28a745',
                        '#ffc107',
                        '#dc3545',
                        '#17a2b8',
                        '#6f42c1',
                        '#fd7e14'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': $' + context.parsed.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

// Load inventory status chart
function loadInventoryChart(inventoryData) {
    const ctx = document.getElementById('inventoryChart').getContext('2d');
    
    if (inventoryChart) {
        inventoryChart.destroy();
    }
    
    const inStock = inventoryData.total_products - inventoryData.low_stock_products.length - inventoryData.out_of_stock_products.length;
    
    inventoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['In Stock', 'Low Stock', 'Out of Stock'],
            datasets: [{
                label: 'Products Count',
                data: [inStock, inventoryData.low_stock_products.length, inventoryData.out_of_stock_products.length],
                backgroundColor: ['#28a745', '#ffc107', '#dc3545']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Load top products chart
function loadTopProductsChart(topProducts) {
    const ctx = document.getElementById('topProductsChart').getContext('2d');
    
    if (topProductsChart) {
        topProductsChart.destroy();
    }
    
    const top5 = topProducts.slice(0, 5);
    
    topProductsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top5.map(p => p.name),
            datasets: [{
                label: 'Revenue ($)',
                data: top5.map(p => p.sales),
                backgroundColor: '#667eea'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Load top products table
function loadTopProductsTable(inventoryData) {
    // This would typically combine sales data with inventory data
    // For now, we'll show a sample table
    const tableBody = document.getElementById('topProductsTable');
    tableBody.innerHTML = '';
    
    // Sample data - in real app, this would come from API
    const sampleProducts = [
        { name: 'iPhone 14', revenue: 60000, units: 10, avgPrice: 6000, stock: 24, performance: 'Excellent' },
        { name: 'Samsung Galaxy', revenue: 45000, units: 15, avgPrice: 3000, stock: 18, performance: 'Good' },
        { name: 'MacBook Pro', revenue: 80000, units: 8, avgPrice: 10000, stock: 5, performance: 'Excellent' },
        { name: 'iPad Air', revenue: 25000, units: 12, avgPrice: 2083, stock: 15, performance: 'Good' },
        { name: 'AirPods Pro', revenue: 15000, units: 25, avgPrice: 600, stock: 30, performance: 'Average' }
    ];
    
    sampleProducts.forEach(product => {
        const row = document.createElement('tr');
        const performanceClass = product.performance.toLowerCase();
        row.innerHTML = `
            <td>${product.name}</td>
            <td>$${product.revenue.toLocaleString()}</td>
            <td>${product.units}</td>
            <td>$${product.avgPrice.toLocaleString()}</td>
            <td>${product.stock}</td>
            <td><span class="performance-badge ${performanceClass}">${product.performance}</span></td>
        `;
        tableBody.appendChild(row);
    });
}

// Users functionality
async function loadUsers() {
    if (currentUser.role !== 'admin' && currentUser.role !== 'manager') {
        return;
    }
    
    const data = await apiCall('/users');
    if (data) {
        users = data;
        renderUsersTable();
    }
}

function renderUsersTable() {
    const tbody = document.querySelector('#usersTable tbody');
    tbody.innerHTML = '';

    users.forEach(user => {
        const row = document.createElement('tr');
        const date = new Date(user.created_at).toLocaleDateString();
        
        const canManage = currentUser.role === 'admin';
        const actions = canManage ? `
            <button class="action-btn edit-btn" onclick="changeUserRole('${user._id}', '${user.role}')">Change Role</button>
        ` : 'View only';
        
        row.innerHTML = `
            <td>${user.username}</td>
            <td><span class="role-badge role-${user.role}">${user.role}</span></td>
            <td><span class="status-${user.is_active ? 'active' : 'inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>${date}</td>
            <td>${actions}</td>
        `;
        tbody.appendChild(row);
    });
}

async function handleUserSubmit(e) {
    e.preventDefault();
    
    const userData = {
        username: document.getElementById('username').value,
        password: document.getElementById('userPassword').value,
        role: document.getElementById('userRole').value
    };
    
    const result = await apiCall('/users', {
        method: 'POST',
        body: JSON.stringify(userData)
    });
    
    if (result) {
        document.getElementById('userModal').style.display = 'none';
        loadUsers();
    }
}

async function changeUserRole(userId, currentRole) {
    const roles = ['staff', 'manager', 'admin'];
    const newRole = prompt(`Current role: ${currentRole}\nEnter new role (${roles.join(', ')}):`, currentRole);
    
    if (newRole && roles.includes(newRole.toLowerCase())) {
        const result = await apiCall(`/users/${userId}/role?role=${newRole.toLowerCase()}`, {
            method: 'PUT'
        });
        
        if (result) {
            loadUsers();
        }
    } else if (newRole) {
        alert('Invalid role. Please use one of: ' + roles.join(', '));
    }
}