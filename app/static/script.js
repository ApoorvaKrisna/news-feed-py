// Enhanced JavaScript for Developer-Focused UI

// API Base URL
const API_BASE = '/api/v1';

// Global state
let currentResults = [];
let systemStatus = 'unknown';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    loadSources();
    checkSystemHealth();
    setupEventListeners();
    updateSystemInfo();
});

// Setup event listeners
function setupEventListeners() {
    // Enter key support for search inputs
    document.getElementById('intelligent-query').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') executeIntelligentQuery();
    });

    document.getElementById('search-query').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') searchByText();
    });
}

// Enhanced utility functions
function showLoading() {
    document.getElementById('loading-overlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('show');
}

function showAlert(message, type = 'error') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'}"></i> ${message}`;

    const container = document.querySelector('.results-container');
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function clearResults() {
    document.getElementById('results-container').innerHTML = `
        <div class="welcome-message">
            <i class="fas fa-rocket"></i>
            <h4>Welcome to the Contextual News API!</h4>
            <p><strong>For Developers:</strong> This is a production-ready news retrieval system with AI integration.</p>
            <ul class="feature-list">
                <li>🧠 <strong>AI-Powered:</strong> Uses OpenAI GPT for intelligent query processing</li>
                <li>🗄️ <strong>MongoDB Atlas:</strong> 2000+ articles with optimized indexes</li>
                <li>🚀 <strong>FastAPI:</strong> High-performance async API with auto-documentation</li>
                <li>📍 <strong>Geospatial:</strong> Location-based search with distance calculations</li>
                <li>📈 <strong>Analytics:</strong> Trending system with user interaction simulation</li>
            </ul>
            <p><strong>Start by trying the AI-powered query above or use the traditional endpoints below.</strong></p>
        </div>
    `;
    currentResults = [];
}

// Enhanced API call wrapper with performance tracking
async function apiCall(endpoint, options = {}) {
    const startTime = performance.now();
    try {
        showLoading();
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        // Log performance for developers
        console.log(`API Call: ${endpoint} - ${duration}ms`);

        if (!response.ok) {
            throw new Error(data.detail?.message || data.detail || 'API call failed');
        }

        // Add performance info to response if query_info exists
        if (data.query_info) {
            data.query_info.client_duration_ms = duration;
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        showAlert(`Error: ${error.message}`);
        throw error;
    } finally {
        hideLoading();
    }
}

// System info updates
async function updateSystemInfo() {
    try {
        const categories = await apiCall('/news/categories');
        const sources = await apiCall('/news/sources');

        document.getElementById('category-count').textContent = categories.length;
        document.getElementById('source-count').textContent = sources.length;
    } catch (error) {
        console.warn('Could not update system info:', error);
    }
}

// Enhanced query examples
function setQuery(query) {
    document.getElementById('intelligent-query').value = query;
    // Optional: auto-execute for demo purposes
    // executeIntelligentQuery();
}

// Load sample coordinates
function loadSampleCoordinates() {
    // Mumbai coordinates
    document.getElementById('nearby-lat').value = '19.0760';
    document.getElementById('nearby-lon').value = '72.8777';
    document.getElementById('trending-lat').value = '19.0760';
    document.getElementById('trending-lon').value = '72.8777';
    document.getElementById('query-lat').value = '19.0760';
    document.getElementById('query-lon').value = '72.8777';

    showAlert('Mumbai coordinates loaded in all location fields!', 'success');
}

// Export results functionality
function exportResults() {
    if (currentResults.length === 0) {
        showAlert('No results to export');
        return;
    }

    const dataStr = JSON.stringify(currentResults, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `news_results_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showAlert('Results exported successfully!', 'success');
}

// Enhanced display functions with performance info
function displayNewsResults(result, title) {
    currentResults = result.articles || [];
    const container = document.getElementById('results-container');

    if (currentResults.length === 0) {
        container.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-search"></i>
                <p>No articles found for your search.</p>
                <p>Try adjusting your search criteria or using different keywords.</p>
            </div>
        `;
        return;
    }

    let html = `<div class="results-info">
        <h4><i class="fas fa-newspaper"></i> ${title}</h4>
        <p>Found ${result.total_count || currentResults.length} articles (showing ${currentResults.length})</p>
    </div>`;

    // Add performance information if available
    if (result.query_info && result.query_info.processing_time_ms) {
        const serverTime = Math.round(result.query_info.processing_time_ms);
        const clientTime = result.query_info.client_duration_ms || 0;

        html += `<div class="performance-info">
            <h4><i class="fas fa-tachometer-alt"></i> Performance Metrics</h4>
            <div class="performance-metrics">
                <div class="metric">
                    <span class="metric-value">${serverTime}ms</span>
                    <span class="metric-label">Server Processing</span>
                </div>
                <div class="metric">
                    <span class="metric-value">${clientTime}ms</span>
                    <span class="metric-label">Network + Client</span>
                </div>
                <div class="metric">
                    <span class="metric-value">${result.query_info.intent || 'N/A'}</span>
                    <span class="metric-label">AI Intent</span>
                </div>
                <div class="metric">
                    <span class="metric-value">${currentResults.length}</span>
                    <span class="metric-label">Results</span>
                </div>
            </div>
        </div>`;
    }

    html += currentResults.map(article => createArticleCard(article)).join('');
    container.innerHTML = html;
}

// Enhanced article card with more developer info
function createArticleCard(article) {
    const pubDate = new Date(article.publication_date);
    const formattedDate = pubDate.toLocaleDateString() + ' ' + pubDate.toLocaleTimeString();

    return `
        <div class="article-card">
            <div class="article-header">
                <div>
                    <div class="article-title">${escapeHtml(article.title)}</div>
                    <div class="article-meta">
                        <span><i class="fas fa-calendar"></i> ${formattedDate}</span>
                        <span><i class="fas fa-globe"></i> ${escapeHtml(article.source_name)}</span>
                        <span class="score-badge">Score: ${article.relevance_score.toFixed(2)}</span>
                        ${article.distance_km ? `<span><i class="fas fa-map-marker-alt"></i> ${article.distance_km.toFixed(1)} km</span>` : ''}
                        <span class="endpoint-badge small">ID: ${article.id.substring(0, 8)}...</span>
                    </div>
                </div>
            </div>

            <div class="article-description">
                ${escapeHtml(article.description)}
            </div>

            ${article.llm_summary ? `
                <div class="article-summary">
                    <strong><i class="fas fa-robot"></i> AI Summary:</strong><br>
                    ${escapeHtml(article.llm_summary)}
                </div>
            ` : ''}

            <div class="article-tags">
                ${article.category.map(cat => `<span class="tag">${escapeHtml(cat)}</span>`).join('')}
                <div style="margin-left: auto; display: flex; gap: 0.5rem;">
                    <button onclick="copyArticleId('${article.id}')" class="btn btn-outline btn-small">
                        <i class="fas fa-copy"></i> Copy ID
                    </button>
                    <a href="${article.url}" target="_blank" class="btn btn-outline btn-small">
                        <i class="fas fa-external-link-alt"></i> Read More
                    </a>
                </div>
            </div>
        </div>
    `;
}

// Copy article ID to clipboard
function copyArticleId(articleId) {
    navigator.clipboard.writeText(articleId).then(() => {
        showAlert('Article ID copied to clipboard!', 'success');
    }).catch(() => {
        showAlert('Failed to copy article ID');
    });
}

// Enhanced health check with more details
async function checkSystemHealth() {
    try {
        const health = await fetch('/health');
        const healthData = await health.json();

        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');

        if (health.ok && healthData.database === 'connected') {
            statusIndicator.className = 'status-indicator healthy';
            statusText.innerHTML = `
                <i class="fas fa-check-circle"></i>
                System Online - DB Connected
            `;
            systemStatus = 'healthy';
        } else {
            statusIndicator.className = 'status-indicator unhealthy';
            statusText.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                System Issues Detected
            `;
            systemStatus = 'unhealthy';
        }
    } catch (error) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        statusIndicator.className = 'status-indicator unhealthy';
        statusText.innerHTML = `
            <i class="fas fa-times-circle"></i>
            Connection Failed
        `;
        systemStatus = 'error';
    }
}

// Keep all the existing search functions (executeIntelligentQuery, searchByCategory, etc.)
// but enhance them with the new features above

// All the existing functions remain the same:
// - executeIntelligentQuery()
// - searchByCategory()
// - searchByText()
// - searchBySource()
// - searchByScore()
// - searchNearby()
// - getTrending()
// - getRandomArticles()
// - simulateInteractions()
// - getActivityStats()
// - loadCategories()
// - loadSources()
// - displayTrendingResults()
// - displayRandomResults()
// - displayStats()
// - createTrendingCard()
// - escapeHtml()

// Add the rest of your existing functions here...

// Utility functions
function showLoading() {
    document.getElementById('loading-overlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('show');
}

function showAlert(message, type = 'error') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'}"></i> ${message}`;

    const container = document.querySelector('.results-container');
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function clearResults() {
    document.getElementById('results-container').innerHTML = `
        <div class="welcome-message">
            <i class="fas fa-info-circle"></i>
            <p>Welcome! Try any of the search methods above to see results here.</p>
            <p>The intelligent query uses AI to automatically choose the best search strategy.</p>
        </div>
    `;
    currentResults = [];
}

// API call wrapper
async function apiCall(endpoint, options = {}) {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail?.message || data.detail || 'API call failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        showAlert(`Error: ${error.message}`);
        throw error;
    } finally {
        hideLoading();
    }
}

// Check system health
async function checkSystemHealth() {
    try {
        const health = await fetch('/health');
        const healthData = await health.json();

        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');

        if (health.ok && healthData.database === 'connected') {
            statusIndicator.className = 'status-indicator healthy';
            statusText.textContent = 'System Online';
            systemStatus = 'healthy';
        } else {
            statusIndicator.className = 'status-indicator unhealthy';
            statusText.textContent = 'System Issues Detected';
            systemStatus = 'unhealthy';
        }
    } catch (error) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        statusIndicator.className = 'status-indicator unhealthy';
        statusText.textContent = 'Connection Failed';
        systemStatus = 'error';
    }
}

// Load categories and sources
async function loadCategories() {
    try {
        const categories = await apiCall('/news/categories');
        const select = document.getElementById('category-select');
        select.innerHTML = '<option value="">Select a category...</option>';

        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            select.appendChild(option);
        });
    } catch (error) {
        document.getElementById('category-select').innerHTML = '<option value="">Failed to load categories</option>';
    }
}

async function loadSources() {
    try {
        const sources = await apiCall('/news/sources');
        const select = document.getElementById('source-select');
        select.innerHTML = '<option value="">Select a source...</option>';

        sources.forEach(source => {
            const option = document.createElement('option');
            option.value = source;
            option.textContent = source;
            select.appendChild(option);
        });
    } catch (error) {
        document.getElementById('source-select').innerHTML = '<option value="">Failed to load sources</option>';
    }
}

// Main search functions
async function executeIntelligentQuery() {
    const query = document.getElementById('intelligent-query').value.trim();
    if (!query) {
        showAlert('Please enter a query');
        return;
    }

    const lat = parseFloat(document.getElementById('query-lat').value) || null;
    const lon = parseFloat(document.getElementById('query-lon').value) || null;
    const limit = parseInt(document.getElementById('query-limit').value) || 5;
    const includeSummary = document.getElementById('include-summary').checked;

    const requestBody = {
        query: query,
        user_lat: lat,
        user_lon: lon,
        limit: limit,
        include_summary: includeSummary
    };

    try {
        const result = await apiCall('/news/query', {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });

        displayNewsResults(result, 'Intelligent Query Results');
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function searchByCategory() {
    const category = document.getElementById('category-select').value;
    if (!category) {
        showAlert('Please select a category');
        return;
    }

    const limit = parseInt(document.getElementById('category-limit').value) || 5;

    try {
        const result = await apiCall(`/news/category?category=${encodeURIComponent(category)}&limit=${limit}`);
        displayNewsResults(result, `Category: ${category}`);
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function searchByText() {
    const query = document.getElementById('search-query').value.trim();
    if (!query) {
        showAlert('Please enter a search query');
        return;
    }

    const limit = parseInt(document.getElementById('search-limit').value) || 5;

    try {
        const result = await apiCall(`/news/search?query=${encodeURIComponent(query)}&limit=${limit}`);
        displayNewsResults(result, `Text Search: "${query}"`);
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function searchBySource() {
    const source = document.getElementById('source-select').value;
    if (!source) {
        showAlert('Please select a source');
        return;
    }

    const limit = parseInt(document.getElementById('source-limit').value) || 5;

    try {
        const result = await apiCall(`/news/source?source=${encodeURIComponent(source)}&limit=${limit}`);
        displayNewsResults(result, `Source: ${source}`);
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function searchByScore() {
    const minScore = parseFloat(document.getElementById('score-threshold').value);
    if (isNaN(minScore) || minScore < 0 || minScore > 1) {
        showAlert('Please enter a valid score between 0 and 1');
        return;
    }

    const limit = parseInt(document.getElementById('score-limit').value) || 5;

    try {
        const result = await apiCall(`/news/score?min_score=${minScore}&limit=${limit}`);
        displayNewsResults(result, `High Quality (Score ≥ ${minScore})`);
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function searchNearby() {
    const lat = parseFloat(document.getElementById('nearby-lat').value);
    const lon = parseFloat(document.getElementById('nearby-lon').value);
    const radius = parseFloat(document.getElementById('nearby-radius').value) || 10;
    const limit = parseInt(document.getElementById('nearby-limit').value) || 5;

    if (isNaN(lat) || isNaN(lon)) {
        showAlert('Please enter valid latitude and longitude coordinates');
        return;
    }

    try {
        const result = await apiCall(`/news/nearby?lat=${lat}&lon=${lon}&radius=${radius}&limit=${limit}`);
        displayNewsResults(result, `Nearby (${radius}km from ${lat.toFixed(4)}, ${lon.toFixed(4)})`);
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function getTrending() {
    const lat = parseFloat(document.getElementById('trending-lat').value);
    const lon = parseFloat(document.getElementById('trending-lon').value);
    const radius = parseFloat(document.getElementById('trending-radius').value) || 20;
    const limit = parseInt(document.getElementById('trending-limit').value) || 10;

    if (isNaN(lat) || isNaN(lon)) {
        showAlert('Please enter valid latitude and longitude coordinates');
        return;
    }

    try {
        const result = await apiCall(`/trending/?lat=${lat}&lon=${lon}&radius=${radius}&limit=${limit}`);
        displayTrendingResults(result, `Trending (${radius}km from ${lat.toFixed(4)}, ${lon.toFixed(4)})`);
    } catch (error) {
        // Error already handled in apiCall
    }
}

// Utility functions
async function getRandomArticles() {
    try {
        const articles = await apiCall('/news/random?limit=5');
        displayRandomResults(articles, 'Random Articles');
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function simulateInteractions() {
    try {
        const result = await apiCall('/trending/simulate?num_events=50', {
            method: 'POST'
        });
        showAlert(`Successfully simulated ${result.data.events_created} user interactions!`, 'success');
    } catch (error) {
        // Error already handled in apiCall
    }
}

async function getActivityStats() {
    try {
        const stats = await apiCall('/trending/stats');
        displayStats(stats, 'User Activity Statistics');
    } catch (error) {
        // Error already handled in apiCall
    }
}

// Display functions
function displayNewsResults(result, title) {
    currentResults = result.articles || [];
    const container = document.getElementById('results-container');

    if (currentResults.length === 0) {
        container.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-search"></i>
                <p>No articles found for your search.</p>
                <p>Try adjusting your search criteria.</p>
            </div>
        `;
        return;
    }

    let html = `<div class="results-info">
        <h4><i class="fas fa-newspaper"></i> ${title}</h4>
        <p>Found ${result.total_count || currentResults.length} articles (showing ${currentResults.length})</p>
    </div>`;

    html += currentResults.map(article => createArticleCard(article)).join('');
    container.innerHTML = html;
}

function displayTrendingResults(articles, title) {
    currentResults = articles || [];
    const container = document.getElementById('results-container');

    if (currentResults.length === 0) {
        container.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-fire"></i>
                <p>No trending articles found in this area.</p>
                <p>Try a larger radius or simulate some user activity first.</p>
            </div>
        `;
        return;
    }

    let html = `<div class="results-info">
        <h4><i class="fas fa-fire"></i> ${title}</h4>
        <p>Found ${currentResults.length} trending articles</p>
    </div>`;

    html += currentResults.map(item => createTrendingCard(item)).join('');
    container.innerHTML = html;
}

function displayRandomResults(articles, title) {
    currentResults = articles || [];
    const container = document.getElementById('results-container');

    let html = `<div class="results-info">
        <h4><i class="fas fa-random"></i> ${title}</h4>
        <p>Showing ${currentResults.length} random articles</p>
    </div>`;

    html += currentResults.map(article => createArticleCard(article)).join('');
    container.innerHTML = html;
}

function displayStats(stats, title) {
    const container = document.getElementById('results-container');

    const html = `
        <div class="results-info">
            <h4><i class="fas fa-chart-bar"></i> ${title}</h4>
            <p>Activity data for the last ${stats.hours_analyzed || 24} hours</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">${stats.total_events || 0}</div>
                <div class="stat-label">Total Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.unique_users || 0}</div>
                <div class="stat-label">Unique Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.unique_articles || 0}</div>
                <div class="stat-label">Articles Interacted</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${Object.keys(stats.event_breakdown || {}).length}</div>
                <div class="stat-label">Event Types</div>
            </div>
        </div>

        ${stats.event_breakdown ? `
            <div class="api-section" style="margin-top: 1rem;">
                <h4>Event Breakdown</h4>
                ${Object.entries(stats.event_breakdown).map(([type, count]) => `
                    <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                        <span>${type}</span>
                        <span class="tag">${count}</span>
                    </div>
                `).join('')}
            </div>
        ` : ''}
    `;

    container.innerHTML = html;
}

// Card creation functions
function createArticleCard(article) {
    const pubDate = new Date(article.publication_date);
    const formattedDate = pubDate.toLocaleDateString() + ' ' + pubDate.toLocaleTimeString();

    return `
        <div class="article-card">
            <div class="article-header">
                <div>
                    <div class="article-title">${escapeHtml(article.title)}</div>
                    <div class="article-meta">
                        <span><i class="fas fa-calendar"></i> ${formattedDate}</span>
                        <span><i class="fas fa-globe"></i> ${escapeHtml(article.source_name)}</span>
                        <span class="score-badge">Score: ${article.relevance_score.toFixed(2)}</span>
                        ${article.distance_km ? `<span><i class="fas fa-map-marker-alt"></i> ${article.distance_km.toFixed(1)} km</span>` : ''}
                    </div>
                </div>
            </div>

            <div class="article-description">
                ${escapeHtml(article.description)}
            </div>

            ${article.llm_summary ? `
                <div class="article-summary">
                    <strong><i class="fas fa-robot"></i> AI Summary:</strong><br>
                    ${escapeHtml(article.llm_summary)}
                </div>
            ` : ''}

            <div class="article-tags">
                ${article.category.map(cat => `<span class="tag">${escapeHtml(cat)}</span>`).join('')}
                <a href="${article.url}" target="_blank" class="btn btn-outline" style="margin-left: auto;">
                    <i class="fas fa-external-link-alt"></i> Read More
                </a>
            </div>
        </div>
    `;
}

function createTrendingCard(item) {
    const article = item.article;
    const pubDate = new Date(article.publication_date);
    const formattedDate = pubDate.toLocaleDateString() + ' ' + pubDate.toLocaleTimeString();

    return `
        <div class="article-card">
            <div class="article-header">
                <div>
                    <div class="article-title">${escapeHtml(article.title)}</div>
                    <div class="article-meta">
                        <span><i class="fas fa-calendar"></i> ${formattedDate}</span>
                        <span><i class="fas fa-globe"></i> ${escapeHtml(article.source_name)}</span>
                        <span class="trending-score">Trending: ${item.trending_score.toFixed(1)}</span>
                    </div>
                </div>
            </div>

            <div class="article-description">
                ${escapeHtml(article.description)}
            </div>

            <div class="stats-grid" style="margin: 1rem 0;">
                <div class="stat-card">
                    <div class="stat-number">${item.interaction_count}</div>
                    <div class="stat-label">Total Interactions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${item.unique_users}</div>
                    <div class="stat-label">Unique Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${item.recent_interactions}</div>
                    <div class="stat-label">Recent Activity</div>
                </div>
            </div>

            <div class="article-tags">
                ${article.category.map(cat => `<span class="tag">${escapeHtml(cat)}</span>`).join('')}
                <a href="${article.url}" target="_blank" class="btn btn-outline" style="margin-left: auto;">
                    <i class="fas fa-external-link-alt"></i> Read More
                </a>
            </div>
        </div>
    `;
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Health check function accessible from UI
async function checkHealth() {
    await checkSystemHealth();
    showAlert(`System status: ${systemStatus}`, systemStatus === 'healthy' ? 'success' : 'error');
}