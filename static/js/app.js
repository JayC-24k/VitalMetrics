(() => {
  const form = document.getElementById('chatForm');
  if (!form) return;
  const input = document.getElementById('chatInput');
  const messages = document.getElementById('chatMessages');
  const addMessage = (text, kind) => {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${kind === 'user' ? 'chat-user' : 'chat-assistant'}`;
    bubble.textContent = text;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
  };
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    addMessage(message, 'user');
    input.value = '';
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const response = await fetch(document.body.dataset.chatUrl || '/chat', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message})
      });
      const data = await response.json();
      addMessage(data.response || 'No pude procesar el mensaje.', 'assistant');
    } catch (_) {
      addMessage('No pude conectar con el asistente. Inténtalo de nuevo.', 'assistant');
    } finally {
      button.disabled = false;
      input.focus();
    }
  });
})();
