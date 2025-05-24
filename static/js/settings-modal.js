// Settings Modal Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const settingsModal = document.getElementById('settingsModal');
    const settingsOverlay = document.getElementById('settingsModalOverlay');
    const settingsOpenBtns = document.querySelectorAll('[data-settings-open]');
    const settingsCloseBtn = document.getElementById('settingsCloseBtn');
    const settingsNavItems = document.querySelectorAll('.settings-nav-item');
    const settingsTabs = document.querySelectorAll('.settings-tab');
    
    // Copy referral link functionality
    const referralLinkInput = document.getElementById('settings-referral-link');
    const copyReferralBtn = document.getElementById('settings-copy-referral');
    const copySuccessMsg = document.getElementById('settings-copy-success');
    
    // Toggle buttons for settings options
    const toggleInputs = document.querySelectorAll('.settings-toggle input');
    
    // Open settings modal
    function openSettingsModal() {
        settingsOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent scrolling behind modal
        
        // Fade in animation
        setTimeout(() => {
            settingsOverlay.style.opacity = '1';
        }, 10);
        
        // Load latest usage data when opening settings
        loadUserUsageData();
    }
    
    // Close settings modal
    function closeSettingsModal() {
        settingsOverlay.style.opacity = '0';
        
        // Wait for fade out animation before hiding
        setTimeout(() => {
            settingsOverlay.style.display = 'none';
            document.body.style.overflow = ''; // Re-enable scrolling
        }, 300);
    }
    
    // Switch between settings tabs
    function switchSettingsTab(tabId) {
        // Deactivate all tabs and nav items
        settingsTabs.forEach(tab => {
            tab.classList.remove('active');
        });
        
        settingsNavItems.forEach(item => {
            item.classList.remove('active');
        });
        
        // Activate selected tab and nav item
        document.getElementById(tabId).classList.add('active');
        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    }    // Load user token usage data
    function loadUserUsageData() {
        fetch('/api/usage/check')
            .then(response => {
                // First check if the response is ok (status in the range 200-299)
                if (!response.ok) {
                    console.warn(`Usage data request failed with status: ${response.status}`);
                    throw new Error(`Server returned ${response.status} status`);
                }
                return response.json();
            })
            .then(data => {
                try {
                    // Check if there's an error in the response
                    if (data.error) {
                        console.error('Error from API:', data.error);
                        return;
                    }
                    
                    // Update the progress bar
                    const progressBar = document.querySelector('.settings-progress-bar');
                    if (progressBar) {
                        progressBar.style.width = `${data.usage_percentage}%`;
                    }
                    
                    // Update text labels - check elements exist before updating
                    const tokensUsedEl = document.getElementById('settings-tokens-used');
                    if (tokensUsedEl) tokensUsedEl.textContent = data.current_usage;
                    
                    const tokensTotalEl = document.getElementById('settings-tokens-total');
                    if (tokensTotalEl) tokensTotalEl.textContent = data.daily_limit;
                    
                    const tokensRemainingEl = document.getElementById('settings-tokens-remaining');
                    if (tokensRemainingEl) tokensRemainingEl.textContent = data.daily_limit - data.current_usage;
                    
                    // Update color based on usage percentage
                    if (progressBar) {
                        if (data.usage_percentage > 90) {
                            progressBar.style.background = 'linear-gradient(90deg, #EF4444 0%, #F87171 100%)';
                        } else if (data.usage_percentage > 70) {
                            progressBar.style.background = 'linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%)';
                        } else {
                            progressBar.style.background = 'linear-gradient(90deg, #6366f1 0%, #38bdf8 100%)';
                        }
                    }
                } catch (error) {
                    console.error('Error processing usage data:', error);
                }
            })
            .catch(error => console.error('Error loading usage data:', error));
    } // Load referral data
    
    function loadReferralData() {
        // Set a loading placeholder
        if (referralLinkInput) {
            referralLinkInput.value = "Loading your referral link...";
        }
        
        fetch('/api/referral/code')
            .then(response => {
                if (!response.ok) {
                    console.warn(`Referral code request failed with status: ${response.status}`);
                    throw new Error(`Server returned ${response.status} status`);
                }
                const contentType = response.headers.get('content-type') || '';
                if (!contentType.includes('application/json')) {
                    // Suppress non-JSON responses (e.g., redirect HTML)
                    if (referralLinkInput) referralLinkInput.value = '';
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (!data) return;
                try {
                    if (data.success && data.referral_url && referralLinkInput) {
                        referralLinkInput.value = data.referral_url;
                    } else if (referralLinkInput) {
                        // If there's an error or no URL returned, set a message
                        referralLinkInput.value = "Error loading referral link. Please try again.";
                    }
                } catch (error) {
                    console.error('Error processing referral data:', error);
                    if (referralLinkInput) {
                        referralLinkInput.value = "Error loading referral link. Please try again.";
                    }
                }
            })
            .catch(error => {
                console.error('Error loading referral data:', error);
                if (referralLinkInput) {
                    referralLinkInput.value = "Error loading referral link. Please try again.";
                }
            });
          // Also load referral stats if applicable
        fetch('/api/referral/stats')
            .then(response => {
                // First check if the response is ok (status in the range 200-299)
                if (!response.ok) {
                    // If we get a redirect to login page or any other non-JSON response
                    console.warn(`Referral stats request failed with status: ${response.status}`);
                    throw new Error(`Server returned ${response.status} status`);
                }
                const contentType = response.headers.get('content-type') || '';
                if (!contentType.includes('application/json')) {
                    console.warn(`Referral stats request returned non-JSON response: ${contentType}`);
                    // Suppress non-JSON responses (e.g., redirect HTML)
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (!data) {
                    return;
                }
                try {
                    if (data.success) {
                        const totalReferralsEl = document.getElementById('settings-total-referrals');
                        const pendingReferralsEl = document.getElementById('settings-pending-referrals');
                        
                        if (totalReferralsEl) {
                            totalReferralsEl.textContent = data.total_count || '0';
                        }
                        if (pendingReferralsEl) {
                            pendingReferralsEl.textContent = data.pending_count || '0';
                        }
                    }
                } catch (error) {
                    console.error('Error processing referral stats:', error);
                }
            })
            .catch(error => {
                console.error('Error loading referral stats:', error);
                // Don't display explicit error on the UI - just leave the values as they are
            });
    }
    
    // Initialize event listeners
    function initializeEventListeners() {
        // Open modal buttons
        settingsOpenBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                openSettingsModal();
            });
        });
        
        // Close button
        settingsCloseBtn.addEventListener('click', closeSettingsModal);
        
        // Close when clicking outside the modal
        settingsOverlay.addEventListener('click', function(event) {
            if (event.target === settingsOverlay) {
                closeSettingsModal();
            }
        });
        
        // Tab navigation
        settingsNavItems.forEach(item => {
            item.addEventListener('click', function() {
                const tabId = this.getAttribute('data-tab');
                switchSettingsTab(tabId);
            });
        });
        
        // Copy referral link
        if (copyReferralBtn && referralLinkInput) {
            copyReferralBtn.addEventListener('click', function() {
                referralLinkInput.select();
                document.execCommand('copy');
                
                // Show success message
                copySuccessMsg.style.display = 'flex';
                
                // Hide after 3 seconds
                setTimeout(() => {
                    copySuccessMsg.style.display = 'none';
                }, 3000);
            });
        }
        
        // Save settings toggle changes
        toggleInputs.forEach(toggle => {
            toggle.addEventListener('change', function() {
                const settingId = this.id;
                const isChecked = this.checked;
                
                // Here you could add code to save the setting to the server
                console.log(`Setting ${settingId} changed to ${isChecked}`);
                
                // Example of how you might save a setting
                // fetch('/api/settings/update', {
                //     method: 'POST',
                //     headers: {
                //         'Content-Type': 'application/json',
                //     },
                //     body: JSON.stringify({
                //         setting: settingId,
                //         value: isChecked
                //     })
                // });
            });
        });
        
        // Theme selector
        const themeSelector = document.getElementById('settings-theme');
        if (themeSelector) {
            themeSelector.addEventListener('change', function() {
                const selectedTheme = this.value;
                console.log(`Theme changed to: ${selectedTheme}`);
                // Apply theme changes or save to server
            });
        }
        
        // Archive all chats button
        const archiveAllBtn = document.getElementById('settings-archive-all');
        if (archiveAllBtn) {
            archiveAllBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to archive all chats?')) {
                    console.log('Archiving all chats');
                    // Add code to archive all chats
                }
            });
        }
        
        // Delete all chats button
        const deleteAllBtn = document.getElementById('settings-delete-all');
        if (deleteAllBtn) {
            deleteAllBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to delete all chats? This cannot be undone.')) {
                    console.log('Deleting all chats');
                    // Add code to delete all chats
                }
            });
        }
        
        // Logout button
        const logoutBtn = document.getElementById('settings-logout');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function() {
                window.location.href = '/logout';
            });
        }
    }
    
    // Initialize the modal
    function initializeSettingsModal() {
        // Set initial state
        settingsOverlay.style.opacity = '0';
        settingsOverlay.style.transition = 'opacity 0.3s ease';
        
        // Set General tab as active by default
        switchSettingsTab('settings-tab-general');
        
        // Load referral data if available
        if (referralLinkInput) {
            loadReferralData();
        }
        
        // Initialize event listeners
        initializeEventListeners();
    }
    
    // Only initialize if modal exists
    if (settingsModal) {
        initializeSettingsModal();
    }
});
