const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const initializeBtn = document.getElementById('initialize-btn');
const statusIndicator = document.getElementById('connection-status');
const statusText = document.getElementById('status-text');
const loaderOverlay = document.getElementById('loader-overlay');
const loaderText = document.getElementById('loader-text');

// State
let isProcessing = false;

// Check API health on load
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            statusIndicator.classList.remove('offline');
            statusIndicator.classList.add('online');
            
            if (data.initialized) {
                statusText.innerText = 'System Ready';
            } else {
                statusText.innerText = 'Needs Initialization';
            }
        }
    } catch (error) {
        console.error('Health check failed:', error);
        statusIndicator.classList.add('offline');
        statusText.innerText = 'API Offline';
    }
}

// Add a message to the UI
function addMessage(text, role, sources = []) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${role}`;
    
    let content = `<div class="msg-bubble"><p>${text}</p>`;
    
    if (sources && sources.length > 0) {
        content += `<div class="sources-container"><strong>Sources:</strong> `;
        const uniqueSources = [...new Set(sources.map(s => s.source))];
        uniqueSources.forEach(source => {
            const fileName = source.split(/[\\/]/).pop();
            content += `<span class="source-tag">${fileName}</span>`;
        });
        content += `</div>`;
    }
    
    content += `</div>`;
    msgDiv.innerHTML = content;
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Handle chat submission
async function handleChat(e) {
    if (e) e.preventDefault();
    
    const question = userInput.value.trim();
    if (!question || isProcessing) return;
    
    // Add user message
    addMessage(question, 'user');
    userInput.value = '';
    
    // Set loading state
    isProcessing = true;
    sendBtn.disabled = true;
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addMessage(data.answer, 'bot', data.sources);
        } else {
            addMessage(`Error: ${data.detail || 'Something went wrong'}`, 'bot');
        }
    } catch (error) {
        addMessage(`Connection error: ${error.message}`, 'bot');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
    }
}

// Handle initialization
async function handleInitialize() {
    loaderOverlay.classList.remove('hidden');
    loaderText.innerText = 'Indexing documents, please wait...';
    
    try {
        const response = await fetch('/initialize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force_recreate: false })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            statusText.innerText = 'System Ready';
            addMessage("System initialized successfully! You can now ask questions about your documents.", "bot");
        } else {
            alert(`Initialization failed: ${data.detail}`);
        }
    } catch (error) {
        alert(`Request failed: ${error.message}`);
    } finally {
        loaderOverlay.classList.add('hidden');
        checkHealth();
    }
}

// Event Listeners
chatForm.addEventListener('submit', handleChat);
initializeBtn.addEventListener('click', handleInitialize);

// Focus input on load
window.addEventListener('load', () => {
    userInput.focus();
    checkHealth();
});
