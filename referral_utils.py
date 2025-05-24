import os
import uuid
import time
from datetime import datetime, timedelta
from flask import g, session
import firebase_admin
from firebase_admin import firestore

# Maximum number of successful referrals per month (4 referrals * 7 days = 28 days max reward)
MAX_MONTHLY_REFERRALS = 4

def get_db():
    """Get the Firestore database client with logging for debugging."""
    try:
        from firebase_admin import firestore
        db_client = firestore.client()
        print("Firestore client initialized successfully.")
        return db_client
    except Exception as e:
        print(f"Error initializing Firestore client: {e}")
        return None

def generate_referral_code(user_id):
    """
    Generate a unique referral code for a user.
    If a referral code already exists, return it instead.
    """
    db = get_db()
    if not db:
        return None
    
    # Check if user already has a referral code
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if user_doc.exists and user_doc.to_dict().get('referral_code'):
        # User already has a referral code
        return user_doc.to_dict().get('referral_code')
    
    # Generate a new referral code using first 8 chars of a UUID
    referral_code = str(uuid.uuid4()).replace('-', '')[:8]
    
    # Make sure it's unique by checking against existing codes
    existing_codes = db.collection('users').where('referral_code', '==', referral_code).get()
    
    # If code already exists, generate a new one
    while len(list(existing_codes)) > 0:
        referral_code = str(uuid.uuid4()).replace('-', '')[:8]
        existing_codes = db.collection('users').where('referral_code', '==', referral_code).get()
    
    # Save the referral code to the user's document using set with merge=True
    # This ensures the fields are added properly without overwriting existing data
    user_ref.set({
        'referral_code': referral_code,
        'referral_created_at': firestore.SERVER_TIMESTAMP
    }, merge=True)
    
    return referral_code

def get_referral_code(user_id):
    """Get the referral code for a given user."""
    db = get_db()
    if not db or not user_id:
        return None
    
    # Check if user already has a referral code
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if user_doc.exists and user_doc.to_dict().get('referral_code'):
        # User already has a referral code
        return user_doc.to_dict().get('referral_code')
    
    # If no referral code exists, generate a new one
    return generate_referral_code(user_id)

def get_referral_count(user_id):
    """Get the number of successful referrals made by a user."""
    db = get_db()
    if not db or not user_id:
        return 0
    
    # Check referrals collection for this user's success count
    try:
        referrals = db.collection('referrals').where('referrer_id', '==', user_id).where('status', '==', 'completed').get()
        return len(list(referrals))
    except Exception as e:
        print(f"Error getting referral count: {e}")
        return 0

def get_monthly_referral_count(user_id):
    """Get the number of successful referrals made by a user in the current month."""
    db = get_db()
    if not db or not user_id:
        return 0
    
    # Get current month start date
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    
    # Check referrals collection for this user's success count within the current month
    try:
        referrals = db.collection('referrals')\
            .where('referrer_id', '==', user_id)\
            .where('status', '==', 'completed')\
            .where('completed_at', '>=', month_start)\
            .get()
        
        return len(list(referrals))
    except Exception as e:
        print(f"Error getting monthly referral count: {e}")
        return 0

def track_referral(referral_code, referred_user_id):
    """
    Track a new referral in the system.
    Called when a new user signs up using a referral code.
    Returns the referrer's user ID if successful, None otherwise.
    """
    db = get_db()
    if not db or not referral_code or not referred_user_id:
        return None
    
    # Find the referrer based on the referral code
    referrers = db.collection('users').where('referral_code', '==', referral_code).get()
    
    if not referrers or len(list(referrers)) == 0:
        # Invalid referral code
        return None
    
    referrer = list(referrers)[0]
    referrer_id = referrer.id
    
    # Don't allow self-referrals
    if referrer_id == referred_user_id:
        return None
    
    # Create a new referral record
    referral_ref = db.collection('referrals').document()
    referral_ref.set({
        'referrer_id': referrer_id,
        'referred_id': referred_user_id,
        'status': 'pending',  # Will be updated to 'completed' after payment
        'created_at': firestore.SERVER_TIMESTAMP
    })
    
    # Update the referred user to track who referred them
    db.collection('users').document(referred_user_id).update({
        'referred_by': referrer_id,
        'referral_code_used': referral_code
    })
    
    return referrer_id

def complete_referral(referred_user_id, plan_type):
    """
    Complete a referral after the referred user has made a payment.
    This will add the 7-day reward to the referrer's account.
    """
    db = get_db()
    if not db or not referred_user_id:
        return False
    
    # Find the referral record
    referrals = db.collection('referrals')\
        .where('referred_id', '==', referred_user_id)\
        .where('status', '==', 'pending')\
        .get()
    
    if not referrals or len(list(referrals)) == 0:
        # No pending referral found
        return False
    
    referral = list(referrals)[0]
    referrer_id = referral.to_dict().get('referrer_id')
    
    # Check if referrer has reached the monthly limit
    monthly_count = get_monthly_referral_count(referrer_id)
    if monthly_count >= MAX_MONTHLY_REFERRALS:
        # Update referral status but don't add reward (limit reached)
        referral.reference.update({
            'status': 'completed',
            'completed_at': firestore.SERVER_TIMESTAMP,
            'plan_type': plan_type,
            'reward_applied': False,
            'reward_reason': 'monthly_limit_reached'
        })
        return False
    
    # Get the referrer's current subscription
    user_ref = db.collection('users').document(referrer_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return False
    
    user_data = user_doc.to_dict()
    current_plan = user_data.get('plan', 'free')
    subscription_end_date = user_data.get('subscription_end_date')
    
    # Calculate reward end date (7 days from now)
    now = datetime.now()
    reward_end_date = now + timedelta(days=7)
    
    # If referrer is already on a paid plan, extend it by 7 days
    if current_plan != 'free' and subscription_end_date:
        # Parse the subscription end date if it's a string
        if isinstance(subscription_end_date, str):
            try:
                subscription_end_date = datetime.fromisoformat(subscription_end_date)
            except ValueError:
                subscription_end_date = now
        
        # If it's a Firestore timestamp, convert to datetime
        elif hasattr(subscription_end_date, 'timestamp'):
            subscription_end_date = datetime.fromtimestamp(subscription_end_date.timestamp())
        
        # Extend current subscription by 7 days
        new_end_date = subscription_end_date + timedelta(days=7)
        
        # Update the user's subscription data
        user_ref.update({
            'subscription_end_date': new_end_date,
            'referral_rewards': firestore.ArrayUnion([{
                'referral_id': referral.id,
                'reward_days': 7,
                'plan_type': plan_type,
                'applied_at': firestore.SERVER_TIMESTAMP
            }])
        })
    else:
        # Referrer is on free plan, give them a 7-day premium trial of the same plan
        user_ref.update({
            'plan': plan_type,  # Set to the same plan as the referred user
            'referral_plan': True,  # Flag to indicate this is a referral-based plan
            'referral_plan_expires_at': reward_end_date,
            'referral_rewards': firestore.ArrayUnion([{
                'referral_id': referral.id,
                'reward_days': 7,
                'plan_type': plan_type,
                'applied_at': firestore.SERVER_TIMESTAMP
            }])
        })
    
    # Update the referral record
    referral.reference.update({
        'status': 'completed',
        'completed_at': firestore.SERVER_TIMESTAMP,
        'plan_type': plan_type,
        'reward_applied': True
    })
    
    return True

def check_expired_referral_plans():
    """
    Check for and process expired referral plans.
    This should be run daily to revert users back to free plan when their referral reward expires.
    """
    db = get_db()
    if not db:
        return False
    
    now = datetime.now()
    
    # Find users with expired referral plans
    expired_users = db.collection('users')\
        .where('referral_plan', '==', True)\
        .where('referral_plan_expires_at', '<', now)\
        .get()
    
    for user_doc in expired_users:
        user_ref = user_doc.reference
        
        # Check if they have a paid subscription
        user_data = user_doc.to_dict()
        if user_data.get('subscription_status') == 'active' and user_data.get('stripe_subscription_id'):
            # User has a paid subscription, just remove the referral plan flag
            user_ref.update({
                'referral_plan': False,
                'referral_plan_expires_at': firestore.DELETE_FIELD
            })
        else:
            # Revert to free plan
            user_ref.update({
                'plan': 'free',
                'referral_plan': False,
                'referral_plan_expires_at': firestore.DELETE_FIELD
            })
    
    return True

def get_referral_stats(user_id):
    """Get the referral statistics for a user."""
    db = get_db()
    if not db or not user_id:
        return {
            'total_count': 0,
            'monthly_count': 0,
            'monthly_limit': MAX_MONTHLY_REFERRALS,
            'pending_count': 0
        }
    
    # Get total completed referrals
    completed = db.collection('referrals')\
        .where('referrer_id', '==', user_id)\
        .where('status', '==', 'completed')\
        .get()
    total_count = len(list(completed))
    
    # Get pending referrals
    pending = db.collection('referrals')\
        .where('referrer_id', '==', user_id)\
        .where('status', '==', 'pending')\
        .get()
    pending_count = len(list(pending))
    
    # Get monthly referral count
    monthly_count = get_monthly_referral_count(user_id)
    
    return {
        'total_count': total_count,
        'monthly_count': monthly_count,
        'monthly_limit': MAX_MONTHLY_REFERRALS,
        'pending_count': pending_count
    }