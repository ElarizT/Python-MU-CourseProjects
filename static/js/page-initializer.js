/**
 * Page Initialization Manager
 * 
 * This script handles common page initialization tasks:
 * 1. Firebase initialization
 * 2. Authentication state checking
 * 3. Loading screen management
 * 4. Redirect handling for protected pages
 */

(function() {
    'use strict';
    
    // Configuration
    const config = {
        // Routes that don't require authentication
        publicRoutes: ['/', '/login', '/signup', '/logout', '/logout_cleanup', '/forgot-password'],
        
        // Routes that should redirect to login if not authenticated
        protectedRoutes: ['/study', '/entertainment', '/proofread', '/presentation', '/account'],
        
        // Default redirect paths
        defaultRedirects: {
            whenLoggedIn: '/',
            whenLoggedOut: '/login',
            afterLogout: '/'
        },
          // Timeout settings
        timeouts: {
            initialAuthCheck: 3000,  // Max time to wait for initial auth check (ms) - reduced from 5000
            hideLoader: 100          // Delay before hiding loader (ms) - reduced from 500
        }
    };
    
    // State tracking
    let firebaseInitialized = false;
    let authCheckComplete = false;
    let currentUser = null;
    
    // Get Firebase config from meta tags
    function getFirebaseConfig() {
        try {
            return {
                apiKey: document.querySelector('meta[name="firebase-api-key"]')?.content,
                authDomain: document.querySelector('meta[name="firebase-auth-domain"]')?.content,
                projectId: document.querySelector('meta[name="firebase-project-id"]')?.content,
                storageBucket: document.querySelector('meta[name="firebase-storage-bucket"]')?.content,
                messagingSenderId: document.querySelector('meta[name="firebase-messaging-sender-id"]')?.content,
                appId: document.querySelector('meta[name="firebase-app-id"]')?.content
            };
        } catch (e) {
            console.error('Error getting Firebase config from meta tags:', e);
            return null;
        }
    }
    
    // Initialize Firebase
    function initializeFirebase() {
        // Skip if already initialized
        if (firebaseInitialized) {
            return true;
        }
        
        // Check if Firebase is available
        if (typeof firebase === 'undefined') {
            console.error('Firebase SDK not found');
            return false;
        }
        
        try {
            // Check if Firebase is already initialized
            if (firebase.apps.length > 0) {
                firebaseInitialized = true;
                return true;
            }
            
            // Get config
            const firebaseConfig = getFirebaseConfig();
            if (!firebaseConfig || !firebaseConfig.apiKey) {
                console.error('Invalid Firebase configuration');
                return false;
            }
            
            // Initialize Firebase app
            firebase.initializeApp(firebaseConfig);
            console.log('Firebase initialized successfully');
            firebaseInitialized = true;
            return true;
        } catch (e) {
            console.error('Error initializing Firebase:', e);
            return false;
        }
    }
    
    // Check if current route requires authentication
    function currentRouteRequiresAuth() {
        const currentPath = window.location.pathname;
        
        // Check if current path is in the protected routes list
        return config.protectedRoutes.some(route => {
            // Exact match
            if (route === currentPath) return true;
            
            // Prefix match for nested routes
            if (route.endsWith('/*') && currentPath.startsWith(route.slice(0, -2))) return true;
            
            return false;
        });
    }
      // Check if current route is public (no auth required)
    function isPublicRoute() {
        const currentPath = window.location.pathname;
        
        // Check for exact matches
        if (config.publicRoutes.includes(currentPath)) {
            return true;
        }
        
        // Check for static files and images
        if (currentPath.startsWith('/static/') || 
            currentPath.endsWith('.js') || 
            currentPath.endsWith('.css') ||
            currentPath.endsWith('.jpg') ||
            currentPath.endsWith('.png') ||
            currentPath.endsWith('.ico')) {
            return true;
        }
        
        // Check for root path
        if (currentPath === '/' || currentPath === '') {
            return true;
        }
        
        return false;
    }
    
    // Handle page access based on auth state
    function handlePageAccess(user) {
        const currentPath = window.location.pathname;
        
        // Check if user explicitly logged out
        const explicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true';
        
        // User is logged in
        if (user) {
            // Clear explicit logout flag if it exists
            if (explicitlyLoggedOut) {
                localStorage.removeItem('explicitly_logged_out');
            }
            
            // If on login or signup page, redirect to home
            if (currentPath === '/login' || currentPath === '/signup') {
                window.location.href = config.defaultRedirects.whenLoggedIn;
                return;
            }
        } 
        // User is not logged in
        else {
            // If on protected route, redirect to login
            if (currentRouteRequiresAuth()) {
                // Don't redirect if already on login page to avoid loops
                if (currentPath !== '/login') {
                    // Save current URL to redirect back after login
                    const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
                    window.location.href = `${config.defaultRedirects.whenLoggedOut}?next=${returnUrl}`;
                    return;
                }
            }
        }
    }
      // Process authentication state
    function processAuthState(user) {
        currentUser = user;
        authCheckComplete = true;
        
        // Log authentication state
        console.log(`Auth check complete: User ${user ? 'is' : 'is not'} authenticated`);
        
        // Handle page access based on auth state
        handlePageAccess(user);
        
        // Hide loading screen immediately to prevent infinite loading
        if (window.LoadingManager) {
            window.LoadingManager.hideLoading();
        }
        
        // Signal that auth check is complete
        document.dispatchEvent(new CustomEvent('pageInitAuthComplete', {
            detail: { user: user }
        }));
    }    // Check authentication state
    function checkAuthState() {
        // First, hide the loading screen for the homepage immediately
        if (window.location.pathname === '/' || window.location.pathname === '') {
            console.log('Homepage detected in checkAuthState, hiding loading screen immediately');
            if (window.LoadingManager) {
                window.LoadingManager.hideLoading();
                
                // Still perform a background auth check for the homepage, but without blocking
                setTimeout(() => {
                    if (!authCheckComplete) {
                        console.log('Processing auth state for homepage in background');
                        processAuthState(null);
                    }
                }, 10); // Very short timeout for index page
                
                // Don't return here, still do the Firebase init but don't show loading again
            }
        }
        
        // Skip if Firebase isn't initialized
        if (!firebaseInitialized) {
            if (!initializeFirebase()) {
                console.error('Unable to check auth state: Firebase not initialized');
                
                // Hide loading even if we can't check auth
                if (window.LoadingManager) {
                    window.LoadingManager.hideLoading();
                }
                
                return;
            }
        }
        
        // Check explicitly logged out state
        const explicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true';
        
        // If explicitly logged out, set persistence to NONE
        if (explicitlyLoggedOut) {
            firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE)
                .catch(e => console.error('Error setting persistence to NONE:', e));
        }
        
        // Listen for auth state changes
        firebase.auth().onAuthStateChanged(user => {
            // If explicitly logged out but we have a user, force logout
            if (user && explicitlyLoggedOut) {
                console.warn('User detected after explicit logout, forcing sign out');
                
                if (window.FirebaseLogout) {
                    window.FirebaseLogout.logoutCompletely().then(() => {
                        processAuthState(null);
                    });
                } else {
                    // Fallback if FirebaseLogout is not available
                    firebase.auth().signOut().then(() => {
                        processAuthState(null);
                    }).catch(e => {
                        console.error('Error signing out:', e);
                        processAuthState(null);
                    });
                }
                return;
            }
            
            // Process normal auth state
            processAuthState(user);
        }, error => {
            console.error('Auth state change error:', error);
            
            // Still process as not authenticated on error
            processAuthState(null);
        });
        
        // Set a timeout to avoid hanging if Firebase auth is slow
        setTimeout(() => {
            if (!authCheckComplete) {
                console.warn('Auth check timed out, proceeding as unauthenticated');
                processAuthState(null);
            }
        }, config.timeouts.initialAuthCheck);
    }      // Initialize the page
    function initializePage() {
        // For public routes, let's not add loading delay
        const isPublic = isPublicRoute();
        
        // Show loading screen if available (only for non-public routes)
        if (window.LoadingManager && !isPublic) {
            window.LoadingManager.showLoading('Loading...');
        } else if (window.LoadingManager) {
            // For public routes, immediately hide any existing loading screen
            window.LoadingManager.hideLoading();
        }
        
        // Initialize Firebase
        const firebaseInitSuccess = initializeFirebase();
        
        // If Firebase fails to initialize and we're on a public route, 
        // hide loading screen immediately
        if (!firebaseInitSuccess && isPublic && window.LoadingManager) {
            window.LoadingManager.hideLoading();
            return;
        }
        
        // If we're on the homepage specifically, hide the loading screen immediately
        if (window.location.pathname === '/' && window.LoadingManager) {
            window.LoadingManager.hideLoading();
        }
        
        // Check auth state
        checkAuthState();
    }
    
    // Expose API for external use
    window.PageInitializer = {
        init: initializePage,
        getCurrentUser: () => currentUser,
        isAuthenticated: () => !!currentUser,
        isAuthCheckComplete: () => authCheckComplete
    };
    
    // Auto-initialize when document is ready
    document.addEventListener('DOMContentLoaded', initializePage);
})();
