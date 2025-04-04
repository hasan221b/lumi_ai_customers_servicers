let currentChatId = null;
let currentUserId = null;

async function init() {
    const userResponse = await fetch('/get_user_id');
    const userData = await userResponse.json();
    currentUserId = userData.user_id;

    const chatsResponse = await fetch(`/chats/${currentUserId}`);
    const chatsData = await chatsResponse.json();
    const contactList = document.getElementById('contact-list');
    contactList.innerHTML = '';
    chatsData.chats.forEach(chat => {
        const contactDiv = document.createElement('div');
        contactDiv.classList.add('contact');
        contactDiv.setAttribute('data-chat-id', chat.chat_id);
        contactDiv.innerHTML = `
            <div class="avatar"></div>
            <div class="contact-info">
                <p>${chat.chat_name}</p>
                <small>No messages yet...</small>
            </div>
            <button class="delete-chat-btn" onclick="deleteChat(${chat.chat_id})">Delete</button>
        `;
        contactList.appendChild(contactDiv);
        contactDiv.addEventListener('click', (e) => {
            if (!e.target.classList.contains('delete-chat-btn')) {
                openChat(chat.chat_id);
            }
        });
    });
}

async function startNewChat() {
    const response = await fetch(`/start_chat/${currentUserId}`, { method: 'POST' });
    if (!response.ok) {
        const error = await response.json();
        alert(error.detail);
        return;
    }
    const data = await response.json();
    const contactList = document.getElementById('contact-list');
    const contactDiv = document.createElement('div');
    contactDiv.classList.add('contact');
    contactDiv.setAttribute('data-chat-id', data.chat_id);
    contactDiv.innerHTML = `
        <div class="avatar"></div>
        <div class="contact-info">
            <p>${data.chat_name}</p>
            <small>Hello! I'm Lumi...</small> <!-- Reflect starter message -->
        </div>
        <button class="delete-chat-btn" onclick="deleteChat(${data.chat_id})">Delete</button>
    `;
    contactList.appendChild(contactDiv);
    contactDiv.addEventListener('click', (e) => {
        if (!e.target.classList.contains('delete-chat-btn')) {
            openChat(data.chat_id);
        }
    });
    openChat(data.chat_id);
}

async function openChat(chatId) {
    currentChatId = chatId;
    const contacts = document.querySelectorAll('.contact');
    contacts.forEach(contact => {
        contact.classList.remove('active');
        if (parseInt(contact.getAttribute('data-chat-id')) === chatId) {
            contact.classList.add('active');
        }
    });

    // Fetch and display chat messages
    const response = await fetch(`/chat/${currentUserId}/${chatId}/messages`);
    const data = await response.json();
    const chatHeader = document.getElementById('chat-header');
    chatHeader.querySelector('h2').textContent = data.chat_name;
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
    data.messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', message.type);
        messageDiv.innerHTML = `<p>${message.text}</p>`;
        chatMessages.appendChild(messageDiv);
    });
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function deleteChat(chatId) {
    if (confirm('Are you sure you want to delete this chat?')) {
        await fetch(`/chat/${currentUserId}/${chatId}`, { method: 'DELETE' });
        const contact = document.querySelector(`.contact[data-chat-id="${chatId}"]`);
        if (contact) contact.remove();
        if (currentChatId === chatId) {
            currentChatId = null;
            document.getElementById('chat-header').querySelector('h2').textContent = '';
            document.getElementById('chat-messages').innerHTML = '';
        }
    }
}

async function sendMessage() {
    if (currentChatId === null) {
        alert('Please start a new chat first!');
        return;
    }
    const input = document.getElementById('message-input');
    const messageText = input.value.trim();
    if (!messageText) return;

    const chatMessages = document.getElementById('chat-messages');
    const userMessage = document.createElement('div');
    userMessage.classList.add('message', 'sent');
    userMessage.innerHTML = `<p>${messageText}</p>`;
    chatMessages.appendChild(userMessage);
    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Add "thinking..." indicator
    const thinkingMessage = document.createElement('div');
    thinkingMessage.classList.add('message', 'received', 'thinking');
    thinkingMessage.innerHTML = `<p>Thinking...</p>`;
    chatMessages.appendChild(thinkingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`/chat/${currentUserId}/${currentChatId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: messageText })
        });
        if (!response.ok) {
            const error = await response.json();
            alert(error.detail);  // Display the limit reached message
            chatMessages.removeChild(thinkingMessage); // Remove thinking message on error
            return;
        }
        const data = await response.json();

        // Update chat name and preview
        const contact = document.querySelector(`.contact[data-chat-id="${currentChatId}"]`);
        if (contact.querySelector('small').textContent === 'Hello! I\'m Lumi...') {
            contact.querySelector('p').textContent = extractTopic(messageText);
            document.getElementById('chat-header').querySelector('h2').textContent = contact.querySelector('p').textContent;
        }
        contact.querySelector('small').textContent = data.response.slice(0, 20) + (data.response.length > 20 ? '...' : '');

        // Remove "thinking..." and add bot response
        chatMessages.removeChild(thinkingMessage);
        const botMessage = document.createElement('div');
        botMessage.classList.add('message', 'received');
        botMessage.innerHTML = `<p>${data.response}</p>`;
        chatMessages.appendChild(botMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        console.error('Error sending message:', error);
        chatMessages.removeChild(thinkingMessage); // Remove thinking message on error
        alert('An error occurred while sending your message.');
    }
}

function extractTopic(message) {
    const words = message.split(' ').filter(word => word.length > 3);
    return words.length > 0 ? words[0].charAt(0).toUpperCase() + words[0].slice(1) : 'General Chat';
}

document.getElementById('message-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

document.addEventListener('DOMContentLoaded', init);
