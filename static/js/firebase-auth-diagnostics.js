/**
 * Firebase Authentication State Diagnostic Tool
 * 
 * This script helps diagnose Firebase authentication issues by checking:
 * 1. Current auth state in memory
 * 2. Persistence settings
 * 3. Storage locations (localStorage, sessionStorage, IndexedDB)
 * 4. Session cookies
 */

function diagnoseFirebaseAuth() {
    console.group('Firebase Authentication Diagnostics');
    
    // Check if Firebase is available and initialized
    if (typeof firebase === 'undefined') {
        console.error('Firebase SDK not loaded');
        console.groupEnd();
        return;
    }
    
    if (!firebase.apps || firebase.apps.length === 0) {
        console.error('Firebase not initialized');
        console.groupEnd();
        return;
    }
    
    // Check current auth state
    console.log('Checking current Firebase auth state...');
    firebase.auth().onAuthStateChanged(user => {
        if (user) {
            console.log('🔴 User is currently signed in:');
            console.log('- Email:', user.email);
            console.log('- UID:', user.uid);
            console.log('- Display Name:', user.displayName);
            console.log('- Email Verified:', user.emailVerified);
            
            // Check token
            user.getIdToken().then(token => {
                console.log('- Valid ID Token available:', token.substring(0, 10) + '...');
            }).catch(err => {
                console.error('- Error getting ID token:', err);
            });
            
            // Check for token refresh ability
            user.getIdTokenResult().then(tokenResult => {
                const expirationTime = new Date(tokenResult.expirationTime).getTime();
                const now = new Date().getTime();
                const timeUntilExpiry = (expirationTime - now) / 1000 / 60; // minutes
                
                console.log(`- Token expires in: ${timeUntilExpiry.toFixed(1)} minutes`);
            });
        } else {
            console.log('✅ No user is currently signed in');
        }
    });
    
    // Check persistence settings
    try {
        if (firebase.auth().Persistence) {
            const availablePersistenceOptions = [
                {name: 'NONE', value: firebase.auth.Auth.Persistence.NONE},
                {name: 'SESSION', value: firebase.auth.Auth.Persistence.SESSION},
                {name: 'LOCAL', value: firebase.auth.Auth.Persistence.LOCAL},
                {name: 'INDEXED_DB', value: firebase.auth.Auth.Persistence.INDEXED_DB}
            ];
            
            console.log('Available persistence types:', availablePersistenceOptions.map(p => p.name));
            
            // There's no direct API to check current persistence setting
            console.log('Note: Current persistence setting cannot be directly queried from the SDK');
        } else {
            console.log('Firebase Auth Persistence API not available');
        }
    } catch (e) {
        console.error('Error checking persistence settings:', e);
    }
    
    // Check for flags in localStorage
    console.group('Local Storage');
    try {
        console.log('explicitly_logged_out flag:', localStorage.getItem('explicitly_logged_out'));
        
        // Check for Firebase auth data
        const firebaseKeys = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.startsWith('firebase:') || key.includes(':auth') || key.includes('firebaseauth'))) {
                firebaseKeys.push(key);
                try {
                    const value = localStorage.getItem(key);
                    // Try to parse it if it's JSON
                    try {
                        const parsedValue = JSON.parse(value);
                        // Only log a preview of the object to avoid cluttering the console
                        console.log(`- ${key}: ${JSON.stringify(parsedValue).substring(0, 50)}...`);
                    } catch {
                        // Not JSON, just log the raw value
                        console.log(`- ${key}: ${value.substring(0, 50)}...`);
                    }
                } catch (e) {
                    console.error(`- Error reading ${key}:`, e);
                }
            }
        }
        
        if (firebaseKeys.length === 0) {
            console.log('✅ No Firebase auth data found in localStorage');
        } else {
            console.log(`🔴 Found ${firebaseKeys.length} Firebase-related items in localStorage`);
        }
    } catch (e) {
        console.error('Error checking localStorage:', e);
    }
    console.groupEnd();
    
    // Check sessionStorage
    console.group('Session Storage');
    try {
        const sessionKeys = [];
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            if (key && (key.startsWith('firebase:') || key.includes(':auth') || key.includes('firebaseauth'))) {
                sessionKeys.push(key);
                console.log(`- ${key}: ${sessionStorage.getItem(key).substring(0, 50)}...`);
            }
        }
        
        if (sessionKeys.length === 0) {
            console.log('✅ No Firebase auth data found in sessionStorage');
        } else {
            console.log(`🔴 Found ${sessionKeys.length} Firebase-related items in sessionStorage`);
        }
    } catch (e) {
        console.error('Error checking sessionStorage:', e);
    }
    console.groupEnd();
    
    // Check IndexedDB
    console.group('IndexedDB');
    try {
        // List all databases
        indexedDB.databases().then(databases => {
            const firebaseDbs = databases.filter(db => db.name.toLowerCase().includes('firebase'));
            
            if (firebaseDbs.length === 0) {
                console.log('✅ No Firebase IndexedDB databases found');
            } else {
                console.log(`🔴 Found ${firebaseDbs.length} Firebase IndexedDB databases:`);
                firebaseDbs.forEach(db => {
                    console.log(`- ${db.name} (version: ${db.version})`);
                });
            }
        }).catch(err => {
            console.error('Error listing IndexedDB databases:', err);
        });
    } catch (e) {
        console.error('Error checking IndexedDB:', e);
    }
    console.groupEnd();
    
    // Check cookies
    console.group('Cookies');
    try {
        const cookies = document.cookie.split(';');
        let foundFirebaseCookies = false;
        
        cookies.forEach(cookie => {
            const trimmed = cookie.trim();
            if (trimmed.includes('firebase') || trimmed.includes('firebaseauth')) {
                console.log('🔴 Firebase-related cookie found:', trimmed);
                foundFirebaseCookies = true;
            }
        });
        
        if (!foundFirebaseCookies) {
            console.log('✅ No Firebase auth cookies found');
        }
        
        // Check for session cookie
        if (document.cookie.includes('session=')) {
            console.log('Server session cookie present');
        } else {
            console.log('No server session cookie present');
        }
    } catch (e) {
        console.error('Error checking cookies:', e);
    }
    console.groupEnd();
    
    // Provide recommendations
    console.group('Recommendations');
    if (typeof localStorage.getItem('explicitly_logged_out') === 'string' && localStorage.getItem('explicitly_logged_out') !== 'true') {
        console.log('❌ explicitly_logged_out flag is not correctly set to true');
        console.log('   Recommendation: Set localStorage.setItem("explicitly_logged_out", "true") and reload');
    }
    
    setTimeout(() => {
        // This check runs after the auth state is checked
        const signOutAgainBtn = document.createElement('button');
        signOutAgainBtn.textContent = 'Force Firebase Sign Out';
        signOutAgainBtn.style.padding = '8px 16px';
        signOutAgainBtn.style.marginTop = '10px';
        signOutAgainBtn.style.backgroundColor = '#d9534f';
        signOutAgainBtn.style.color = 'white';
        signOutAgainBtn.style.border = 'none';
        signOutAgainBtn.style.borderRadius = '4px';
        signOutAgainBtn.style.cursor = 'pointer';
        
        signOutAgainBtn.addEventListener('click', () => {
            console.log('Forcing Firebase sign out...');
            
            // Set the explicit logout flag
            localStorage.setItem('explicitly_logged_out', 'true');
            
            // Clear Firebase auth data
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && (key.startsWith('firebase:') || key.includes(':auth') || key.includes('firebaseauth'))) {
                        localStorage.removeItem(key);
                    }
                }
                
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    if (key && (key.startsWith('firebase:') || key.includes(':auth') || key.includes('firebaseauth'))) {
                        sessionStorage.removeItem(key);
                    }
                }
            } catch (e) {
                console.error('Error clearing storage:', e);
            }
            
            // Sign out from Firebase
            if (firebase && firebase.auth) {
                firebase.auth().signOut().then(() => {
                    console.log('Successfully signed out from Firebase');
                    
                    // Try to clear IndexedDB
                    try {
                        const dbNames = [
                            'firebaseLocalStorageDb', 
                            'firebase-heartbeat-database',
                            'firebase-installations-database'
                        ];
                        
                        dbNames.forEach(dbName => {
                            const req = indexedDB.deleteDatabase(dbName);
                            req.onsuccess = () => console.log(`Successfully deleted IndexedDB: ${dbName}`);
                            req.onerror = () => console.error(`Error deleting IndexedDB: ${dbName}`);
                        });
                    } catch (e) {
                        console.error('Error clearing IndexedDB:', e);
                    }
                    
                    alert('Signed out successfully. Please reload the page to verify.');
                }).catch(error => {
                    console.error('Error signing out from Firebase:', error);
                    alert('Error signing out: ' + error.message);
                });
            } else {
                console.error('Firebase auth not available');
                alert('Firebase auth not available');
            }
        });
        
        // Add the button to the console
        console.log('Use this button to force sign out:');
        console.log(signOutAgainBtn);
    }, 1000);
    console.groupEnd();
    
    console.groupEnd();
}

// Execute the diagnostics
diagnoseFirebaseAuth();

// Add a global function to run again from the console
window.diagnoseFirebaseAuth = diagnoseFirebaseAuth;
