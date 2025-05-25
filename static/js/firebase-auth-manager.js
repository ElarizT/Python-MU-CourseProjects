/**
 * Firebase Authentication Manager
 * 
 * This script provides improved Firebase authentication handling,
 * dealing with common issues like persisted auth state after logout,
 * and correctly managing loading states during auth operations.
 */

(function() {
  'use strict';

  // Hold our auth state
  let isInitialized = false;
  let isAuthCheckComplete = false;
  let currentUser = null;
  
  // Create the FirebaseAuthManager global object
  window.FirebaseAuthManager = {
    /**
     * Initialize Firebase Authentication
     * @param {Object} firebaseApp - Firebase app instance
     * @param {Function} onAuthStateReady - Callback when auth state is determined
     */
    init: function(firebaseApp, onAuthStateReady) {
      if (isInitialized) {
        console.warn('FirebaseAuthManager is already initialized');
        return;
      }

      console.log('Initializing Firebase Auth Manager');
      isInitialized = true;
      
      // Show loading screen while checking auth
      if (window.LoadingManager) {
        window.LoadingManager.showLoading('Checking authentication status...');
      }
      
      // Get auth instance
      const auth = firebaseApp.auth();
      
      // Set persistence based on logout state
      const wasExplicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true';
      const persistenceType = wasExplicitlyLoggedOut ? 
                             firebase.auth.Auth.Persistence.NONE : 
                             firebase.auth.Auth.Persistence.LOCAL;
      
      console.log('Setting Firebase auth persistence:', wasExplicitlyLoggedOut ? 'NONE (explicitly logged out)' : 'LOCAL');
      
      // Set the persistence
      auth.setPersistence(persistenceType)
        .then(() => {
          console.log('Firebase persistence set successfully');
          
          // Setup auth state listener
          auth.onAuthStateChanged(function(user) {
            currentUser = user;
            isAuthCheckComplete = true;
            
            console.log('Firebase auth state changed:', user ? 'User is signed in' : 'No user');
            
            // If we were explicitly logged out but a user is still detected, force logout
            if (user && wasExplicitlyLoggedOut) {
              console.warn('User detected after explicit logout, forcing sign out');
              FirebaseAuthManager.signOut();
              return;
            }
            
            // Call the callback with the auth state
            if (onAuthStateReady && typeof onAuthStateReady === 'function') {
              onAuthStateReady(user);
            }
            
            // Hide loading screen now that auth is determined
            if (window.LoadingManager) {
              window.LoadingManager.hideLoading();
            }
          });
        })
        .catch(error => {
          console.error('Error setting Firebase persistence:', error);
          isAuthCheckComplete = true;
          
          // Hide loading even on error
          if (window.LoadingManager) {
            window.LoadingManager.hideLoading();
          }
          
          // Call callback with null user on error
          if (onAuthStateReady && typeof onAuthStateReady === 'function') {
            onAuthStateReady(null);
          }
        });
    },
    
    /**
     * Sign out the current user from Firebase and the server
     * @param {Function} onComplete - Callback after signout completes
     */
    signOut: async function(onComplete) {
      if (!isInitialized) {
        console.warn('FirebaseAuthManager not initialized before signOut');
      }
      
      console.log('Starting comprehensive signout process');
      
      // Show loading during signout
      if (window.LoadingManager) {
        window.LoadingManager.showLoading('Signing out...');
      }
      
      // Set explicit logout flag
      localStorage.setItem('explicitly_logged_out', 'true');
      
      try {
        // 1. Call the server logout API
        const serverLogoutResponse = await fetch('/api/auth/signout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
          },
          credentials: 'same-origin'
        });
        
        console.log('Server logout response:', serverLogoutResponse.status);
        
        // 2. Get current user token for revocation (if available)
        let currentToken = null;
        if (firebase.auth().currentUser) {
          try {
            currentToken = await firebase.auth().currentUser.getIdToken();
            console.log('Retrieved user token for revocation');
          } catch (tokenError) {
            console.warn('Could not retrieve user token for revocation:', tokenError);
          }
        }
        
        // 3. Sign out from Firebase
        await firebase.auth().signOut();
        console.log('Successfully signed out from Firebase');
        
        // 4. Revoke the token if we have one
        if (currentToken) {
          try {
            const revokeResponse = await fetch('/api/auth/revoke-token', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
              },
              body: JSON.stringify({ token: currentToken })
            });
            
            if (revokeResponse.ok) {
              console.log('Successfully revoked Firebase token');
            } else {
              console.warn('Failed to revoke token:', await revokeResponse.text());
            }
          } catch (revokeError) {
            console.error('Error revoking token:', revokeError);
          }
        }
        
        // 5. Clear all Firebase storage
        this.clearFirebaseStorage();
        
        // 6. Set Firebase persistence to NONE to prevent auto-relogin
        await firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);
        console.log('Set Firebase persistence to NONE');
        
      } catch (error) {
        console.error('Error during signout process:', error);
      } finally {
        // Hide loading when done
        if (window.LoadingManager) {
          window.LoadingManager.hideLoading();
        }
        
        // Call the completion callback
        if (onComplete && typeof onComplete === 'function') {
          onComplete();
        }
        
        // Reload the page or redirect to ensure clean state
        window.location.href = '/logout_cleanup';
      }
    },
    
    /**
     * Clear all Firebase-related storage
     */
    clearFirebaseStorage: function() {
      console.log('Clearing all Firebase storage');
      
      // Clear localStorage
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key && (
            key.startsWith('firebase:') || 
            key.includes('firebase') || 
            key.includes('auth') ||
            key.includes('user')
        )) {
          console.log('Removing localStorage item:', key);
          localStorage.removeItem(key);
        }
      }
      
      // Clear sessionStorage
      for (let i = sessionStorage.length - 1; i >= 0; i--) {
        const key = sessionStorage.key(i);
        if (key && (
            key.startsWith('firebase:') || 
            key.includes('firebase') || 
            key.includes('auth') ||
            key.includes('user')
        )) {
          console.log('Removing sessionStorage item:', key);
          sessionStorage.removeItem(key);
        }
      }
      
      // Clear IndexedDB
      try {
        const dbNames = ['firebaseLocalStorageDb', 'firebase-heartbeat-database'];
        dbNames.forEach(dbName => {
          const req = indexedDB.deleteDatabase(dbName);
          req.onsuccess = () => console.log(`Successfully deleted IndexedDB: ${dbName}`);
          req.onerror = (e) => console.error(`Error deleting IndexedDB ${dbName}: ${e.target.error}`);
        });
      } catch (e) {
        console.error('Error clearing IndexedDB:', e);
      }
      
      // Clear cookies that might be related to Firebase
      document.cookie.split(';').forEach(cookie => {
        const cookieName = cookie.split('=')[0].trim();
        if (cookieName.includes('firebase') || cookieName.includes('auth')) {
          document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
          console.log('Cleared cookie:', cookieName);
        }
      });
    },
    
    /**
     * Get the current authenticated user
     * @returns {Object|null} Firebase user object or null if not authenticated
     */
    getCurrentUser: function() {
      if (!isInitialized) {
        console.warn('FirebaseAuthManager not initialized before getCurrentUser');
      }
      return currentUser;
    },
    
    /**
     * Check if auth state check is complete
     * @returns {boolean} True if auth state check is complete
     */
    isAuthStateReady: function() {
      return isAuthCheckComplete;
    },
    
    /**
     * Check if user is currently authenticated
     * @returns {boolean} True if user is authenticated
     */
    isAuthenticated: function() {
      return !!currentUser;
    }
  };
})();
