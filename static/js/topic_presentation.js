/**
 * LightYearAI Topic-Based Presentation Generator
 * 
 * This module handles the client-side functionality for generating presentations
 * directly from topics using LLM.
 */

class TopicPresentationGenerator {
    /**
     * Initialize the topic-based presentation generator
     * @param {string} containerSelector - The CSS selector for the container element
     */
    constructor(containerSelector = '#topic-presentation-container') {
        this.container = document.querySelector(containerSelector);
        if (!this.container) {
            console.error('Topic presentation container not found');
            return;
        }
        
        this.initUI();
        this.bindEvents();
    }
    
    /**
     * Initialize the user interface
     */
    initUI() {
        const html = `
            <div class="topic-presentation-form">
                <h2>Generate Presentation from Topic</h2>
                <p class="description">Enter a topic and our AI will create a professional presentation with relevant content.</p>
                
                <div class="form-group">
                    <label for="presentation-topic">Presentation Topic</label>
                    <input type="text" id="presentation-topic" class="form-control" 
                           placeholder="e.g., Climate Change Impact on Business, Digital Marketing Trends 2025...">
                </div>
                
                <div class="form-group">
                    <label for="presentation-style">Presentation Style</label>
                    <select id="presentation-style" class="form-control">
                        <option value="professional" selected>Professional</option>
                        <option value="academic">Academic</option>
                        <option value="casual">Casual</option>
                    </select>
                </div>
                
                <div class="examples">
                    <h3>Example Topics</h3>
                    <div class="example-topics">
                        <button class="example-topic" data-topic="Artificial Intelligence in Healthcare">AI in Healthcare</button>
                        <button class="example-topic" data-topic="Sustainable Business Practices">Sustainable Business</button>
                        <button class="example-topic" data-topic="Remote Work Best Practices">Remote Work</button>
                        <button class="example-topic" data-topic="Future of Renewable Energy">Renewable Energy</button>
                        <button class="example-topic" data-topic="Blockchain Technology Applications">Blockchain Applications</button>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <button id="generate-presentation" class="btn btn-primary">Generate Presentation</button>
                </div>
                
                <div id="presentation-status" class="status-message" style="display: none;">
                    <div class="spinner"></div>
                    <span id="status-text">Generating your presentation...</span>
                </div>
                
                <div id="presentation-result" class="result-section" style="display: none;">
                    <h3>Your Presentation is Ready</h3>
                    <div class="presentation-actions">
                        <a href="#" id="download-presentation" class="btn btn-success" target="_blank">
                            <i class="fa fa-download"></i> Download Presentation
                        </a>
                        <a href="#" id="view-presentation" class="btn btn-info" target="_blank">
                            <i class="fa fa-eye"></i> View Presentation
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
        
        // Cache UI elements
        this.topicInput = this.container.querySelector('#presentation-topic');
        this.styleSelect = this.container.querySelector('#presentation-style');
        this.generateButton = this.container.querySelector('#generate-presentation');
        this.statusSection = this.container.querySelector('#presentation-status');
        this.statusText = this.container.querySelector('#status-text');
        this.resultSection = this.container.querySelector('#presentation-result');
        this.downloadLink = this.container.querySelector('#download-presentation');
        this.viewLink = this.container.querySelector('#view-presentation');
    }
    
    /**
     * Bind event listeners
     */
    bindEvents() {
        // Generate button click
        this.generateButton.addEventListener('click', () => this.generatePresentation());
        
        // Example topic buttons
        const exampleButtons = this.container.querySelectorAll('.example-topic');
        exampleButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.topicInput.value = button.getAttribute('data-topic');
                this.topicInput.focus();
            });
        });
        
        // Enter key in topic input
        this.topicInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.generatePresentation();
            }
        });
    }
    
    /**
     * Generate a presentation from the topic
     */
    generatePresentation() {
        const topic = this.topicInput.value.trim();
        if (!topic) {
            alert('Please enter a presentation topic');
            this.topicInput.focus();
            return;
        }
        
        const style = this.styleSelect.value;
        
        // Show status and hide results
        this.statusSection.style.display = 'block';
        this.resultSection.style.display = 'none';
        this.generateButton.disabled = true;
        this.statusText.textContent = 'Generating your presentation...';
        
        // Prepare form data
        const formData = new FormData();
        formData.append('topic', topic);
        formData.append('tone', style);
        
        // Send request to server
        fetch('/api/topic-presentation', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error generating presentation');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.statusText.textContent = 'Presentation created successfully!';
                
                // Set download and view links
                this.downloadLink.href = data.download_url;
                this.viewLink.href = data.view_url;
                
                // Show result section
                this.resultSection.style.display = 'block';
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            this.statusText.textContent = `Error: ${error.message}`;
        })
        .finally(() => {
            this.generateButton.disabled = false;
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if container exists before initializing
    if (document.querySelector('#topic-presentation-container')) {
        window.topicPresentationGenerator = new TopicPresentationGenerator();
    }
});
