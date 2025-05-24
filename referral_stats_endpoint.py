"""
This file contains the fixed endpoint for referral stats.
Add this to your app.py or app_fixed.py file.
"""

@app.route('/api/referral/stats', methods=['GET'])
@login_required
def api_get_referral_stats():
    """Get the user's referral statistics with improved error handling."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            print("No user_id in session when requesting referral stats")
            return jsonify({
                'success': False,
                'error': 'Not authenticated',
                'total_count': 0,
                'pending_count': 0
            }), 401
        
        print(f"Fetching referral stats for user_id: {user_id}")
        stats = get_referral_stats(user_id)
        print(f"Referral stats: {stats}")
        
        return jsonify({
            'success': True,
            **stats
        })
    except Exception as e:
        print(f"Error in api_get_referral_stats: {str(e)}")
        # Return a valid JSON response even in case of error
        return jsonify({
            'success': False,
            'error': str(e),
            'total_count': 0,
            'pending_count': 0
        }), 500
