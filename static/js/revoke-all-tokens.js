// Revoke all tokens for a user
async function revokeAllTokens(uid, email) {
    console.log(`Revoking all tokens for ${email} (${uid})`);
    logBuffer = [`--- Token Revocation for ${email} ---\n`];
    updateDebugOutput();
    
    try {
        // Get current token if possible
        let currentToken = null;
        try {
            const currentUser = firebase.auth().currentUser;
            if (currentUser) {
                currentToken = await currentUser.getIdToken();
                logBuffer.push('✅ Retrieved token for revocation');
            }
        } catch (e) {
            logBuffer.push(`❌ Error getting token: ${e.message}`);
        }
        updateDebugOutput();
        
        // Build the revocation payload
        const payload = { user_id: uid };
        if (currentToken) {
            payload.token = currentToken;
        }
        
        // Call the token revocation API
        try {
            logBuffer.push(`Calling token revocation API with payload: ${JSON.stringify(payload)}`);
            const revokeResponse = await fetch('/api/auth/revoke-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                },
                body: JSON.stringify(payload)
            });
            
            if (revokeResponse.ok) {
                const result = await revokeResponse.json();
                logBuffer.push('✅ Successfully revoked all tokens for user');
                logBuffer.push(`Server response: ${JSON.stringify(result)}`);
            } else {
                const errorText = await revokeResponse.text();
                logBuffer.push(`❌ Failed to revoke tokens: ${errorText}`);
            }
        } catch (e) {
            logBuffer.push(`❌ Error calling revocation API: ${e.message}`);
        }
        updateDebugOutput();
        
        // Show completion message
        logBuffer.push('\n✅ Token revocation process complete!');
        updateDebugOutput();
    } catch (e) {
        logBuffer.push(`❌ Token revocation error: ${e.message}`);
        updateDebugOutput();
    }
}
