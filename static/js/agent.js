/**
 * LightYearAI - Agent Development Kit (ADK) Client Integration
 * 
 * This module handles client-side interaction with the server-side ADK agents.
 * It provides functions for communicating with the agent API, rendering agent responses,
 * and handling form submissions for different features through a unified interface.
 */

class LiyaAgent {
    constructor(chatContainerId = 'unified-chat', options = {}) {
        // Default configuration
        this.config = {
            // Various config options
            // ...existing code...
        };
        
        // Override defaults with provided options
        Object.assign(this.config, options);
        
        // Initialize properties
        this.sessionId = this.generateSessionId();
        this.activeModule = null;
        this.isProcessing = false;
        this.messageHistory = [];
        this.contextData = {}; // Stores contextual data for modules
        this.uploadedFiles = {}; // Store uploaded file references
        this.fileHistory = {}; // Store history of all uploaded files
        
        this.isUserLoggedIn = false; // Track login status
          // Bind DOM elements when the document is ready
        document.addEventListener('DOMContentLoaded', () => {
            this.bindDomElements();
            this.setupEventListeners();
            this.checkLoginStatus(); // Check if user is logged in
            
            // Always start with a new chat when the app opens
            this.startNewChat();
        });
    }
    
    /**
     * Generate a unique session ID
     */
    generateSessionId() {
        return Date.now().toString(36) + Math.random().toString(36).substring(2);
    }
      /**
     * Bind DOM elements for the unified chat interface
     */
    bindDomElements() {
        // Chat UI elements
        this.chatSidebar = document.getElementById('chatSidebar');
        this.chatMain = document.getElementById('chatMain');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.commandSuggestions = document.getElementById('commandSuggestions');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.newChatBtn = document.getElementById('newChatBtn');        this.chatHistory = document.getElementById('chatHistory');
        this.syncButton = document.getElementById('syncButton');
        this.chatHistorySearch = document.getElementById('chatHistorySearch');
        this.clearSearchBtn = document.getElementById('clearSearchBtn');
        
        // Keep track of all chats for filtering
        this.allChats = [];
    }/**
     * Set up event listeners for the chat interface
     */
    setupEventListeners() {
        // Chat input handling
        if (this.chatInput) {
            this.chatInput.addEventListener('input', (e) => {
                // Auto-resize textarea
                this.chatInput.style.height = 'auto';
                this.chatInput.style.height = (this.chatInput.scrollHeight) + 'px';
                
                // Handle slash commands
                this.handleChatInputChange(e);
            });
            
            this.chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleChatSubmit();
                }
            });
        }
        
        // Sidebar toggle
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }
          // New chat button
        if (this.newChatBtn) {
            this.newChatBtn.addEventListener('click', () => this.startNewChat());
        }
          // Chat history search
        if (this.chatHistorySearch) {
            const clearSearchBtn = document.getElementById('clearSearchBtn');
            
            this.chatHistorySearch.addEventListener('input', (e) => {
                const searchValue = e.target.value;
                this.filterChatHistory(searchValue);
                
                // Toggle clear button visibility
                if (clearSearchBtn) {
                    clearSearchBtn.style.display = searchValue.trim() ? 'flex' : 'none';
                }
            });
            
            // Add clear button functionality
            if (clearSearchBtn) {
                clearSearchBtn.addEventListener('click', () => {
                    if (this.chatHistorySearch) {
                        this.chatHistorySearch.value = '';
                        this.chatHistorySearch.focus();
                        this.filterChatHistory('');
                        clearSearchBtn.style.display = 'none';
                    }
                });
            }
        }
        
        // Set up sync button click handler
        const syncButton = document.getElementById('syncButton');
        if (syncButton) {
            syncButton.addEventListener('click', () => this.syncChatHistory());
        }
        
    // Add event delegation for command links in messages
        if (this.chatMessages) {
            this.chatMessages.addEventListener('click', (e) => {
                // Check if the clicked element is a command link
                const commandLink = e.target.closest('.command-link');
                if (commandLink) {
                    e.preventDefault();
                    const command = commandLink.getAttribute('data-command');
                    if (command) {
                        // Add visual feedback for the click
                        commandLink.classList.add('command-executing');
                        setTimeout(() => {
                            commandLink.classList.remove('command-executing');
                        }, 1000);
                        
                        // Set the command in the input field
                        if (this.chatInput) {
                            this.chatInput.value = `/${command}`;
                            this.chatInput.focus();
                        }
                        // Process the command
                        this.processCommand(`/${command}`);
                    }
                }
            });
        }

        // Sync button
        if (this.syncButton) {
            this.syncButton.addEventListener('click', () => this.syncChatHistory());
        }
    }
      /**
     * Load chat history from server or localStorage
     */
    loadChatHistory() {
        // First try to load from server if user is logged in
        if (this.isUserLoggedIn && this.userId) {
            console.log('Loading chat history from server for user:', this.userId);
            fetch('/api/user-chats', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.chats && data.chats.length > 0) {
                    console.log('Server chat history loaded:', data.chats.length, 'conversations');
                    
                    // Update local storage with server data
                    localStorage.setItem('unifiedChatHistory', JSON.stringify(data.chats));
                    
                    // Load conversations into the sidebar
                    this.updateChatHistorySidebar(data.chats);
                          // Create a new chat session instead of loading the most recent conversation
                    this.createNewChatSession();
                } else {
                    // Fall back to localStorage if no server data
                    this.loadLocalChatHistory(true); // Pass true to indicate we want a new chat
                }
            })
            .catch(error => {
                console.error('Error loading server chat history:', error);
                // Fall back to localStorage
                this.loadLocalChatHistory();
            });
        } else {
            // User not logged in, use localStorage
            this.loadLocalChatHistory(true); // Always create a new chat session on app load
        }
    }
      /**
     * Load chat history from localStorage as fallback
     * @param {boolean} createNew - Whether to create a new chat session instead of loading the most recent
     */
    loadLocalChatHistory(createNew = false) {
        console.log('Loading chat history from localStorage, createNew:', createNew);
        const savedHistory = localStorage.getItem('unifiedChatHistory');
        
        if (savedHistory) {
            try {
                const history = JSON.parse(savedHistory);
                
                // Load chat conversations into the sidebar
                this.updateChatHistorySidebar(history);
                
                // Create a new chat session or load most recent conversation if available
                if (createNew) {
                    this.createNewChatSession();
                } else if (history.length > 0) {
                    this.loadChatSession(history[0].id);
                }
            } catch (error) {
                console.error('Error loading chat history from localStorage:', error);
            }
        }
        
        // If no history was loaded, display welcome message
        if (this.chatMessages && this.chatMessages.children.length === 0) {
            this.showWelcomeMessage();
        }
    }
      /**
     * Show welcome message in the chat
     */    showWelcomeMessage() {
        // Clear chat first
        this.chatMessages.innerHTML = '';
        
        // Get time of day for personalized greeting
        const hour = new Date().getHours();
        let greeting = "Hello";
        let greetingIcon = "✨";
        let timeClass = "default-time";
        
        if (hour < 12) {
            greeting = "Good morning";
            greetingIcon = "🌅";
            timeClass = "morning-time";
        } else if (hour < 18) {
            greeting = "Good afternoon";
            greetingIcon = "☀️";
            timeClass = "afternoon-time";
        } else {
            greeting = "Good evening";
            greetingIcon = "🌙";
            timeClass = "evening-time";
        }
        
        // Get day of week for even more personalization
        const dayOfWeek = new Date().getDay();
        let dayMessage = "";
        
        if (dayOfWeek === 1) {
            dayMessage = "Let's make this Monday productive!";
        } else if (dayOfWeek === 5) {
            dayMessage = "Happy Friday! Let's finish the week strong!";
        } else if (dayOfWeek === 0 || dayOfWeek === 6) {
            dayMessage = "Hope you're having a great weekend!";
        }
        
        // Add welcome message
        const welcomeMsg = document.createElement('div');
        welcomeMsg.className = 'bot-message message';
        welcomeMsg.innerHTML = `
            <div class="message-bubble welcome-message ${timeClass}">
                <h2>${greetingIcon} ${greeting} and welcome to LightYearAI! ${greetingIcon}</h2>
                ${dayMessage ? `<p class="day-message">${dayMessage}</p>` : ''}                <p>I'm your personal AI assistant ready to help with whatever you need today. Let's make something amazing together!</p>
                <p><strong>📁 File Management:</strong> You can upload files using the upload button, and I'll remember them for future conversations. Files will only be used when you specifically ask for them. Type "list files" to see your uploaded files, or mention a file by name (like "please use report.pdf") to use it in our conversation.</p>
                  <div class="command-section">
                    <h3>🚀 Try these powerful commands:</h3>
                    <div class="command-grid">
                        <div class="command-card">
                            <a href="#" class="command-link featured" data-command="study" title="Ask questions about homework, get explanations for concepts, and receive help with studying">
                                <span class="command-icon">📚</span>
                                <span class="command-name"><strong>/study</strong></span>
                                <span class="command-desc">Homework help & learning</span>
                            </a>
                        </div>
                        <div class="command-card">
                            <a href="#" class="command-link featured" data-command="proofread" title="Check your text for grammar errors, improve writing style, and get suggestions for better phrasing">
                                <span class="command-icon">✍️</span>
                                <span class="command-name"><strong>/proofread</strong></span>
                                <span class="command-desc">Perfect your writing</span>
                            </a>
                        </div>
                        <div class="command-card">
                            <a href="#" class="command-link featured" data-command="entertainment" title="Discuss movies, TV shows, music, books, and games with personalized recommendations">
                                <span class="command-icon">🎮</span>
                                <span class="command-name"><strong>/entertainment</strong></span>
                                <span class="command-desc">Movies, music & more</span>
                            </a>
                        </div>
                        <div class="command-card">
                            <a href="#" class="command-link featured" data-command="excel" title="Generate Excel spreadsheets from natural language descriptions, with formulas and formatting">
                                <span class="command-icon">📊</span>
                                <span class="command-name"><strong>/excel</strong></span>
                                <span class="command-desc">Create spreadsheets</span>
                            </a>
                        </div>
                        <div class="command-card">
                            <a href="#" class="command-link featured" data-command="presentation" title="Create professional presentation slides with content, formatting, and design elements">
                                <span class="command-icon">🎯</span>
                                <span class="command-name"><strong>/presentation</strong></span>
                                <span class="command-desc">Design slide decks</span>
                            </a>
                        </div>
                        <div class="command-card">
                            <a href="#" class="command-link featured" data-command="translate" title="Translate text between multiple languages with accurate preservation of meaning">
                                <span class="command-icon">🌐</span>
                                <span class="command-name"><strong>/translate</strong></span>
                                <span class="command-desc">Language translation</span>
                            </a>
                        </div>
                        <div class="command-card">
                            <a href="#" class="command-link featured" data-command="summarize" title="Create concise summaries of long documents while preserving key information">
                                <span class="command-icon">📝</span>
                                <span class="command-name"><strong>/summarize</strong></span>
                                <span class="command-desc">Summarize documents</span>
                            </a>
                        </div>
                        <div class="command-card">
                            <a href="#" class="command-link featured" data-command="help" title="Display a list of available commands and their descriptions">
                                <span class="command-icon">❓</span>
                                <span class="command-name"><strong>/help</strong></span>
                                <span class="command-desc">See all commands</span>
                            </a>
                        </div>
                    </div>
                </div>
                
                <p class="welcome-prompt">What would you like to work on today? You can click any command above, type a slash command like <strong>/study</strong>, or simply ask in natural language like <strong>"help me with my homework"</strong>!</p>
            </div>
        `;
        this.chatMessages.appendChild(welcomeMsg);
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    /**
     * Handle input changes in the chat input field (detect commands)
     */
    handleChatInputChange(e) {
        const { value } = e.target;
        if (value.startsWith('/')) {
            const query = value.slice(1).toLowerCase();
            const cmds = [
                { name: 'study', emoji: '📚', description: 'Get help with homework and studying', tooltip: 'Ask questions about homework, get explanations for concepts, and receive help with studying' },
                { name: 'proofread', emoji: '✍️', description: 'Check grammar and improve writing', tooltip: 'Check your text for grammar errors, improve writing style, and get suggestions for better phrasing' },
                { name: 'entertainment', emoji: '🎮', description: 'Chat about movies, music, etc.', tooltip: 'Discuss movies, TV shows, music, books, and games with personalized recommendations' },
                { name: 'excel', emoji: '📊', description: 'Generate Excel spreadsheets', tooltip: 'Generate Excel spreadsheets from natural language descriptions, with formulas and formatting' },
                { name: 'presentation', emoji: '🎯', description: 'Create presentation slides', tooltip: 'Create professional presentation slides with content, formatting, and design elements' },
                { name: 'translate', emoji: '🌐', description: 'Translate text between languages', tooltip: 'Translate text between multiple languages with accurate preservation of meaning' },
                { name: 'summarize', emoji: '📝', description: 'Summarize long text or documents', tooltip: 'Create concise summaries of long documents while preserving key information' },
                { name: 'clear', emoji: '🧹', description: 'Clear the current chat', tooltip: 'Reset the conversation and start fresh while keeping your session' },
                { name: 'help', emoji: '❓', description: 'Show this help message', tooltip: 'Display this list of available commands and their descriptions' }
            ];
        } else {
            if (value.trim() === '') {
                // Handle empty input case
            }
        }
    }

    /**
     * Display command suggestions dropdown
     */
    showCommandSuggestions(list) {
        if (!this.commandSuggestions) {
            return;
        }
        
        this.commandSuggestions.innerHTML = '';
        if (!list.length) {
            this.commandSuggestions.style.display = 'none';
            return;
        }
          list.forEach(cmd => {
            const item = document.createElement('div');
            item.className = 'command-item';
            item.title = cmd.tooltip || cmd.description;
            item.innerHTML = `<span class="cmd-icon">▶</span><strong>/${cmd.name}</strong> ${cmd.emoji} - ${cmd.description}`;
            item.addEventListener('click', () => {
                this.chatInput.value = `/${cmd.name} `;
                this.chatInput.focus();
                this.commandSuggestions.style.display = 'none';
            });
            this.commandSuggestions.appendChild(item);
        });
        
        this.commandSuggestions.style.display = 'block';
    }    /**
     * Handle chat form submission
     */
    handleChatSubmit() {
        if (this.isProcessing) {
            return;
        }
        
        const text = this.chatInput.value.trim();
        if (!text) {
            return;
        }
        
        // Check if this is a slash command
        if (text.startsWith('/')) {
            this.processCommand(text);
        } else {
            // Check for natural language commands
            const detectedCommand = this.detectNaturalLanguageCommand(text);
            
            if (detectedCommand) {
                // Show what command was detected (for user feedback)
                const feedbackMsg = document.createElement('div');
                feedbackMsg.className = 'system-message message';
                feedbackMsg.innerHTML = `
                    <div class="message-bubble command-detection">
                        <p><i>Using command: <strong>/${detectedCommand.command}</strong></i></p>
                    </div>
                `;
                this.chatMessages.appendChild(feedbackMsg);
                this.scrollToBottom();
                
                // Add the original user message
                this.addMessage(text, true);
                
                // Process the command with the original text as arguments
                this.processCommand(`/${detectedCommand.command} ${detectedCommand.args}`);
            } else {
                this.sendChatMessage(text);
            }
        }
        
        // Clear input and reset height
        this.chatInput.value = '';
        this.chatInput.style.height = 'auto';
    }
      /**
     * Process slash commands
     */
    processCommand(commandText) {
        const parts = commandText.trim().split(' ');
        const command = parts[0].substring(1).toLowerCase(); // Remove the slash
        const args = parts.slice(1).join(' ');
        const isNaturalLanguageCommand = commandText.includes(`/${command} ${command}`); // Detect if this is from a natural language command
        
        // Create timestamp for this command sequence
        const timestamp = new Date().toISOString();
        
        // Save the user command to message history first with the timestamp
        this.messageHistory.push({
            role: 'user',
            content: commandText,
            timestamp: timestamp,
            isCommand: true
        });
        
        // List of all available commands
        const availableCommands = [
            { name: 'study', emoji: '📚', description: 'Get help with homework and studying' },
            { name: 'proofread', emoji: '✍️', description: 'Check grammar and improve writing' },
            { name: 'entertainment', emoji: '🎮', description: 'Chat about movies, music, etc.' },
            { name: 'excel', emoji: '📊', description: 'Generate Excel spreadsheets' },
            { name: 'presentation', emoji: '🎯', description: 'Create presentation slides' },
            { name: 'translate', emoji: '🌐', description: 'Translate text between languages' },
            { name: 'summarize', emoji: '📝', description: 'Summarize long text or documents' },
            { name: 'clear', emoji: '🧹', description: 'Clear the current chat' },
            { name: 'help', emoji: '❓', description: 'Show this help message' }
        ];
        
        // Handle different commands
        switch(command) {
            case 'study':
                this.activateModule('study', args, timestamp);
                break;
            case 'proofread':
                this.activateModule('proofread', args, timestamp);
                break;
            case 'entertainment':
                this.activateModule('entertainment', args, timestamp);
                break;
            case 'excel':
                this.activateModule('excel', args, timestamp);
                break;
            case 'presentation':
                this.activateModule('presentation', args, timestamp);
                break;            case 'translate':
                // Check if the user specified languages in the command
                let sourceLanguage = 'auto';
                let targetLanguage = 'english';
                
                // Parse language specifications from command
                // Examples: /translate from Polish to Azerbaijani
                //           /translate to Spanish
                const fromMatch = args.match(/from\s+([a-zA-Z]+)/i);
                const toMatch = args.match(/(?:to|into)\s+([a-zA-Z]+)/i);
                
                if (fromMatch) {
                    sourceLanguage = fromMatch[1];
                }
                
                if (toMatch) {
                    targetLanguage = toMatch[1];
                }
                
                // Store the language settings in contextData
                this.contextData.sourceLanguage = sourceLanguage;
                this.contextData.targetLanguage = targetLanguage;
                
                this.activateModule('translate', args, timestamp);
                break;
            case 'summarize':
                this.activateModule('summarize', args, timestamp);
                break;
            case 'help':
                this.showHelpMessage(timestamp);
                break;
            case 'clear':
                this.clearChat();
                break;
            default:
                // Find similar commands to suggest
                const suggestedCommands = this.findSimilarCommands(command, availableCommands);
                
                // Create fallback message with suggestions
                let fallbackMessage = `<div class="command-not-found">
                    <p><strong>Command '/${command}' not recognized.</strong></p>`;
                
                // Add suggestions if we have any
                if (suggestedCommands.length > 0) {
                    fallbackMessage += `<p>Did you mean:</p>
                    <div class="command-suggestions">`;
                    
                    suggestedCommands.forEach(cmd => {
                        fallbackMessage += `<button class="suggested-command" data-command="${cmd.name}">
                            <span class="cmd-icon">${cmd.emoji}</span>
                            <span class="cmd-name">/${cmd.name}</span>
                        </button>`;
                    });
                    
                    fallbackMessage += `</div>`;
                }
                
                // Always add help suggestion
                fallbackMessage += `<p>Type <a href="#" class="command-link" data-command="help">/help</a> to see all available commands.</p>
                </div>`;
                
                // Add the message to UI
                this.addMessage(fallbackMessage, false);
                
                // Add click handlers for suggested commands
                setTimeout(() => {
                    const suggestedBtns = document.querySelectorAll('.suggested-command');
                    suggestedBtns.forEach(btn => {
                        btn.addEventListener('click', () => {
                            const cmdName = btn.getAttribute('data-command');
                            if (cmdName) {
                                this.chatInput.value = `/${cmdName}`;
                                this.handleChatSubmit();
                            }
                        });
                    });
                }, 50);
                
                // Save to history
                this.messageHistory.push({
                    role: 'assistant',
                    content: `Command '/${command}' not recognized.`,
                    timestamp: timestamp
                });
        }
        
        // Save chat to localStorage
        this.saveCurrentChat();
    }
    
    /**
     * Find similar commands based on input
     */
    findSimilarCommands(input, availableCommands) {
        // Calculate similarity scores using a simple algorithm
        const scoredCommands = availableCommands.map(cmd => {
            // Simple similarity metric: count matching characters in sequence
            let score = 0;
            let inputChars = input.toLowerCase().split('');
            let cmdChars = cmd.name.toLowerCase().split('');
            
            // Check for partial matches (beginning of command)
            if (cmd.name.startsWith(input)) {
                score += 10; // High score for prefix matches
            }
            
            // Check for contained matches
            if (cmd.name.includes(input)) {
                score += 5;
            }
            
            // Count matching characters
            for (let i = 0; i < inputChars.length; i++) {
                if (cmdChars.includes(inputChars[i])) {
                    score += 1;
                    // Remove the matched character to avoid double-counting
                    cmdChars.splice(cmdChars.indexOf(inputChars[i]), 1);
                }
            }
            
            // Longer commands should have a slight penalty
            score /= Math.sqrt(Math.max(1, cmd.name.length - input.length));
            
            return { ...cmd, score };
        });
        
        // Sort by score (highest first) and take top 3
        return scoredCommands
            .sort((a, b) => b.score - a.score)
            .slice(0, 3);
    }
    
    /**
     * Detect natural language commands from user input
     * Returns the command and arguments if a command is detected, null otherwise
     */
    detectNaturalLanguageCommand(text) {
        // Clean and normalize the input text
        const normalizedText = text.toLowerCase().trim();
        
        // Define natural language patterns for each command
        const commandPatterns = [
            {
                command: 'study',
                patterns: [
                    /^(?:can you |please |)(?:help me |)(?:with |)(?:my |)(?:homework|studying|assignment|problem|question|math|science|history|learn|understand)/i,
                    /^(?:i need help |i'm struggling |i am struggling |)(?:with |)(?:my |)(?:homework|studying|assignment|problem|question)/i,
                    /^explain (?:to me |)(?:how|what|why|when|where|who|which)/i,
                    /^(?:can you |)(?:teach me|explain|help me understand)/i
                ]
            },
            {
                command: 'proofread',
                patterns: [
                    /^(?:can you |please |)(?:proofread|check|review|edit|correct|fix|improve) (?:my |this |the |)(?:text|writing|grammar|spelling|essay|paper|document)/i,
                    /^(?:can you |please |)(?:help me |)(?:with |)(?:my |)(?:writing|grammar|spelling)/i,
                    /^(?:check|correct|fix|improve) (?:the |my |this |)(?:grammar|spelling|text|writing|essay|document)/i,
                    /^(?:find|fix) (?:errors|mistakes|typos|issues) (?:in|with) (?:my|this|the) (?:text|writing|essay|document)/i
                ]
            },
            {
                command: 'entertainment',
                patterns: [
                    /^(?:let's |can we |)(?:talk|chat) about (?:movies|tv|shows|music|books|entertainment|games|series|films)/i,
                    /^(?:recommend|suggest)(?: me|) (?:a |some |)(?:movie|tv show|book|song|music|game)/i,
                    /^(?:what|which) (?:movie|show|book|song|music|game)/i,
                    /^(?:i'm|i am|i feel) (?:bored|looking for something to watch|looking for entertainment)/i
                ]
            },
            {
                command: 'excel',
                patterns: [
                    /^(?:can you |please |)(?:create|make|generate|build|design|produce) (?:an |a |)(?:excel|spreadsheet)/i,
                    /^(?:i need |i want |help me |)(?:to |)(?:create|make|build|design) (?:an |a |)(?:excel|spreadsheet)/i,
                    /^(?:can you |please |)(?:help me |)(?:with |)(?:excel|spreadsheet|data|calculation|formula|table)/i,
                    /^(?:excel |spreadsheet |)(?:for|to track|to calculate|to analyze)/i
                ]
            },
            {
                command: 'presentation',
                patterns: [
                    /^(?:can you |please |)(?:create|make|generate|build|design|produce) (?:a |)(?:presentation|slide|slides|slideshow|deck|powerpoint)/i,
                    /^(?:i need |i want |help me |)(?:to |)(?:create|make|build|design) (?:a |)(?:presentation|slide|slides|slideshow|deck|powerpoint)/i,
                    /^(?:can you |please |)(?:help me |)(?:with |)(?:my |a |)(?:presentation|slides|slideshow|powerpoint)/i,
                    /^(?:presentation|slides|powerpoint) (?:about|on|for) /i
                ]
            },
            {
                command: 'translate',
                patterns: [
                    /^(?:can you |please |)(?:translate|convert) (?:this|the following|text|sentence|paragraph|document)/i,
                    /^(?:how|what)(?:'s| is| does) (?:this|that|it) (?:say |written |mean |translated |)(?:in|to) (?:[a-z]+)/i,
                    /^(?:translate|convert) (?:from|to) ([a-z]+)/i,
                    /^(?:say|write) (?:this|the following|it) (?:in|to) ([a-z]+)/i
                ]
            },
            {
                command: 'summarize',
                patterns: [
                    /^(?:can you |please |)(?:summarize|summarise|sum up|condense|shorten|give me a summary of) (?:this|the|following|text|document|article|essay|paper)/i,
                    /^(?:i need |i want |give me |)(?:a |the |)(?:summary|brief|short version|tldr|overview|main points) (?:of|for|about)/i,
                    /^(?:what are |)(?:the |)(?:key|main|important) (?:points|ideas|concepts|takeaways|findings) (?:in|from|of)/i,
                    /^(?:tldr|too long didn't read|too long didnt read)/i
                ]
            },
            {
                command: 'clear',
                patterns: [
                    /^(?:can you |please |)(?:clear|reset|restart|clean|new) (?:the |this |our |)(?:chat|conversation|discussion|session)/i,
                    /^(?:let's |i want to |i would like to |can we |)(?:start |begin |)(?:over|again|fresh|new|afresh)/i,
                    /^(?:clear|reset|restart|clean) (?:everything|all)/i,
                    /^(?:start|begin) (?:a |)(?:new|fresh) (?:chat|conversation)/i
                ]
            },
            {
                command: 'help',
                patterns: [
                    /^(?:can you |please |)(?:show|tell|give) me (?:the |all |available |)(?:commands|options|features|help)/i,
                    /^(?:what|which) (?:commands|features|functions) (?:can you|do you|are) (?:do|use|have|support|available)/i,
                    /^(?:help|assistance|commands|options|menu|what can you do)/i,
                    /^(?:how do i|how can i|how to) (?:use|access|get to) (?:the |)(?:commands|features|options)/i
                ]
            }
        ];
        
        // Test all patterns and find the first match
        for (const commandPattern of commandPatterns) {
            for (const pattern of commandPattern.patterns) {
                if (pattern.test(normalizedText)) {
                    // Extract the arguments (everything after the matched command pattern)
                    let match = pattern.exec(normalizedText);
                    let args = normalizedText;
                    
                    // Return the detected command and the full text as arguments
                    return {
                        command: commandPattern.command,
                        args: args
                    };
                }
            }
        }
        
        // No natural language command detected
        return null;
    }
    
    /**
     * Activate a specific feature module
     */
    activateModule(moduleName, initialText = '', commandTimestamp = null) {
        // Set the active module
        this.activeModule = moduleName;
        
        // Use the provided timestamp or create a new one (slightly later than command timestamp to maintain order)
        const timestamp = commandTimestamp ? 
            new Date(new Date(commandTimestamp).getTime() + 1).toISOString() : 
            new Date().toISOString();
        
        // Add a system message showing the module activation
        let moduleMessage = '';
        
        switch(moduleName) {
            case 'study':
                moduleMessage = `<p>Switching to <strong>Study Mode</strong>. You can ask homework questions or get help understanding concepts.</p>`;
                break;
            case 'proofread':
                moduleMessage = `<p>Switching to <strong>Proofreading Mode</strong>. Paste text to check grammar and improve writing.</p>`;
                break;
            case 'entertainment':
                moduleMessage = `<p>Switching to <strong>Entertainment Mode</strong>. Let's chat about movies, music, books, or other entertainment topics!</p>`;
                break;
            case 'excel':
                moduleMessage = `<p>Switching to <strong>Excel Generator</strong>. Describe the spreadsheet you want to create.</p>`;
                break;
            case 'presentation':
                moduleMessage = `<p>Switching to <strong>Presentation Builder</strong>. Describe the presentation you want to create.</p>`;
                break;            case 'translate':
                // Get the source and target languages from contextData
                const sourceLanguage = this.contextData.sourceLanguage || 'auto';
                const targetLanguage = this.contextData.targetLanguage || 'English';
                
                // Create a more informative activation message
                const sourceText = sourceLanguage === 'auto' ? 
                    'auto-detect the source language' : 
                    `translate from <strong>${sourceLanguage}</strong>`;
                
                moduleMessage = `
                <p>Switching to <strong>Translation Mode</strong>.</p>
                <p>I'll ${sourceText} to <strong>${targetLanguage}</strong>.</p>
                <p>Simply enter the text you want to translate.</p>
                <p>You can change languages anytime by typing:<br>
                <code>to [language]</code> or <code>from [language] to [language]</code></p>
                `;
                break;
            case 'summarize':
                moduleMessage = `<p>Switching to <strong>Summarize Mode</strong>. Paste the text you want to summarize.</p>`;
                break;
        }
        
        this.addMessage(moduleMessage, false, true);
        
        // Save system message to history with the timestamp
        this.messageHistory.push({
            role: 'system',
            content: moduleMessage,
            timestamp: timestamp,
            module: moduleName
        });
        
        // If initial text was provided, process it right away
        // We'll use a slightly later timestamp for this message to ensure proper ordering
        if (initialText) {
            // Small delay to ensure this message comes after the system message
            const messageTimestamp = commandTimestamp ? 
                new Date(new Date(commandTimestamp).getTime() + 2).toISOString() : 
                new Date(new Date().getTime() + 1).toISOString();
                
            this.sendModuleMessage(initialText, messageTimestamp);
        }
    }    /**
     * Send a regular chat message (when no module is active)
     */    sendChatMessage(text) {
        // If a module is active, route to that module's handler
        if (this.activeModule) {
            // Special handling for translation mode language changes
            if (this.activeModule === 'translate') {
                // Check if user is changing languages
                const fromMatch = text.match(/^(?:from|translate from)\s+([a-zA-Z]+)(?:\s+to\s+([a-zA-Z]+))?$/i);
                const toMatch = text.match(/^(?:to|into|translate to|translate into)\s+([a-zA-Z]+)$/i);
                
                if (fromMatch || toMatch) {
                    if (fromMatch) {
                        this.contextData.sourceLanguage = fromMatch[1];
                        if (fromMatch[2]) {
                            this.contextData.targetLanguage = fromMatch[2];
                        }
                    } else if (toMatch) {
                        this.contextData.targetLanguage = toMatch[1];
                    }
                    
                    // Confirm the language change
                    const sourceText = this.contextData.sourceLanguage === 'auto' ? 
                        'Auto-detect' : 
                        `<strong>${this.contextData.sourceLanguage}</strong>`;
                    
                    const confirmationMsg = `
                    <p>Updated translation settings:</p>
                    <p>Source language: ${sourceText}</p>
                    <p>Target language: <strong>${this.contextData.targetLanguage}</strong></p>
                    <p>Enter text to translate.</p>
                    `;
                    
                    this.addMessage(confirmationMsg, false);
                    return;
                }
            }
            
            this.sendModuleMessage(text);
            return;
        }
        
        // Check for specific file related commands
        if (text.toLowerCase().trim() === 'list files' || text.toLowerCase().trim() === 'show files') {
            this.showAvailableFiles();
            return;
        }
        
        // Check if the message mentions a file
        const mentionedFilename = this.checkForFileMentions(text);
        if (mentionedFilename) {
            // Add file to the context for this conversation
            if (this.addFileToContext(mentionedFilename)) {
                // Show file context indicator
                const fileContext = this.createFileContextIndicator(mentionedFilename);
                this.chatMessages.appendChild(fileContext);
                this.scrollToBottom();
            }
        }
        
        // Add user message to UI
        this.addMessage(text, true);
        
        // Show typing indicator
        const typingIndicator = this.showTypingIndicator();
        
        // Make API call
        this.isProcessing = true;
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                session_id: this.sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            this.hideTypingIndicator(typingIndicator);
            this.isProcessing = false;
              // Update file state if the response contains file information
            if (data.hasFile && data.fileName) {
                console.log('File detected in response:', data.fileName, 'ID:', data.fileId || 'unknown');
                
                // Update our context data to reflect the file without showing a redundant indicator
                if (!this.contextData.uploadedFile || this.contextData.uploadedFile.filename !== data.fileName) {
                    this.contextData.uploadedFile = {
                        filename: data.fileName,
                        file_id: data.fileId
                    };
                    console.log("File context updated from response:", this.contextData.uploadedFile);
                    
                    // Store in fileHistory for future reference
                    if (!this.fileHistory[data.fileName]) {
                        this.fileHistory[data.fileName] = {
                            filename: data.fileName,
                            file_id: data.fileId,
                            timestamp: new Date().toISOString()
                        };
                    }
                }
            }
            
            // Add bot response
            this.addMessage(data.response, false);
            
            // Save to message history with timestamps
            const timestamp = new Date().toISOString();
            this.messageHistory.push({
                role: 'user',
                content: text,
                timestamp: timestamp
            });
            this.messageHistory.push({
                role: 'assistant',
                content: data.response,
                timestamp: timestamp
            });
            
            // Save chat to localStorage
            this.saveCurrentChat();
        })
        .catch(error => {
            console.error('Error:', error);
            this.hideTypingIndicator(typingIndicator);
            this.isProcessing = false;
            this.addMessage('Sorry, I encountered an error. Please try again.', false);
        });
    }    /**
     * Send a message to the active module
     */    sendModuleMessage(text, commandTimestamp = null) {
        // Check for specific file related commands
        if (text.toLowerCase().trim() === 'list files' || text.toLowerCase().trim() === 'show files') {
            this.showAvailableFiles();
            return;
        }
        
        // Check if the message mentions a file
        const mentionedFilename = this.checkForFileMentions(text);
        if (mentionedFilename) {
            // Add file to the context for this conversation
            if (this.addFileToContext(mentionedFilename)) {
                // Show file context indicator
                const fileContext = this.createFileContextIndicator(mentionedFilename);
                this.chatMessages.appendChild(fileContext);
                this.scrollToBottom();
            }
        }
        
        // Add user message to UI
        this.addMessage(text, true);
        
        // Show typing indicator
        const typingIndicator = this.showTypingIndicator();
        
        // Prepare the endpoint based on the active module
        let endpoint = '/api/chat'; // Default endpoint
        let payload = {
            message: text,
            session_id: this.sessionId
        };switch(this.activeModule) {
            case 'study':                
                endpoint = '/study/chat';
                
                // Log file status before building payload
                console.log('File status check:', {
                    hasUploadedFile: !!this.contextData.uploadedFile,
                    fileId: this.contextData.uploadedFile?.file_id,
                    hasContent: !!this.contextData.pdfContent,
                    contentLength: this.contextData.pdfContent ? this.contextData.pdfContent.length : 0
                });
                
                // Explicitly include hasFile and hasFileId flags in the actual payload
                payload = {
                    message: text,
                    pdfContent: this.contextData.pdfContent || null,
                    fileId: this.contextData.uploadedFile?.file_id || null,
                    hasFile: !!(this.contextData.pdfContent || (this.contextData.uploadedFile && this.contextData.uploadedFile.file_id)),
                    hasFileId: !!this.contextData.uploadedFile?.file_id,
                    sessionId: this.sessionId
                };
                
                // Add detailed debug log
                console.log('Study request payload:', JSON.stringify({
                    message: text.substring(0, 50) + '...',
                    hasContent: !!this.contextData.pdfContent,
                    contentLength: this.contextData.pdfContent ? this.contextData.pdfContent.length : 0,
                    hasFileId: !!this.contextData.uploadedFile?.file_id,
                    fileId: this.contextData.uploadedFile?.file_id || null,
                    fileInfo: this.contextData.uploadedFile ? {
                        filename: this.contextData.uploadedFile.filename
                    } : null
                }));
                break;
            case 'proofread':
                endpoint = '/proofread/text';
                payload = { text: text };
                break;
            case 'entertainment':
                endpoint = '/entertainment/chat';
                payload = { 
                    message: text,
                    category: this.contextData.category || 'all'
                };
                break;            case 'excel':
                endpoint = '/generate_excel_crew';
                payload = { 
                    prompt: text,
                    use_crew: true  // Enable CrewAI multi-agent system
                };
                break;case 'presentation':
                endpoint = '/api/create-presentation';
                
                // Debug message to help troubleshoot
                console.log("Creating presentation with text:", text.substring(0, 100) + "...");
                
                // Create FormData for presentation creation since the API expects form data, not JSON
                const formData = new FormData();
                formData.append('text', text);
                formData.append('title', 'Presentation'); // Default title
                formData.append('tone', 'professional'); // Default tone
                
                // Special case for presentation - we're sending FormData instead of JSON
                // Don't try to JSON.stringify this payload
                this.sendFormData = true;
                payload = formData;
                
                console.log("FormData created with fields:", 
                    Array.from(formData.keys()).map(key => `${key}: ${formData.get(key).toString().substring(0, 30)}...`));
                break;
            case 'translate':
                endpoint = '/api/translate';
                
                // Extract source and target languages from context if available
                const sourceLanguage = this.contextData.sourceLanguage || 'auto';
                const targetLanguage = this.contextData.targetLanguage || 'english';
                
                payload = {
                    text: text,
                    source_language: sourceLanguage,
                    target_language: targetLanguage,
                    session_id: this.sessionId
                };
                
                console.log("Translation request:", {
                    text: text.substring(0, 30) + '...',
                    source: sourceLanguage,
                    target: targetLanguage
                });
                break;
            // Other modules would go here
        }
        
        // Use the provided timestamp or generate a new one
        const messageTimestamp = commandTimestamp || new Date().toISOString();
        
        // Save to message history with timestamp (storing before API call to maintain order)
        this.messageHistory.push({
            role: 'user',
            content: text,
            module: this.activeModule,
            timestamp: messageTimestamp
        });        // Make API call
        this.isProcessing = true;
        
        // Set up request options conditionally based on payload type
        const requestOptions = {
            method: 'POST',
            credentials: 'same-origin' // Important: ensure cookies are sent
        };
        
        // Check if we need to send form data (for presentations) or JSON (for everything else)
        if (this.sendFormData && payload instanceof FormData) {
            // For FormData, don't set Content-Type header (browser sets it with boundary)
            requestOptions.body = payload;
            
            console.log("Sending FormData request to:", endpoint);
            
            // Reset the flag
            this.sendFormData = false;
        } else {
            // For JSON payloads (most requests)
            requestOptions.headers = {
                'Content-Type': 'application/json'
            };
            requestOptions.body = JSON.stringify(payload);
            
            console.log("Sending JSON request to:", endpoint);
        }
        
        fetch(endpoint, requestOptions)        .then(response => {
            // Check if the response is OK first
            if (!response.ok) {
                // Try to extract error message if possible
                return response.json().then(errorData => {
                    throw new Error(errorData.error || `Server returned ${response.status}: ${response.statusText}`);
                }).catch(err => {
                    // If we can't parse the error response
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide typing indicator
            this.hideTypingIndicator(typingIndicator);
            this.isProcessing = false;
            
            // Debug output for the presentation response
            if (this.activeModule === 'presentation') {
                console.log('Presentation response data:', data);
                
                // Check if we have the necessary download URL
                if (!data.download_url && !data.presentation_url) {
                    console.error('Missing download_url or presentation_url in response:', data);
                }
            }
            
            // Update file state if the response contains file information
            if (this.activeModule === 'study' && data.hasFile && data.fileName) {
                console.log('File detected in response:', data.fileName, 'ID:', data.fileId || 'unknown');
                
                // Make sure we update our context data to reflect the file without showing a redundant indicator
                if (!this.contextData.uploadedFile || this.contextData.uploadedFile.filename !== data.fileName) {
                    this.contextData.uploadedFile = {
                        filename: data.fileName,
                        file_id: data.fileId
                    };
                    console.log("File context updated from response:", this.contextData.uploadedFile);
                    
                    // Store in fileHistory for future reference
                    if (!this.fileHistory[data.fileName]) {
                        this.fileHistory[data.fileName] = {
                            filename: data.fileName,
                            file_id: data.fileId,
                            timestamp: new Date().toISOString()
                        };
                    }
                }
            }
            
            // Process response based on module with a slightly later timestamp
            // This ensures the response appears after the user message
            const responseTimestamp = new Date(new Date(messageTimestamp).getTime() + 1).toISOString();
            this.handleModuleResponse(data, responseTimestamp);
            
            // Save chat to localStorage
            this.saveCurrentChat();
        })        .catch(error => {
            console.error('Error in API call:', error);
            this.hideTypingIndicator(typingIndicator);
            this.isProcessing = false;
            
            // Custom error handling for presentation errors
            if (this.activeModule === 'presentation') {
                const errorMsg = `
                <p>Sorry, I encountered an error while creating your presentation:</p>
                <div class="error-details">
                    <p>${error.message || 'Unknown error'}</p>
                </div>
                <p>Please check your request and try again with these suggestions:</p>
                <ul>
                    <li>Use shorter, more specific descriptions</li>
                    <li>Try a different topic</li>
                    <li>Wait a few moments and try again</li>
                </ul>`;
                this.addMessage(errorMsg, false);
            } else {
                // Generic error for other modules
                this.addMessage('Sorry, I encountered an error with this module. Please try again or try a different command.', false);
            }
        });
    }
    
    /**
     * Handle module-specific responses
     */
    handleModuleResponse(data, responseTimestamp = null) {
        // Use provided timestamp or generate a new one
        const timestamp = responseTimestamp || new Date().toISOString();
        
        switch(this.activeModule) {
            case 'study':
                // Standard chat response
                this.addMessage(data.response, false);
                this.messageHistory.push({
                    role: 'assistant',
                    content: data.response,
                    module: 'study',
                    timestamp: timestamp
                });
                break;
                
            case 'proofread':
                // Handle proofread response with corrections
                let responseContent = `<p>I've proofread your text. Here are my corrections:</p>`;
                
                // Add corrections if there are any
                if (data.corrections && data.corrections.length > 0) {
                    responseContent += `<div class="corrections-list">`;
                    data.corrections.forEach(correction => {
                        responseContent += `
                            <div class="correction-item">
                                <div>
                                    <span class="original-text">${correction.original}</span> → 
                                    <span class="corrected-text">${correction.corrected}</span>
                                </div>
                                <div class="explanation">${correction.explanation || 'Grammar or spelling correction'}</div>
                            </div>
                        `;
                    });
                    responseContent += `</div>`;
                } else {
                    responseContent += `<p>No significant errors found in your text. Great job!</p>`;
                }
                
                // Add download link if available
                if (data.pdf_url) {
                    responseContent += `<p><a href="${data.pdf_url}" target="_blank" class="btn btn-primary btn-sm"><i class="fas fa-download me-1"></i> Download Corrected PDF</a></p>`;
                }
                
                this.addMessage(responseContent, false);
                this.messageHistory.push({
                    role: 'assistant',
                    content: responseContent,
                    module: 'proofread',
                    timestamp: timestamp,
                    metadata: {
                        corrections: data.corrections,
                        pdf_url: data.pdf_url
                    }
                });
                break;
                
            case 'entertainment':
                // Handle entertainment response with suggestions
                this.addMessage(data.response, false);
                
                // Add suggestion chips if provided
                if (data.suggestions && data.suggestions.length > 0) {
                    const suggestionsDiv = document.createElement('div');
                    suggestionsDiv.className = 'suggestion-chips';
                    
                    data.suggestions.forEach(suggestion => {
                        const chip = document.createElement('button');
                        chip.className = 'suggestion-chip';
                        chip.textContent = suggestion;
                        chip.addEventListener('click', () => {
                            this.chatInput.value = suggestion;
                            this.handleChatSubmit();
                        });
                        suggestionsDiv.appendChild(chip);
                    });
                    
                    const lastMessage = this.chatMessages.lastElementChild;
                    if (lastMessage) {
                        const messageBubble = lastMessage.querySelector('.message-bubble');
                        if (messageBubble) {
                            messageBubble.appendChild(suggestionsDiv);
                        }
                    }
                }
                
                this.messageHistory.push({
                    role: 'assistant',
                    content: data.response,
                    module: 'entertainment',
                    timestamp: timestamp,
                    metadata: {
                        suggestions: data.suggestions
                    }
                });
                break;
                  case 'excel':
                // Handle excel generation response
                let excelResponse = '<p>I\'ve generated an Excel spreadsheet based on your description.</p>';
                
                // Show generation method and quality information
                if (data.method === 'crewai') {
                    excelResponse += '<p><small class="text-success"><i class="fas fa-users me-1"></i><strong>Multi-Agent Enhanced:</strong> Generated using specialized AI agents for data analysis, Excel design, charts, and quality assurance.</small></p>';
                    if (data.quality_score) {
                        excelResponse += `<p><small class="text-info"><i class="fas fa-star me-1"></i><strong>Quality Score:</strong> ${data.quality_score}</small></p>`;
                    }
                    if (data.agent_details) {
                        excelResponse += '<p><small class="text-muted"><i class="fas fa-cogs me-1"></i><strong>Agent Details:</strong> ' + JSON.stringify(data.agent_details) + '</small></p>';
                    }
                } else if (data.method === 'fallback') {
                    excelResponse += '<p><small class="text-warning"><i class="fas fa-bolt me-1"></i><strong>Standard Method:</strong> Generated using the standard Excel generation system.</small></p>';
                    if (data.warning) {
                        excelResponse += `<p><small class="text-muted"><i class="fas fa-info-circle me-1"></i><strong>Note:</strong> ${data.warning}</small></p>`;
                    }
                }
                
                if (data.excel_url) {
                    excelResponse += `<p><a href="${data.excel_url}" target="_blank" class="btn btn-primary btn-sm"><i class="fas fa-file-excel me-1"></i> Download Excel File</a></p>`;
                }
                
                this.addMessage(excelResponse, false);
                this.messageHistory.push({
                    role: 'assistant',
                    content: excelResponse,
                    module: 'excel',
                    timestamp: timestamp,
                    metadata: {
                        excel_url: data.excel_url,
                        method: data.method,
                        quality_score: data.quality_score,
                        agent_details: data.agent_details
                    }
                });
                break;
                  case 'presentation':
                // Handle presentation generation response
                let presentationResponse = '<p>I\'ve created a presentation based on your description.</p>';
                  // Debug output to help identify what's actually in the response                console.log("Presentation response data:", JSON.stringify(data));
                
                // Check for URLs in multiple formats and locations with fallbacks
                const downloadUrl = data.download_url || data.presentation_url || '';
                const viewUrl = data.view_url || '';
                const filename = data.filename || '';
                
                // Additional logging for debugging the presentation URLs
                console.log("Download URL found:", downloadUrl);
                console.log("View URL found:", viewUrl);
                console.log("Filename found:", filename);
                
                // Extra debug logging for presentation URLs
                console.log("Presentation URLs extracted:", {
                    download: downloadUrl,
                    view: viewUrl,
                    filename: filename
                });
                
                if (downloadUrl) {
                    presentationResponse += `<p>
                        <a href="${downloadUrl}" target="_blank" class="btn btn-primary btn-sm me-2"><i class="fas fa-download me-1"></i> Download PowerPoint</a>`;
                    
                    // Only add view button if view_url is available
                    if (viewUrl) {
                        presentationResponse += `
                        <a href="${viewUrl}" target="_blank" class="btn btn-outline-primary btn-sm"><i class="fas fa-eye me-1"></i> Preview Presentation</a>`;
                    }
                    
                    presentationResponse += `</p>`;
                } else {
                    // Error message if no download URL found
                    console.error("No presentation download URL found in response:", data);
                    presentationResponse += `<p class="text-danger">
                        <i class="fas fa-exclamation-triangle me-1"></i> 
                        Sorry, there was an issue generating your presentation. Please try again with a different description.
                    </p>`;
                }
                
                this.addMessage(presentationResponse, false);
                this.messageHistory.push({
                    role: 'assistant',
                    content: presentationResponse,
                    module: 'presentation',
                    timestamp: timestamp,
                    metadata: {
                        download_url: downloadUrl,
                        view_url: viewUrl
                    }
                });
                break;
                  case 'translate':
                // Handle translation response
                let translationResponse = '';
                
                if (data.translated_text) {
                    translationResponse += `<div class="translation-result">
                        <div class="translated-text">${data.translated_text}</div>`;
                    
                    // If detected language is provided, show it
                    if (data.detected_language) {
                        translationResponse += `<div class="translation-details">
                            <span class="detected-language">Detected language: ${data.detected_language}</span>
                        </div>`;
                    }
                    
                    // If there are alternative translations, show them
                    if (data.alternatives && data.alternatives.length > 0) {
                        translationResponse += `<div class="alternative-translations">
                            <p class="alternatives-title">Alternative translations:</p>
                            <ul>`;
                        
                        data.alternatives.forEach(alt => {
                            translationResponse += `<li>${alt}</li>`;
                        });
                        
                        translationResponse += `</ul></div>`;
                    }
                    
                    translationResponse += `</div>`;
                } else {
                    translationResponse = "Sorry, I couldn't translate the text. Please try again with a different phrase.";
                }
                
                this.addMessage(translationResponse, false);
                this.messageHistory.push({
                    role: 'assistant',
                    content: translationResponse,
                    module: 'translate',
                    timestamp: timestamp,
                    metadata: {
                        source_language: data.detected_language || data.source_language,
                        target_language: data.target_language,
                        alternatives: data.alternatives
                    }
                });
                break;
                
            default:
                // Generic response handling
                this.addMessage(data.response || "The task was completed successfully.", false);
                this.messageHistory.push({
                    role: 'assistant',
                    content: data.response || "The task was completed successfully.",
                    module: this.activeModule,
                    timestamp: timestamp
                });
        }
    }
    
    /**
     * Add message to the chat UI
     */
    addMessage(content, isUser, isSystem = false) {
        if (!this.chatMessages) {
            return;
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'user-message message' : 'bot-message message';
        
        if (isSystem) {
            messageDiv.classList.add('system-message');
        }
        
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        messageBubble.innerHTML = content;
        
        // For non-user messages, add copy button
        if (!isUser) {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'btn btn-sm btn-outline-light copy-btn ms-2';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            copyBtn.title = 'Copy message';
            copyBtn.addEventListener('click', () => {
                // Extract text content without HTML tags
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = content;
                const textToCopy = tempDiv.textContent || tempDiv.innerText || '';
                
                navigator.clipboard.writeText(textToCopy.trim())
                    .then(() => {
                        copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                        setTimeout(() => {
                            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                        }, 2000);
                    });
            });
            messageBubble.appendChild(copyBtn);
        }
        
        messageDiv.appendChild(messageBubble);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.scrollToBottom();
        
        return messageDiv;
    }
    
    /**
     * Show typing indicator
     */
    showTypingIndicator() {
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
        this.chatMessages.appendChild(typingIndicator);
        this.scrollToBottom();
        return typingIndicator;
    }
    
    /**
     * Hide typing indicator
     */
    hideTypingIndicator(typingIndicator) {
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.parentNode.removeChild(typingIndicator);
        }
    }
    
    /**
     * Scroll chat to the bottom
     */
    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }
    
    /**
     * Toggle the chat sidebar open/closed
     */
    toggleSidebar() {
        if (this.chatSidebar) {
            this.chatSidebar.classList.toggle('open');
        }
    }    /**
     * Start a new chat session
     */    startNewChat() {
        // Create a new session ID
        this.sessionId = this.generateSessionId();
        
        // Reset message history
        this.messageHistory = [];
        
        // Reset active module
        this.activeModule = null;
        
        // Reset context data - specifically clear any active file
        // Important: we're intentionally starting with an empty contextData object
        // Files will only be added when explicitly mentioned by the user
        this.contextData = {};
        
        // Clear the search input if it exists
        if (this.chatHistorySearch) {
            this.chatHistorySearch.value = '';
        }
        
        // Add welcome message
        this.showWelcomeMessage();
        
        // Create a new chat session in history
        this.saveCurrentChat();
    }
    
    /**
     * Create a new chat session (used when app starts)
     */
    createNewChatSession() {
        // Use the existing startNewChat method to create a new session
        this.startNewChat();
        
        // Additional initialization specific to app startup can go here
        console.log('Created new chat session on app startup');
    }
      /**
     * Save current chat to server and localStorage
     */
    saveCurrentChat() {
        if (!this.sessionId || !this.messageHistory.length) {
            return;
        }
        
        // Get existing chat history
        let chatSessions = [];
        try {
            const saved = localStorage.getItem('unifiedChatHistory');
            if (saved) {
                chatSessions = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Error loading chat history for saving:', error);
        }
        
        // Get the first user message as title
        const userMessages = this.messageHistory.filter(msg => msg.role === 'user');
        let title = userMessages.length > 0 ? userMessages[0].content : 'New Chat';
        title = title.length > 30 ? title.substring(0, 27) + '...' : title;
        
        // Get the current timestamp
        const currentTime = new Date().toISOString();
        
        // Check if this chat already exists in history to preserve createdAt
        const existingChat = chatSessions.find(c => c.id === this.sessionId);
        const createdAt = existingChat ? existingChat.createdAt || currentTime : currentTime;
        
        // Create chat session object
        const chat = {
            id: this.sessionId,
            title: title,
            createdAt: createdAt,        // When the chat was first created
            lastMessageAt: currentTime,  // When the last message was sent
            messages: this.messageHistory,
            module: this.activeModule,
            contextData: this.contextData
        };
        
        // Update or add to chat sessions
        const existingIndex = chatSessions.findIndex(c => c.id === this.sessionId);
        if (existingIndex >= 0) {
            chatSessions[existingIndex] = chat;
        } else {
            chatSessions.unshift(chat); // Add to beginning of array
        }
        
        // Limit to 20 most recent chats
        chatSessions = chatSessions.slice(0, 20);
        
        // Save to localStorage
        localStorage.setItem('unifiedChatHistory', JSON.stringify(chatSessions));
        
        // Update sidebar
        this.updateChatHistorySidebar(chatSessions);
        
        // If user is logged in, also save to server
        if (this.isUserLoggedIn && this.userId) {
            console.log('Saving chat to server for user:', this.userId);
            fetch('/api/save-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    chat: chat,
                    userId: this.userId
                }),
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    console.error('Error saving chat to server:', data.error);
                }
            })
            .catch(error => {
                console.error('Error saving chat to server:', error);
            });
        }
    }
    
    /**
     * Update the chat history sidebar with saved chats
     */    updateChatHistorySidebar(chats) {
        if (!this.chatHistory) {
            return;
        }
        
        // Store all chats for filtering
        this.allChats = [...chats];
        
        // Check if there's a search term in the search box
        const searchTerm = this.chatHistorySearch ? this.chatHistorySearch.value.trim() : '';
        
        if (searchTerm) {
            // If there's a search term, apply filter
            this.filterChatHistory(searchTerm);
        } else {
            // Otherwise render all chats
            this.renderChatHistoryItems(chats);
        }
    }/**
     * Load a specific chat session
     */
    loadChatSession(chatId) {
        // Get chat history from localStorage
        try {
            const saved = localStorage.getItem('unifiedChatHistory');
            if (saved) {
                const chats = JSON.parse(saved);
                const chat = chats.find(c => c.id === chatId);
                
                if (chat) {
                    // Set session data
                    this.sessionId = chat.id;
                    this.messageHistory = [...chat.messages];
                    this.activeModule = chat.module || null;
                    this.contextData = chat.contextData || {};
                    
                    // Clear chat UI
                    this.chatMessages.innerHTML = '';
                    
                    // Sort messages by timestamp if available
                    let messagesToDisplay = [...chat.messages];
                    
                    // Add default timestamps to messages that don't have them
                    // Using indices as fallback to maintain original order for older chats
                    messagesToDisplay.forEach((msg, index) => {
                        if (!msg.timestamp) {
                            msg.timestamp = new Date(chat.timestamp || new Date()).toISOString();
                            // Add a small offset based on index to preserve original order for messages without timestamps
                            msg._displayOrder = index;
                        } else {
                            msg._displayOrder = 0;
                        }
                    });
                    
                    // Sort by timestamp first, then by _displayOrder for same timestamps
                    messagesToDisplay.sort((a, b) => {
                        // Compare timestamps first
                        const timeCompare = new Date(a.timestamp) - new Date(b.timestamp);
                        
                        // If timestamps are the same, use message _displayOrder (original order)
                        if (timeCompare === 0) {
                            return a._displayOrder - b._displayOrder;
                        }
                        
                        return timeCompare;
                    });
                    
                    // Add messages to UI in sorted order
                    messagesToDisplay.forEach(msg => {
                        const isUser = msg.role === 'user';
                        const isSystem = msg.role === 'system';
                        this.addMessage(msg.content, isUser, isSystem);
                    });
                    
                    // Update sidebar highlight
                    const chatItems = this.chatHistory.querySelectorAll('.chat-history-item');
                    chatItems.forEach(item => {
                        item.classList.remove('active');
                        if (item.dataset.id === chatId) {
                            item.classList.add('active');
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error loading chat session:', error);
        }
    }
      /**
     * Delete a chat session
     */
    deleteChat(chatId) {
        // Confirm deletion
        if (!confirm('Are you sure you want to delete this chat?')) {
            return;
        }
        
        // Get chat history from localStorage
        try {
            const saved = localStorage.getItem('unifiedChatHistory');
            if (saved) {
                let chats = JSON.parse(saved);
                
                // Remove the specified chat
                chats = chats.filter(c => c.id !== chatId);
                
                // Save updated history
                localStorage.setItem('unifiedChatHistory', JSON.stringify(chats));
                
                // Update sidebar
                this.updateChatHistorySidebar(chats);
                
                // If we deleted the current chat, start a new one
                if (chatId === this.sessionId) {
                    this.startNewChat();
                }
            }
            
            // If user is logged in, also delete from server
            if (this.isUserLoggedIn && this.userId) {
                console.log('Deleting chat from server:', chatId);
                fetch('/api/delete-chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        chatId: chatId,
                        userId: this.userId
                    }),
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        console.error('Error deleting chat from server:', data.error);
                    }
                })
                .catch(error => {
                    console.error('Error deleting chat from server:', error);
                });
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
        }
    }
      /**
     * Clear the current chat
     */
    clearChat() {
        // Reset the chat UI but keep the session ID
        this.messageHistory = [];
        this.activeModule = null;
        this.contextData = {}; // Clear file context
        
        // Show welcome message
        this.showWelcomeMessage();
        
        // Save empty chat
        this.saveCurrentChat();
    }
      /**
     * Show help message with available commands
     */
    showHelpMessage() {
        const helpContent = `
            <p>Available commands:</p>
            <ul>
                <li><a href="#" class="command-link" data-command="study" title="Ask questions about homework, get explanations for concepts, and receive help with studying"><strong>/study [question]</strong> 📚</a> - Get help with homework and studying</li>
                <li><a href="#" class="command-link" data-command="proofread" title="Check your text for grammar errors, improve writing style, and get suggestions for better phrasing"><strong>/proofread [text]</strong> ✍️</a> - Check grammar and improve writing</li>
                <li><a href="#" class="command-link" data-command="entertainment" title="Discuss movies, TV shows, music, books, and games with personalized recommendations"><strong>/entertainment [topic]</strong> 🎮</a> - Chat about movies, music, etc.</li>
                <li><a href="#" class="command-link" data-command="excel" title="Generate Excel spreadsheets from natural language descriptions, with formulas and formatting"><strong>/excel [description]</strong> 📊</a> - Generate Excel spreadsheets</li>
                <li><a href="#" class="command-link" data-command="presentation" title="Create professional presentation slides with content, formatting, and design elements"><strong>/presentation [description]</strong> 🎯</a> - Create presentation slides</li>
                <li><a href="#" class="command-link" data-command="translate" title="Translate text between multiple languages with accurate preservation of meaning"><strong>/translate [text]</strong> 🌐</a> - Translate text between languages</li>
                <li><a href="#" class="command-link" data-command="summarize" title="Create concise summaries of long documents while preserving key information"><strong>/summarize [text]</strong> 📝</a> - Summarize long text</li>
                <li><a href="#" class="command-link" data-command="clear" title="Reset the conversation and start fresh while keeping your session"><strong>/clear</strong> 🧹</a> - Clear the current chat</li>
                <li><a href="#" class="command-link" data-command="help" title="Display this list of available commands and their descriptions"><strong>/help</strong> ❓</a> - Show this help message</li>
            </ul>
            <div class="command-feature-callout">
                <h4>💡 Natural Language Support</h4>
                <p>You can also trigger commands using natural language! Examples:</p>
                <ul>
                    <li><strong>"Help me with my math homework"</strong> - Activates /study</li>
                    <li><strong>"Check my grammar in this text"</strong> - Activates /proofread</li>
                    <li><strong>"Recommend a movie to watch"</strong> - Activates /entertainment</li>
                    <li><strong>"Create a spreadsheet for tracking expenses"</strong> - Activates /excel</li>
                    <li><strong>"Make a presentation about climate change"</strong> - Activates /presentation</li>
                </ul>
            </div>
            <p>You can also use the sidebar to start a new chat or access previous conversations.</p>
        `;
        
        this.addMessage(helpContent, false, true);
    }

    /**
     * Show dialog for renaming a chat
     * @param {string} chatId - The ID of the chat to rename
     * @param {string} currentTitle - The current title of the chat
     */
    showRenameChatDialog(chatId, currentTitle) {
        // Remove any existing dialogs
        const existingDialog = document.querySelector('.rename-dialog-container');
        if (existingDialog) {
            existingDialog.remove();
        }
        
        // Create dialog container
        const dialogContainer = document.createElement('div');
        dialogContainer.className = 'rename-dialog-container';
        
        // Create dialog content
        dialogContainer.innerHTML = `
            <div class="rename-dialog">
                <h3>Rename Chat</h3>
                <form id="renameChatForm">
                    <input type="text" id="newChatTitle" value="${currentTitle}" placeholder="Enter new title" maxlength="50" autofocus>
                    <div class="rename-dialog-buttons">
                        <button type="button" class="cancel-btn">Cancel</button>
                        <button type="submit" class="save-btn">Save</button>
                    </div>
                </form>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(dialogContainer);
        
        // Focus the input
        setTimeout(() => {
            const input = document.getElementById('newChatTitle');
            if (input) {
                input.focus();
                input.select();
            }
        }, 50);
        
        // Add event listeners
        const form = dialogContainer.querySelector('#renameChatForm');
        const cancelBtn = dialogContainer.querySelector('.cancel-btn');
        
        // Close on cancel
        cancelBtn.addEventListener('click', () => {
            dialogContainer.remove();
        });
        
        // Close on clicking outside
        dialogContainer.addEventListener('click', (e) => {
            if (e.target === dialogContainer) {
                dialogContainer.remove();
            }
        });
        
        // Handle form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const newTitle = document.getElementById('newChatTitle').value.trim();
            if (newTitle) {
                this.renameChat(chatId, newTitle);
                dialogContainer.remove();
            }
        });
    }
    
    /**
     * Rename a chat session
     * @param {string} chatId - The ID of the chat to rename
     * @param {string} newTitle - The new title for the chat
     */
    renameChat(chatId, newTitle) {
        try {
            // Get chat history from localStorage
            const saved = localStorage.getItem('unifiedChatHistory');
            if (saved) {
                let chats = JSON.parse(saved);
                
                // Find and update the chat
                const chatIndex = chats.findIndex(c => c.id === chatId);
                if (chatIndex !== -1) {
                    chats[chatIndex].title = newTitle;
                    
                    // Save updated history
                    localStorage.setItem('unifiedChatHistory', JSON.stringify(chats));
                    
                    // Update sidebar
                    this.updateChatHistorySidebar(chats);
                    
                    // If this is the current chat, update the sessionId
                    if (chatId === this.sessionId) {
                        // Just update our local state, save will happen automatically next time
                        console.log(`Renamed current chat to "${newTitle}"`);
                    }
                    
                    // If user is logged in, also update on server
                    if (this.isUserLoggedIn && this.userId) {
                        console.log(`Updating chat "${chatId}" title on server to "${newTitle}"`);
                        
                        fetch('/api/save-chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                chat: chats[chatIndex],
                                userId: this.userId
                            }),
                            credentials: 'same-origin'
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (!data.success) {
                                console.error('Error updating chat title on server:', data.error);
                            }
                        })
                        .catch(error => {
                            console.error('Error updating chat title on server:', error);
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Error renaming chat:', error);
        }
    }

    /**
     * Handle file upload and storage
     * @param {File} file - The file object to upload
     * @returns {Promise} - Promise that resolves with the upload result
     */
    uploadFile(file) {
        if (!file) {
            return Promise.reject('No file provided');
        }
        
        // Show a user message with the file upload
        this.addMessage(`Uploading file: ${file.name}`, true);
        
        // Show typing indicator
        const typingIndicator = this.showTypingIndicator();
        
        // Create form data for upload
        const formData = new FormData();
        formData.append('file', file);
        
        return fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            this.hideTypingIndicator(typingIndicator);
            
            if (data.success) {                // Create file object
                const fileData = {
                    filename: data.filename,
                    stored_filename: data.stored_filename,
                    content_preview: data.content_preview,
                    storage_type: data.storage_type,
                    timestamp: new Date().toISOString()
                };
                
                // Add optional file properties
                if (data.content) {
                    fileData.content = data.content;
                    
                    // Handle truncated content
                    if (data.is_truncated) {
                        console.log(`Received truncated file content: ${data.content.length} characters of ${data.full_content_size} total`);
                        fileData.is_truncated = true;
                        fileData.full_content_size = data.full_content_size;
                    } else {
                        console.log(`Received file content: ${data.content.length} characters`);
                    }
                }
                
                if (data.download_url) {
                    fileData.download_url = data.download_url;
                }
                
                if (data.file_id) {
                    fileData.file_id = data.file_id;
                    console.log(`Stored file ID: ${data.file_id}`);
                } else {
                    console.warn("No file ID received from server");
                }
                  // Store in fileHistory for later reference, but don't automatically add to context
                this.fileHistory[data.filename] = fileData;
                
                // Only store in the file history but don't add to the active context automatically
                // The user will need to mention the file by name to use it
                
                // Log what we've stored
                console.log("File added to history:", {
                    filename: fileData.filename,
                    hasContent: !!fileData.content,
                    contentLength: fileData.content ? fileData.content.length : 0,
                    hasFileId: !!fileData.file_id
                });
                
                // For backward compatibility
                this.uploadedFiles[data.filename] = fileData;
                
                // Custom success message based on active module
                let successMsg = '';
                let moduleInstructions = '';
                
                // Different messages based on the active module
                switch(this.activeModule) {
                    case 'proofread':
                        successMsg = `File uploaded successfully. You can now ask me to proofread ${file.name}.`;
                        moduleInstructions = "Try asking: \"Please proofread this document and fix any errors.\"";
                        break;
                    case 'study':
                        successMsg = `File uploaded successfully. I can help you study the content in ${file.name}.`;
                        moduleInstructions = "Try asking: \"Can you explain the key concepts in this document?\" or \"Summarize this document for me.\"";
                        break;
                    case 'entertainment':
                        successMsg = `File uploaded successfully. I can discuss the content of ${file.name} with you.`;
                        moduleInstructions = "Try asking: \"What do you think about this content?\" or \"Let's discuss the themes in this document.\"";
                        break;
                    case 'excel':
                        successMsg = `File uploaded successfully. I can help you analyze or transform the data in ${file.name}.`;
                        moduleInstructions = "Try asking: \"Can you generate an Excel spreadsheet based on this data?\" or \"Analyze this data for me.\"";
                        break;
                    case 'presentation':
                        successMsg = `File uploaded successfully. I can create a presentation based on ${file.name}.`;
                        moduleInstructions = "Try asking: \"Create a presentation based on this document\" or \"Extract the main points for slides.\"";
                        break;
                    default:
                        successMsg = `File uploaded successfully. I'll be happy to help you with ${file.name}.`;
                        moduleInstructions = "Let me know what you'd like to do with this file.";
                }
                
                // Add module-specific instructions to the message
                const completeMessage = `${successMsg}<br><br><em>${moduleInstructions}</em>`;
                this.addMessage(completeMessage, false);
                
                // Save to history
                this.messageHistory.push({
                    role: 'assistant',
                    content: completeMessage,
                    timestamp: new Date().toISOString(),
                    file: this.contextData.uploadedFile
                });
                
                // Save chat state
                this.saveCurrentChat();
                
                // Return successfully stored file data
                return {
                    success: true,
                    filename: data.filename,
                    content_preview: data.content_preview,
                    message: 'File uploaded and stored successfully'
                };
            } else {
                // Show error message
                const errorMsg = `Sorry, there was an error uploading your file: ${data.error || 'Unknown error'}`;
                this.addMessage(errorMsg, false);
                
                return {
                    success: false,
                    error: data.error || 'Unknown error'
                };
            }
        })
        .catch(error => {
            console.error('Error uploading file:', error);
            this.hideTypingIndicator(typingIndicator);
            
            // Show error message
            const errorMsg = `Sorry, there was an error uploading your file: ${error.toString()}`;
            this.addMessage(errorMsg, false);
            
            return {
                success: false,
                error: error.toString()
            };
        });
    }
    
    /**
     * Get all uploaded files for this session
     * @returns {Object} - Object containing all uploaded files
     */
    getUploadedFiles() {
        return this.uploadedFiles;
    }
    
    /**
     * Get a specific uploaded file by filename
     * @param {string} filename - The filename to look for
     * @returns {Object|null} - The file data or null if not found
     */
    getUploadedFile(filename) {
        return this.uploadedFiles[filename] || null;
    }

    /**
     * Check if user is currently logged in
     */
    checkLoginStatus() {
        // If Firebase is available, use it to check login status
        if (typeof firebase !== 'undefined' && firebase.auth) {
            firebase.auth().onAuthStateChanged(user => {
                this.isUserLoggedIn = !!user;
                if (user) {
                    console.log('User is logged in:', user.email);
                    this.userId = user.uid;
                } else {
                    console.log('User is not logged in');
                    this.userId = null;
                }
            });
        } else {
            // Try to check if we have a user_id in a session cookie
            // This is a simplified check that assumes if we're logged in, certain elements would exist
            const accountLink = document.querySelector('a[href="/account"]');
            const loginLink = document.querySelector('a[href="/login"]');
            
            this.isUserLoggedIn = !!accountLink && !loginLink;
            console.log('Login status determined from DOM:', this.isUserLoggedIn);
            
            // We'll make an API call to check login status more reliably
            fetch('/api/check-login-status', {
                method: 'GET',
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                this.isUserLoggedIn = data.loggedIn;
                this.userId = data.userId || null;
                console.log('Login status from API:', this.isUserLoggedIn);
                
                // If user is logged in, load chat history for the sidebar only
                if (this.isUserLoggedIn && this.userId) {
                    this.loadChatHistoryForSidebar();
                }
            })
            .catch(error => {
                console.error('Error checking login status:', error);
            });
        }
    }

    /**
     * Force sync of chat history with server
     */
    syncChatHistory() {
        if (!this.isUserLoggedIn || !this.userId) {
            alert('Please log in to sync your chat history across devices');
            return;
        }
        
        // First save the current chat
        this.saveCurrentChat();
        
        // Show loading indicator
        const syncButton = document.querySelector('.sync-button');
        if (syncButton) {
            syncButton.classList.add('syncing');
            syncButton.setAttribute('disabled', 'disabled');
            syncButton.innerHTML = '<i class="fas fa-sync fa-spin"></i>';
        }
        
        // Send all local chats to server
        const savedHistory = localStorage.getItem('unifiedChatHistory');
        if (savedHistory) {
            try {
                const chats = JSON.parse(savedHistory);
                // If no local chats, just reload from server without calling API
                if (!Array.isArray(chats) || chats.length === 0) {
                    // Reset sync button
                    if (syncButton) {
                        syncButton.classList.remove('syncing');
                        syncButton.removeAttribute('disabled');
                        syncButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
                    }
                    // Reload chat history from server
                    this.loadChatHistory();
                    return;
                }
                
                fetch('/api/sync-chats', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        chats: chats,
                        userId: this.userId
                    }),
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    // Reset sync button
                    if (syncButton) {
                        syncButton.classList.remove('syncing');
                        syncButton.removeAttribute('disabled');
                        syncButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
                    }
                    if (data.success) {
                        // Reload chat history from server
                        this.loadChatHistory();
                        alert('Chat history synced successfully!');
                    } else {
                        console.error('Error syncing chats:', data.error);
                        alert('Error syncing chat history: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error syncing chats:', error);
                    alert('Error syncing chat history: ' + error.message);
                    
                    // Reset sync button
                    if (syncButton) {
                        syncButton.classList.remove('syncing');
                        syncButton.removeAttribute('disabled');
                        syncButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
                    }
                });
            } catch (error) {
                console.error('Error parsing chat history for sync:', error);
                alert('Error syncing chat history. Please try again.');
                
                // Reset sync button
                if (syncButton) {
                    syncButton.classList.remove('syncing');
                    syncButton.removeAttribute('disabled');
                    syncButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
                }
            }
        }
    }
    
    /**
     * Load chat history for sidebar only, without loading any chat content
     */
    loadChatHistoryForSidebar() {
        // Load from server if user is logged in
        if (this.isUserLoggedIn && this.userId) {
            console.log('Loading chat history for sidebar for user:', this.userId);
            fetch('/api/user-chats', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.chats && data.chats.length > 0) {
                    console.log('Server chat history loaded for sidebar:', data.chats.length, 'conversations');
                    
                    // Update local storage with server data
                    localStorage.setItem('unifiedChatHistory', JSON.stringify(data.chats));
                    
                    // Load conversations into the sidebar only
                    this.updateChatHistorySidebar(data.chats);
                }
            })
            .catch(error => {
                console.error('Error loading server chat history for sidebar:', error);
                // Try using local storage for sidebar
                const savedHistory = localStorage.getItem('unifiedChatHistory');
                if (savedHistory) {
                    try {
                        const history = JSON.parse(savedHistory);
                        this.updateChatHistorySidebar(history);
                    } catch (error) {
                        console.error('Error loading chat history from localStorage for sidebar:', error);
                    }
                }
            });
        } else {
            // User not logged in, use localStorage for sidebar
            const savedHistory = localStorage.getItem('unifiedChatHistory');
            if (savedHistory) {
                try {
                    const history = JSON.parse(savedHistory);
                    this.updateChatHistorySidebar(history);
                } catch (error) {
                    console.error('Error loading chat history from localStorage for sidebar:', error);
                }
            }
        }
    }
    
    /**
     * Check if a message mentions any of the files we have in history
     * @param {string} message - The message text to check
     * @returns {string|null} - The filename if found, null otherwise
     */
    checkForFileMentions(message) {
        if (!message || !this.fileHistory || Object.keys(this.fileHistory).length === 0) {
            return null;
        }
        
        // Convert message to lowercase for case-insensitive matching
        const lowerMessage = message.toLowerCase();
        
        // First check if the message explicitly asks to use a file
        if (lowerMessage.includes("use file") || 
            lowerMessage.includes("reference file") || 
            lowerMessage.includes("look at file") || 
            lowerMessage.includes("open file") || 
            lowerMessage.includes("read file") ||
            lowerMessage.includes("refer to file") ||
            lowerMessage.includes("use the file") ||
            lowerMessage.includes("use document") ||
            lowerMessage.includes("with document")) {
            // User is explicitly asking to use a file
        } else if (!(
            lowerMessage.includes("use") || 
            lowerMessage.includes("refer") ||
            lowerMessage.includes("from") ||
            lowerMessage.includes("open") ||
            lowerMessage.includes("load") ||
            lowerMessage.includes("with") ||
            lowerMessage.includes("based on")
        )) {
            // If none of these keywords are in the message, it's unlikely to be a file request
            return null;
        }
        
        // More precise patterns that indicate intent to use a file
        const filePatterns = [
            /(?:use|open|refer\s+to|read|with|based\s+on)\s+(?:(?:the|my|this)\s+)?(?:file|document|pdf|spreadsheet|excel|presentation|doc)\s+(?:named|called)?\s*["']?([^"'.,!?\s]+(?:\s+[^"'.,!?\s]+){0,3})["']?/i,
            /(?:file|document|pdf|spreadsheet|excel|presentation|doc)\s+(?:named|called)?\s*["']?([^"'.,!?\s]+(?:\s+[^"'.,!?\s]+){0,3})["']?/i,
            /["']([^"']+\.(pdf|doc|docx|xlsx|xls|pptx|ppt|txt))["']/i
        ];
        
        for (const pattern of filePatterns) {
            const match = message.match(pattern);
            if (match && match[1]) {
                const potentialFilename = match[1].trim();
                
                // Check if this matches any file in our history
                for (const filename in this.fileHistory) {
                    // Create variations of the filename to check for
                    const filenameWithoutExt = filename.substring(0, filename.lastIndexOf('.')) || filename;
                    const lowerFilename = filename.toLowerCase();
                    const lowerFilenameWithoutExt = filenameWithoutExt.toLowerCase();
                    const lowerPotential = potentialFilename.toLowerCase();
                    
                    // Check for partial matches (the mentioned text is part of the filename)
                    if (lowerFilename.includes(lowerPotential) || 
                        lowerPotential.includes(lowerFilename) ||
                        lowerFilenameWithoutExt.includes(lowerPotential) || 
                        lowerPotential.includes(lowerFilenameWithoutExt)) {
                        console.log(`File mention detected: ${filename} (matched: ${potentialFilename})`);
                        return filename;
                    }
                }
            }
        }
          // Fall back to simple inclusion check if patterns don't match, but be more selective
        // Only check for exact matches or mentions with file-related context
        const fileRelatedWords = ['file', 'document', 'pdf', 'doc', 'text', 'upload', 'using', 'refer', 'according', 'written', 'from'];
        const hasFileContext = fileRelatedWords.some(word => lowerMessage.includes(word.toLowerCase()));
        
        // Only proceed with exact matching if there's file-related context
        if (hasFileContext) {
            for (const filename in this.fileHistory) {
                // Create variations of the filename to check for
                const filenameWithoutExt = filename.substring(0, filename.lastIndexOf('.')) || filename;
                const lowerFilename = filename.toLowerCase();
                const lowerFilenameWithoutExt = filenameWithoutExt.toLowerCase();
                
                // Check for more precise matches (not just inclusion)
                // The file name should be a distinct part of the message
                const isExactMatch = 
                    lowerMessage.includes(` ${lowerFilename} `) || 
                    lowerMessage.includes(` ${lowerFilename}.`) || 
                    lowerMessage.includes(` ${lowerFilename},`) || 
                    lowerMessage.includes(`"${lowerFilename}"`) || 
                    lowerMessage.includes(`'${lowerFilename}'`) || 
                    lowerMessage.includes(` ${lowerFilenameWithoutExt} `) || 
                    lowerMessage.includes(` ${lowerFilenameWithoutExt}.`) || 
                    lowerMessage.includes(` ${lowerFilenameWithoutExt},`) || 
                    lowerMessage.includes(`"${lowerFilenameWithoutExt}"`) || 
                    lowerMessage.includes(`'${lowerFilenameWithoutExt}'`) || 
                    lowerMessage.startsWith(lowerFilename) || 
                    lowerMessage.startsWith(lowerFilenameWithoutExt);
                    
                if (isExactMatch) {
                    console.log(`File mention detected: ${filename} (direct inclusion with context)`);
                    return filename;
                }
            }
        }
        
        return null;
    }

    /**
     * Add a file from history to current context
     * @param {string} filename - The filename to add to context
     * @returns {boolean} - Whether the file was successfully added
     */
    addFileToContext(filename) {
        if (!filename || !this.fileHistory[filename]) {
            return false;
        }
        
        const fileData = this.fileHistory[filename];
        
        // Add file to the context for this conversation
        this.contextData.uploadedFile = {...fileData};
        
        // Add content if available
        if (fileData.content) {
            this.contextData.pdfContent = fileData.content;
        }
        
        console.log(`Added file to context: ${filename}`);
        return true;
    }

    /**
     * List all files available in file history
     * @returns {Array} - Array of file objects with their names and timestamps
     */
    listAvailableFiles() {
        if (!this.fileHistory || Object.keys(this.fileHistory).length === 0) {
            return [];
        }
        
        return Object.entries(this.fileHistory).map(([filename, data]) => {
            return {
                filename: filename,
                timestamp: data.timestamp,
                formattedDate: new Date(data.timestamp).toLocaleString()
            };
        }).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)); // Sort by date, newest first
    }

    /**
     * Show a list of available files in the chat
     */
    showAvailableFiles() {
        const files = this.listAvailableFiles();
        
        // Add user message
        this.addMessage('list files', true);
        
        if (!files.length) {
            // No files available
            this.addMessage('You haven\'t uploaded any files yet. You can upload a file using the file upload button below the chat input.', false);
            return;
        }
        
        // Format the files list
        let messageContent = '<p>Here are your available files:</p><div class="file-list">';
        files.forEach((file, index) => {
            const date = new Date(file.timestamp);
            const formattedDate = date.toLocaleDateString() + ' ' + 
                               date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                               
            messageContent += `
                <div class="file-list-item" data-filename="${file.filename}">
                    <div class="file-icon"><i class="fas fa-file"></i></div>
                    <div class="file-info">
                        <div class="file-name">${file.filename}</div>
                        <div class="file-date">Uploaded: ${formattedDate}</div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-outline-primary use-file-btn" title="Use this file">Use</button>
                    </div>
                </div>
            `;
        });
        
        messageContent += '</div><p>You can mention any of these files by name in your messages (for example: "Please use <filename>"), or click the "Use" button to start using a file.</p>';
        
        // Add the response message
        const messageDiv = this.addMessage(messageContent, false);
        
        // Add click handlers for "Use" buttons
        if (messageDiv) {
            const useButtons = messageDiv.querySelectorAll('.use-file-btn');
            useButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const fileItem = button.closest('.file-list-item');
                    const filename = fileItem.getAttribute('data-filename');
                    
                    if (filename && this.addFileToContext(filename)) {
                        // Show file context indicator
                        const fileContext = this.createFileContextIndicator(filename);
                        this.chatMessages.appendChild(fileContext);
                        this.scrollToBottom();
                        
                        // Add confirmation message
                        this.addMessage(`I'll use ${filename} for our conversation. What would you like to know about it?`, false);
                    }
                });
            });
        }
        
        // Add to message history
        this.messageHistory.push({
            role: 'user',
            content: 'list files',
            timestamp: new Date().toISOString()
        });
        this.messageHistory.push({
            role: 'assistant',
            content: messageContent,
            timestamp: new Date().toISOString()
        });
        
        // Save to localStorage
        this.saveCurrentChat();
    }

    /**
     * Clear the current file context
     * @returns {boolean} - Whether a file was cleared
     */
    clearFileContext() {
        if (!this.contextData.uploadedFile && !this.contextData.pdfContent) {
            return false; // No file to clear
        }
        
        // Save what we're clearing for the message
        const filename = this.contextData.uploadedFile?.filename || 'file';
        
        // Clear file context
        delete this.contextData.uploadedFile;
        delete this.contextData.pdfContent;
        
        console.log('File context cleared');
        
        // Add message to the chat
        this.addMessage(`I'm no longer using "${filename}" for this conversation. If you need to reference it again, please mention it by name.`, false);
        
        // Save updated chat state
        this.saveCurrentChat();
        
        return true;
    }

    /**
     * Create a file context indicator with a dismiss button
     * @param {string} filename - The filename to show in the indicator
     * @returns {HTMLElement} - The file context indicator element
     */
    createFileContextIndicator(filename) {
        const fileContext = document.createElement('div');
        fileContext.className = 'file-context-indicator';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'file-context-content';
        contentDiv.innerHTML = `<i class="fas fa-file-alt"></i> Now using file: ${filename}`;
        fileContext.appendChild(contentDiv);
        
        const dismissBtn = document.createElement('button');
        dismissBtn.className = 'file-context-dismiss';
        dismissBtn.innerHTML = '×';
        dismissBtn.title = 'Stop using this file';
        dismissBtn.addEventListener('click', () => {
            this.clearFileContext();
            fileContext.remove();
        });
        fileContext.appendChild(dismissBtn);
        
        return fileContext;
    }

    /**
     * Filter chat history based on search term
     * @param {string} searchTerm - The term to filter by
     */
    filterChatHistory(searchTerm) {
        if (!this.allChats || !this.allChats.length) {
            return;
        }
        
        searchTerm = searchTerm.toLowerCase().trim();
        
        if (!searchTerm) {
            // If search is cleared, show all chats
            this.renderChatHistoryItems(this.allChats);
            return;
        }
        
        // Filter chats based on title
        const filteredChats = this.allChats.filter(chat => {
            const title = chat.title.toLowerCase();
            return title.includes(searchTerm);
        });
        
        // Render the filtered chats
        this.renderChatHistoryItems(filteredChats);
    }
    
    /**
     * Render chat history items in the sidebar
     * @param {Array} chats - The chats to render
     */
    renderChatHistoryItems(chats) {
        if (!this.chatHistory) {
            return;
        }
        
        this.chatHistory.innerHTML = '';
          if (!chats || chats.length === 0) {
            const noHistory = document.createElement('div');
            noHistory.className = 'text-center text-white-50 p-3';
            
            const isFiltered = chats !== this.allChats && this.allChats && this.allChats.length > 0;
            
            if (isFiltered) {
                noHistory.innerHTML = `
                    <p>No matching chats</p>
                    <button class="clear-search-btn">
                        <i class="fas fa-times-circle me-1"></i> Clear search
                    </button>
                `;
                
                // Add clear search button functionality
                const clearBtn = noHistory.querySelector('.clear-search-btn');
                if (clearBtn && this.chatHistorySearch) {
                    clearBtn.addEventListener('click', () => {
                        this.chatHistorySearch.value = '';
                        this.renderChatHistoryItems(this.allChats);
                    });
                }
            } else {
                noHistory.textContent = 'No previous chats';
            }
            
            this.chatHistory.appendChild(noHistory);
            return;
        }
        
        chats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-history-item';
            chatItem.dataset.id = chat.id;
            if (chat.id === this.sessionId) {
                chatItem.classList.add('active');
            }
            
            // Format date - use lastMessageAt if available, fall back to createdAt or timestamp
            const dateString = chat.lastMessageAt || chat.createdAt || chat.timestamp;
            const date = new Date(dateString);
            const formattedDate = date.toLocaleDateString() + ' ' + 
                                date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              // Get search term for highlighting
            const searchTerm = this.chatHistorySearch ? this.chatHistorySearch.value.trim().toLowerCase() : '';
            const titleWithHighlight = searchTerm ? 
                this.highlightMatchingText(chat.title, searchTerm) : 
                chat.title;
            
            // Create item content with title and date
            chatItem.innerHTML = `
                <div class="history-item-content">
                    <div class="history-title">${titleWithHighlight}</div>
                    <div class="history-date">${formattedDate}</div>
                </div>
                <div class="history-actions">
                    <button class="history-rename" title="Rename chat"><i class="fas fa-edit"></i></button>
                    <button class="history-delete" title="Delete chat"><i class="fas fa-trash"></i></button>
                </div>
            `;
            
            // Add click handler to load chat
            chatItem.addEventListener('click', (e) => {
                if (!e.target.closest('.history-actions')) {
                    this.loadChatSession(chat.id);
                }
            });
            
            // Add rename button handler
            const renameBtn = chatItem.querySelector('.history-rename');
            if (renameBtn) {
                renameBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showRenameChatDialog(chat.id, chat.title);
                });
            }
            
            // Add delete button handler
            const deleteBtn = chatItem.querySelector('.history-delete');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteChat(chat.id);
                });
            }
            
            this.chatHistory.appendChild(chatItem);
        });
    }

    /**
     * Highlight matching text in a string
     * @param {string} text - The text to highlight within
     * @param {string} searchTerm - The search term to highlight
     * @returns {string} - HTML string with highlighted text
     */
    highlightMatchingText(text, searchTerm) {
        if (!searchTerm || !text) {
            return text;
        }
        
        searchTerm = searchTerm.toLowerCase();
        const lowerText = text.toLowerCase();
        const startIndex = lowerText.indexOf(searchTerm);
        
        if (startIndex === -1) {
            return text;
        }
        
        const endIndex = startIndex + searchTerm.length;
        const beforeMatch = text.slice(0, startIndex);
        const match = text.slice(startIndex, endIndex);
        const afterMatch = text.slice(endIndex);
        
        return `${beforeMatch}<span class="search-highlight">${match}</span>${afterMatch}`;
    }    /**
     * Fetch and display files from Firebase Storage
     */
    fetchAndDisplayFiles() {
        fetch('/api/list-files', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const { files } = data;
                const fileListContainer = document.getElementById('fileListContainer');
                
                if (fileListContainer) {
                    // Clear the container
                    fileListContainer.innerHTML = '';
                    
                    // Create a "no files" message
                    if (!files || files.length === 0) {
                        const noFilesMessage = document.createElement('div');
                        noFilesMessage.className = 'no-files-message';
                        noFilesMessage.textContent = "You haven't uploaded any files yet. You can upload a file using the file upload button below the chat input.";
                        fileListContainer.appendChild(noFilesMessage);
                        return;
                    }
                    
                    // Create a file list heading
                    const fileListHeading = document.createElement('div');
                    fileListHeading.className = 'file-list-heading';
                    fileListHeading.textContent = `Your Files (${files.length})`;
                    fileListContainer.appendChild(fileListHeading);
                    
                    // Create a file list
                    files.forEach(file => {
                        const fileItem = document.createElement('div');
                        fileItem.className = 'file-item';
                        
                        // Get file name, preferring display name fields
                        const fileName = file.name || file.filename || file.stored_filename || 'Unnamed file';
                        
                        // Show file icon based on file type
                        const fileExtension = fileName.split('.').pop().toLowerCase();
                        let fileIcon = '📄'; // Default document icon
                        
                        if (['pdf'].includes(fileExtension)) {
                            fileIcon = '📕';
                        } else if (['doc', 'docx'].includes(fileExtension)) {
                            fileIcon = '📝';
                        } else if (['xls', 'xlsx', 'csv'].includes(fileExtension)) {
                            fileIcon = '📊';
                        } else if (['ppt', 'pptx'].includes(fileExtension)) {
                            fileIcon = '📊';
                        } else if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExtension)) {
                            fileIcon = '🖼️';
                        }
                        
                        // Display the file with its icon
                        fileItem.innerHTML = `${fileIcon} ${fileName}`;
                        
                        // Add click event to use the file in the chat
                        fileItem.addEventListener('click', () => {
                            this.selectAndUseFile(file);
                        });
                        
                        fileListContainer.appendChild(fileItem);
                    });
                }
            } else {
                console.error('Failed to fetch files:', data.error);
                
                // Display error message
                const fileListContainer = document.getElementById('fileListContainer');
                if (fileListContainer) {
                    fileListContainer.innerHTML = '<div class="error-message">Failed to load your files. Please try again later.</div>';
                }
            }
        })        .catch(error => {
            console.error('Error fetching files:', error);
            
            // Display error message
            const fileListContainer = document.getElementById('fileListContainer');
            if (fileListContainer) {
                fileListContainer.innerHTML = '<div class="error-message">Failed to load your files. Please try again later.</div>';
            }
        });
    }
    
    /**
     * Select and use a file from the file list in the chat
     * @param {Object} file - File object containing metadata
     */
    selectAndUseFile(file) {
        if (!file) return;
        
        // Display a message indicating the file is being used
        const fileName = file.name || file.filename || file.stored_filename || 'selected file';
        this.addMessage(`I'm using the uploaded file: ${fileName}`, true);
        
        // Store the file in context
        const fileData = {
            filename: fileName,
            file_id: file.file_id,
            download_url: file.download_url,
            content: file.content || '',
            storage_type: file.storage_type || 'firebase'
        };
        
        // Set as current context file
        this.contextData.uploadedFile = fileData;
        
        // Show typing indicator
        const typingIndicator = this.showTypingIndicator();
        
        // Check if we need to download the file content
        if (!fileData.content && fileData.download_url) {
            // Just use the file without trying to download the content
            this.hideTypingIndicator(typingIndicator);
            this.addMessage(`I'm now using ${fileName}. What would you like to know about this file?`, false);
        } else {
            // We already have the content, use it directly
            this.hideTypingIndicator(typingIndicator);
            this.addMessage(`I'm now using ${fileName}. What would you like to know about this file?`, false);
        }
    }
}

// Initialize the agent
const liyaAgent = new LiyaAgent();

// Make it globally available
window.liyaAgent = liyaAgent;