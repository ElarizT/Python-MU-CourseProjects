/**
 * Enhanced file processing utilities for LightYearAI
 * Improves handling of large files in the chat interface
 */

// File processing manager
const FileProcessor = {
    // Track uploads in progress
    activeUploads: {},
    
    // Timeout for file uploads in ms (60 seconds)
    uploadTimeout: 60000,
    
    /**
     * Process a file upload with timeout handling and error management
     * @param {File} file - The file object to upload
     * @param {Function} onStart - Callback when upload starts
     * @param {Function} onSuccess - Callback on successful upload
     * @param {Function} onError - Callback on error
     * @param {Function} onTimeout - Callback on timeout
     */
    uploadFile(file, onStart, onSuccess, onError, onTimeout) {
        // Generate a unique ID for this upload
        const uploadId = Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Call start callback
        if (onStart && typeof onStart === 'function') {
            onStart(uploadId, file);
        }
        
        // Set timeout handler
        this.activeUploads[uploadId] = {
            file,
            timeoutId: setTimeout(() => {
                if (this.activeUploads[uploadId]) {
                    // Call timeout callback
                    if (onTimeout && typeof onTimeout === 'function') {
                        onTimeout(uploadId, file);
                    }
                    // Remove from active uploads
                    delete this.activeUploads[uploadId];
                }
            }, this.uploadTimeout)
        };
        
        // Start fetch request
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            // Clear timeout as we got a response
            if (this.activeUploads[uploadId]) {
                clearTimeout(this.activeUploads[uploadId].timeoutId);
            }
            
            // Check if response is ok
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            return response.json();
        })
        .then(data => {
            // Call success callback
            if (onSuccess && typeof onSuccess === 'function') {
                onSuccess(uploadId, file, data);
            }
            
            // Remove from active uploads
            delete this.activeUploads[uploadId];
        })
        .catch(error => {
            console.error('File upload error:', error);
            
            // Clear timeout if exists
            if (this.activeUploads[uploadId]) {
                clearTimeout(this.activeUploads[uploadId].timeoutId);
            }
            
            // Call error callback
            if (onError && typeof onError === 'function') {
                onError(uploadId, file, error);
            }
            
            // Remove from active uploads
            delete this.activeUploads[uploadId];
        });
        
        // Return the upload ID for tracking
        return uploadId;
    },
    
    /**
     * Cancel an active file upload
     * @param {string} uploadId - The ID of the upload to cancel 
     */
    cancelUpload(uploadId) {
        if (this.activeUploads[uploadId]) {
            clearTimeout(this.activeUploads[uploadId].timeoutId);
            delete this.activeUploads[uploadId];
            return true;
        }
        return false;
    },
    
    /**
     * Get estimated file size description
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted file size description
     */
    getFileSizeDescription(bytes) {
        if (bytes < 1024) {
            return bytes + ' B';
        } else if (bytes < 1024 * 1024) {
            return (bytes / 1024).toFixed(2) + ' KB';
        } else if (bytes < 1024 * 1024 * 1024) {
            return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
        } else {
            return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
        }
    }
};

// Integration with chat interface
document.addEventListener('DOMContentLoaded', function() {
    // Integrate with existing file upload capabilities
    const uploadButton = document.getElementById('uploadButton');
    if (!uploadButton) return;
    
    // Create hidden file input
    const hiddenFileInput = document.createElement('input');
    hiddenFileInput.type = 'file';
    hiddenFileInput.accept = '.txt,.pdf,.docx,.xlsx,.csv';
    hiddenFileInput.style.display = 'none';
    document.body.appendChild(hiddenFileInput);
    
    // Handle upload button click
    uploadButton.addEventListener('click', function(e) {
        e.preventDefault();
        hiddenFileInput.click();
    });
    
    // Handle file selection
    hiddenFileInput.addEventListener('change', function() {
        if (!this.files || this.files.length === 0) return;
        
        const file = this.files[0];
        const chatMessages = document.getElementById('chatMessages');
        
        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert('File size must be less than 10MB');
            this.value = '';
            return;
        }
        
        // Show user message about file upload
        const userMsg = document.createElement('div');
        userMsg.className = 'user-message message';
        userMsg.innerHTML = `<div class="message-bubble">
            <p>Uploading file: ${file.name} (${FileProcessor.getFileSizeDescription(file.size)})</p>
        </div>`;
        chatMessages.appendChild(userMsg);
        
        // Create typing indicator
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
        
        // Upload callbacks
        const onStart = (uploadId, file) => {
            console.log(`Starting upload: ${file.name} (${FileProcessor.getFileSizeDescription(file.size)})`);
            chatMessages.appendChild(typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        };
        
        const onSuccess = (uploadId, file, data) => {
            console.log(`Upload successful: ${file.name}`);
            
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
                    sizeNote = `<p><em>Note: This is a large file (${sizeMB} MB of text). 
                        I have the content and can answer questions about it.</em></p>`;
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
        };
        
        const onError = (uploadId, file, error) => {
            console.error(`Upload error: ${error}`);
            
            // Remove typing indicator
            if (chatMessages.contains(typingIndicator)) {
                chatMessages.removeChild(typingIndicator);
            }
            
            // Add error message
            const errorMsg = document.createElement('div');
            errorMsg.className = 'bot-message message';
            errorMsg.innerHTML = `<div class="message-bubble">
                <p>Sorry, there was an error uploading your file. Please try again.</p>
                <p><em>Error details: ${error.message || 'Unknown error'}</em></p>
            </div>`;
            chatMessages.appendChild(errorMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Reset file input
            hiddenFileInput.value = '';
        };
        
        const onTimeout = (uploadId, file) => {
            console.warn(`Upload timeout: ${file.name}`);
            
            // Remove typing indicator
            if (chatMessages.contains(typingIndicator)) {
                chatMessages.removeChild(typingIndicator);
            }
            
            // Add timeout message
            const timeoutMsg = document.createElement('div');
            timeoutMsg.className = 'bot-message message';
            timeoutMsg.innerHTML = `<div class="message-bubble">
                <p>The upload of ${file.name} is taking longer than expected. This could be because:</p>
                <ul>
                    <li>The file is very large (${FileProcessor.getFileSizeDescription(file.size)})</li>
                    <li>Your internet connection is slow</li>
                    <li>The server is busy processing other requests</li>
                </ul>
                <p>You can try again with a smaller file or wait a moment and try again.</p>
            </div>`;
            chatMessages.appendChild(timeoutMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Reset file input
            hiddenFileInput.value = '';
        };
        
        // Start the upload
        FileProcessor.uploadFile(file, onStart, onSuccess, onError, onTimeout);
        
        // Reset file input for next upload
        this.value = '';
    });
});
