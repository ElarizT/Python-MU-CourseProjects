// Handle large file uploads in the chat interface
document.addEventListener('DOMContentLoaded', function() {
    // File upload button handler
    const uploadButton = document.getElementById('uploadButton');
    if (!uploadButton) return;
    
    const hiddenFileInput = document.createElement('input');
    hiddenFileInput.type = 'file';
    hiddenFileInput.accept = '.txt,.pdf,.docx,.xlsx,.csv';
    hiddenFileInput.style.display = 'none';
    document.body.appendChild(hiddenFileInput);
    
    uploadButton.addEventListener('click', function(e) {
        e.preventDefault();
        hiddenFileInput.click();
    });
    
    hiddenFileInput.addEventListener('change', function() {
        if (this.files && this.files.length > 0) {
            const file = this.files[0];
            
            // Validate file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                alert('File size must be less than 10MB');
                this.value = '';
                return;
            }
            
            // Create FormData and append file
            const formData = new FormData();
            formData.append('file', file);
            
            // Show upload in progress message
            const chatMessages = document.getElementById('chatMessages');
            const userMsg = document.createElement('div');
            userMsg.className = 'user-message message';
            userMsg.innerHTML = `<div class="message-bubble"><p>Uploading file: ${file.name}</p></div>`;
            chatMessages.appendChild(userMsg);
            
            // Show typing indicator
            const typingIndicator = document.createElement('div');
            typingIndicator.className = 'bot-message message typing-indicator';
            typingIndicator.innerHTML = `
                <div class="message-bubble">
                    <div class="typing">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            chatMessages.appendChild(typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Track upload time for timeout handling
            const startTime = Date.now();
            const UPLOAD_TIMEOUT = 60000; // 60 seconds timeout
            let uploadTimeoutId = setTimeout(function() {
                // Remove typing indicator if still present
                if (chatMessages.contains(typingIndicator)) {
                    chatMessages.removeChild(typingIndicator);
                    
                    // Add timeout message
                    const timeoutMsg = document.createElement('div');
                    timeoutMsg.className = 'bot-message message';
                    timeoutMsg.innerHTML = `<div class="message-bubble">
                        <p>The file upload is taking longer than expected. This could be because:</p>
                        <ul>
                            <li>The file is very large</li>
                            <li>Your internet connection is slow</li>
                            <li>The server is busy processing other requests</li>
                        </ul>
                        <p>Please try again with a smaller file or wait and try again later.</p>
                    </div>`;
                    chatMessages.appendChild(timeoutMsg);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            }, UPLOAD_TIMEOUT);
            
            // Upload file with timeout handling
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                // Clear timeout as we got a response
                clearTimeout(uploadTimeoutId);
                return response.json();
            })
            .then(data => {
                // Calculate upload and processing time for logging
                const processingTime = Date.now() - startTime;
                console.log(`File processed in ${processingTime}ms`);
                
                // Remove typing indicator
                if (chatMessages.contains(typingIndicator)) {
                    chatMessages.removeChild(typingIndicator);
                }
                
                // Add bot response
                const botMsg = document.createElement('div');
                botMsg.className = 'bot-message message';
                
                if (data.success) {
                    // Choose appropriate message based on the current module or mode
                    const agentObj = window.liyaAgent;
                    let moduleType = "default";
                    if (agentObj && agentObj.activeModule) {
                        moduleType = agentObj.activeModule;
                    }
                    
                    let successMsg = '';
                    switch(moduleType) {
                        case 'proofread':
                            successMsg = `File uploaded successfully. You can now ask me to proofread ${file.name}.`;
                            break;
                        case 'study':
                            successMsg = `File uploaded successfully. I can help you study the content in ${file.name}.`;
                            break;
                        case 'entertainment':
                            successMsg = `File uploaded successfully. I can discuss the content of ${file.name} with you.`;
                            break;
                        case 'excel':
                            successMsg = `File uploaded successfully. I can help you analyze or transform the data in ${file.name}.`;
                            break;
                        case 'presentation':
                            successMsg = `File uploaded successfully. I can create a presentation based on ${file.name}.`;
                            break;
                        default:
                            successMsg = `File uploaded successfully. Let me know what you'd like to do with ${file.name}.`;
                    }
                    
                    // Add a note if the content was large and truncated
                    let sizeNote = '';
                    if (data.is_truncated) {
                        const sizeMB = (data.full_content_size / (1024 * 1024)).toFixed(2);
                        sizeNote = `<p><em>Note: This is a large file (${sizeMB}MB of text). I have the content and can answer questions about it.</em></p>`;
                    }
                    
                    botMsg.innerHTML = `<div class="message-bubble">
                        <p>${successMsg}</p>
                        ${sizeNote}
                        <p><em>Ask me a question about this file to get started.</em></p>
                    </div>`;
                } else {
                    botMsg.innerHTML = `<div class="message-bubble">
                        <p>Sorry, there was an error uploading your file: ${data.error || 'Unknown error'}</p>
                    </div>`;
                }
                
                chatMessages.appendChild(botMsg);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                // Reset file input
                hiddenFileInput.value = '';
            })
            .catch(error => {
                // Clear timeout as we got an error
                clearTimeout(uploadTimeoutId);
                console.error('File upload error:', error);
                
                // Remove typing indicator
                if (chatMessages.contains(typingIndicator)) {
                    chatMessages.removeChild(typingIndicator);
                }
                
                // Add error message
                const errorMsg = document.createElement('div');
                errorMsg.className = 'bot-message message';
                errorMsg.innerHTML = `<div class="message-bubble">
                    <p>Sorry, there was an error uploading your file. Please try again.</p>
                </div>`;
                chatMessages.appendChild(errorMsg);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                // Reset file input
                hiddenFileInput.value = '';
            });
        }
    });
});
