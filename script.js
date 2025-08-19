const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', function() {
  const file = this.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      localStorage.setItem('uploadedImage', e.target.result);
      window.location.href = "ml-result.html"; // redirect to demo ML page
    }
    reader.readAsDataURL(file);
  }
});

// Camera functionality for scanner
const startScannerBtn = document.getElementById('startScannerBtn');
const cameraPreview = document.getElementById('cameraPreview');
const captureBtn = document.getElementById('captureBtn');
const captureCanvas = document.getElementById('captureCanvas');

if (startScannerBtn && cameraPreview && captureBtn) {
  startScannerBtn.addEventListener('click', function() {
    // Show video and capture button
    cameraPreview.style.display = 'block';
    captureBtn.style.display = 'block';
    startScannerBtn.style.display = 'none';

    // Start camera
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {
          cameraPreview.srcObject = stream;
        })
        .catch(function(err) {
          console.error('Camera error:', err);
        });
    }
  });
}

if (captureBtn && cameraPreview && captureCanvas) {
  captureBtn.addEventListener('click', function() {
    const context = captureCanvas.getContext('2d');
    context.drawImage(cameraPreview, 0, 0, captureCanvas.width, captureCanvas.height);
    captureCanvas.style.display = 'block';

    // Save image to localStorage
    const imageData = captureCanvas.toDataURL('image/png');
    localStorage.setItem('capturedPhoto', imageData);

    // Show download link
    let downloadLink = document.getElementById('downloadPhotoLink');
    if (!downloadLink) {
      downloadLink = document.createElement('a');
      downloadLink.id = 'downloadPhotoLink';
      downloadLink.textContent = 'Download Photo';
      downloadLink.style.display = 'block';
      downloadLink.style.marginTop = '10px';
      captureCanvas.parentNode.appendChild(downloadLink);
    }
    downloadLink.href = imageData;
    downloadLink.download = 'captured_photo.png';

    // Redirect to another website after capture
    window.location.href = "ml-result.html";
  });
}

// Chatbot functionality

const chatbotHeader = document.getElementById('chatbotHeader');
const chatbotBody = document.getElementById('chatbotBody');
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const chatbotToggle = document.getElementById('chatbotToggle');

// Hide chatbot body on page load
chatbotBody.style.display = 'none';

let isChatOpen = false;

chatbotToggle.addEventListener('click', () => {
  isChatOpen = !isChatOpen;
  chatbotBody.style.display = isChatOpen ? 'flex' : 'none';
  chatbotToggle.textContent = isChatOpen ? '-' : '+';
});

sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  // Add user message to chat
  addMessage(message, 'user');
  userInput.value = '';

  // Show typing indicator
  const typingIndicator = addMessage('typing...', 'bot');
  
  try {
    // Call OpenRouter API
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer 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',
        'Content-Type': 'application/json',
        'HTTP-Referer': window.location.href,
        'X-Title': 'HealthCare+'
      },
      body: JSON.stringify({
        model: "deepseek/deepseek-chat-v3-0324:free",
        messages: [
          {
            role: "system",
            content: "You are a helpful medical assistant for HealthCare+. Provide accurate health information but always recommend consulting a doctor for serious concerns. Be friendly and professional."
          },
          {
            role: "user",
            content: message
          }
        ]
      })
    });

    const data = await response.json();
    
    // Remove typing indicator
    chatMessages.removeChild(typingIndicator);
    
    // Add bot response
    if (data.choices && data.choices[0] && data.choices[0].message) {
      addMessage(data.choices[0].message.content, 'bot');
    } else {
      addMessage("I'm sorry, I couldn't process your request. Please try again later.", 'bot');
    }
  } catch (error) {
    console.error('Error:', error);
    // Remove typing indicator
    chatMessages.removeChild(typingIndicator);
    addMessage("Sorry, I'm having trouble connecting to the server. Please try again later.", 'bot');
  }
}

function addMessage(text, sender) {
  const messageDiv = document.createElement('div');
  messageDiv.classList.add('message');
  messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
  messageDiv.textContent = text;
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return messageDiv;
}