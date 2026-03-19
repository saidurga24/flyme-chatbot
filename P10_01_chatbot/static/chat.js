// Chat interface logic - talks to /api/chat

// Generate a unique conversation ID for this session
const conversationId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const suggestions = document.getElementById('suggestions');
const todayDate = document.getElementById('todayDate');
const welcomeTime = document.getElementById('welcomeTime');

// Set today's date
const now = new Date();
todayDate.textContent = now.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
});
welcomeTime.textContent = formatTime(now);

// Event listeners
userInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

/**
 * Format a Date object to a time string (HH:MM AM/PM)
 */
function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

/**
 * Add a message to the chat display.
 * @param {string} text - Message text
 * @param {boolean} isUser - Whether the message is from the user
 */
function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    // Parse markdown-style formatting
    const formattedText = formatMessageText(text);
    bubble.innerHTML = formattedText;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = formatTime(new Date());

    messageDiv.appendChild(bubble);
    messageDiv.appendChild(timeSpan);
    chatMessages.appendChild(messageDiv);

    scrollToBottom();
}

/**
 * Format message text with basic markdown support.
 */
function formatMessageText(text) {
    return text
        // Bold: **text**
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic: *text*
        .replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
        // Line breaks
        .replace(/\n/g, '<br>')
        // Bullet points
        .replace(/^• (.+)/gm, '<li>$1</li>')
        // Wrap consecutive <li> in <ul>
        .replace(/((?:<li>.*<\/li>\s*)+)/g, '<ul>$1</ul>');
}

/**
 * Show a typing indicator while waiting for bot response.
 */
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.id = 'typingIndicator';

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    typingDiv.appendChild(indicator);
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

/**
 * Remove the typing indicator.
 */
function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Scroll the chat area to the bottom.
 */
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Send a message from a suggestion chip.
 */
function sendSuggestion(text) {
    userInput.value = text;
    sendMessage();
}

/**
 * Send the user's message to the bot API.
 */
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Hide suggestions after first message
    suggestions.classList.add('hidden');

    // Display user message
    addMessage(message, true);
    userInput.value = '';
    sendButton.disabled = true;

    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId,
            }),
        });

        const data = await response.json();
        removeTypingIndicator();

        if (data.reply) {
            // Split multiple bot responses and show them
            const replies = data.reply.split('\n').filter(r => r.trim());
            addMessage(data.reply, false);
        }
    } catch (error) {
        removeTypingIndicator();
        addMessage('Sorry, I couldn\'t connect to the server. Please make sure the bot is running and try again.', false);
        console.error('Error sending message:', error);
    }

    sendButton.disabled = false;
    userInput.focus();
}
