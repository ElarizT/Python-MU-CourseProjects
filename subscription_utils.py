import os
import json
import time
from datetime import datetime, timedelta
import stripe
import firebase_admin
from firebase_admin import firestore, auth
import tiktoken
from flask import session, g, flash, jsonify

# Initialize Stripe with the API key
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = STRIPE_API_KEY

# Plan configurations
FREE_PLAN_DAILY_LIMIT = 25000  # 25k tokens per day
PAID_PLAN_DAILY_LIMIT = 100000  # 100k tokens per day
MONTHLY_PRICE = 900  # $9.00 in cents

# Total monthly budget limit for all users (50 PLN ≈ $12.50)
TOTAL_MONTHLY_BUDGET_TOKENS = 2000000  # 2 million tokens total monthly budget

# Global variable for the Firestore client
_db = None

def get_db():
    """Get the Firestore database client, initializing it if necessary."""
    global _db
    if (_db is None):
        # Check if Firebase app is already initialized
        if not firebase_admin._apps:
            # If not initialized, don't try to initialize here
            # The main app.py will handle initialization
            pass
        else:
            # If already initialized, create the client
            _db = firestore.client()
    return _db

def count_tokens(text, model="gpt-4"):
    """
    Count the number of tokens in a text string.
    Using tiktoken for more accurate token counting.
    """
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")  # Using GPT-4 encoding as an approximation for Gemini
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error counting tokens: {e}")
        # Fallback to approximate token count (1 token ≈ 4 chars for English text)
        return len(text) // 4

def get_user_subscription(user_id):
    """Get the subscription status of a user."""
    if not user_id:
        return None
    
    db = get_db()
    if not db:
        return {
            'plan': 'free',
            'stripe_customer_id': None,
            'stripe_subscription_id': None,
            'subscription_status': None,
            'subscription_end_date': None,
        }
    
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        # Initialize user document if it doesn't exist
        user_ref.set({
            'plan': 'free',
            'created_at': firestore.SERVER_TIMESTAMP,
        })
        return {
            'plan': 'free',
            'stripe_customer_id': None,
            'stripe_subscription_id': None,
            'subscription_status': None,
            'subscription_end_date': None,
        }
    
    user_data = user_doc.to_dict()
    return {
        'plan': user_data.get('plan', 'free'),
        'stripe_customer_id': user_data.get('stripe_customer_id', None),
        'stripe_subscription_id': user_data.get('stripe_subscription_id', None),
        'subscription_status': user_data.get('subscription_status', None),
        'subscription_end_date': user_data.get('subscription_end_date', None),
    }

def get_user_daily_token_usage(user_id):
    """Get the user's token usage for today."""
    if not user_id:
        return 0
    
    db = get_db()
    if not db:
        return 0
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    usage_doc = db.collection('token_usage').document(user_id).collection('daily').document(today).get()
    
    if not usage_doc.exists:
        return 0
    
    return usage_doc.to_dict().get('tokens_used', 0)

def increment_user_token_usage(user_id, tokens_used):
    """Increment the user's token usage for today and update monthly totals."""
    if not user_id:
        return

    db = get_db()
    if not db:
        return

    today = datetime.now().strftime('%Y-%m-%d')
    current_month = datetime.now().strftime('%Y-%m')
    
    # Update daily usage
    daily_ref = db.collection('token_usage').document(user_id).collection('daily').document(today)
    
    # Use transactions to safely update the token count
    @firestore.transactional
    def update_daily_usage(transaction, doc_ref):
        doc = doc_ref.get(transaction=transaction)
        if doc.exists:
            current_usage = doc.to_dict().get('tokens_used', 0)
            transaction.update(doc_ref, {
                'tokens_used': current_usage + tokens_used,
                'last_updated': firestore.SERVER_TIMESTAMP
            })
        else:
            transaction.set(doc_ref, {
                'tokens_used': tokens_used,
                'date': today,
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_updated': firestore.SERVER_TIMESTAMP
            })
    
    # Update monthly usage for organization-wide tracking
    monthly_ref = db.collection('token_usage_monthly').document(current_month)
    
    @firestore.transactional
    def update_monthly_usage(transaction, doc_ref):
        doc = doc_ref.get(transaction=transaction)
        if doc.exists:
            current_usage = doc.to_dict().get('tokens_used', 0)
            transaction.update(doc_ref, {
                'tokens_used': current_usage + tokens_used,
                'last_updated': firestore.SERVER_TIMESTAMP
            })
        else:
            transaction.set(doc_ref, {
                'tokens_used': tokens_used,
                'month': current_month,
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_updated': firestore.SERVER_TIMESTAMP
            })
    
    # Execute transactions
    transaction = db.transaction()
    update_daily_usage(transaction, daily_ref)
    
    transaction = db.transaction()
    update_monthly_usage(transaction, monthly_ref)

def check_user_token_limit(user_id):
    """
    Check if the user has exceeded their token limit.
    Returns:
    - (True, remaining) if user can continue
    - (False, 0) if user has reached their limit
    """
    if not user_id:
        return False, 0
    
    db = get_db()
    if not db:
        # If DB connection isn't available, allow usage to prevent blocking users
        return True, FREE_PLAN_DAILY_LIMIT
    
    # Get user's subscription status
    subscription = get_user_subscription(user_id)
    plan = subscription.get('plan', 'free')
    
    # Get daily limit based on plan
    daily_limit = FREE_PLAN_DAILY_LIMIT if plan == 'free' else PAID_PLAN_DAILY_LIMIT
    
    # Get current usage
    current_usage = get_user_daily_token_usage(user_id)
    
    # Check if total monthly budget has been exceeded
    current_month = datetime.now().strftime('%Y-%m')
    monthly_usage_doc = db.collection('token_usage_monthly').document(current_month).get()
    total_monthly_usage = 0
    if monthly_usage_doc.exists:
        total_monthly_usage = monthly_usage_doc.to_dict().get('tokens_used', 0)
    
    # If total budget is exceeded, limit everyone except admins
    if total_monthly_usage >= TOTAL_MONTHLY_BUDGET_TOKENS:
        # Check if user is admin before limiting
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists and user_doc.to_dict().get('is_admin', False):
            # Admins can continue using
            remaining = daily_limit - current_usage
            return remaining > 0, remaining
        else:
            # Non-admins are limited when budget is exceeded
            return False, 0
    
    # Check individual limits
    remaining = daily_limit - current_usage
    return remaining > 0, remaining

def track_token_usage_for_api_call(user_id, prompt, response_text, estimated_tokens=None):
    """
    Track token usage for an API call, counting both prompt and response tokens.
    
    Args:
        user_id: The ID of the user making the request
        prompt: The user's prompt or query text
        response_text: The response text from the AI
        estimated_tokens: Optional pre-calculated token count (if provided, skips counting)
        
    Returns:
        The total tokens used in this call
    """
    if not user_id:
        return 0
    
    # Use estimated tokens if provided, otherwise count them
    if estimated_tokens is not None:
        total_tokens = estimated_tokens
    else:
        # Count tokens in the request
        prompt_tokens = count_tokens(prompt)
        
        # Count tokens in the response
        response_tokens = count_tokens(response_text)
        
        # Total tokens used in this call
        total_tokens = prompt_tokens + response_tokens
    
    # Log the usage
    increment_user_token_usage(user_id, total_tokens)
    
    return total_tokens

def create_stripe_checkout_session(user_id, email, success_url, cancel_url):
    """Create a Stripe checkout session for subscription."""
    try:
        db = get_db()
        if not db:
            return None
            
        # Check if user already has a Stripe customer ID
        user_doc = db.collection('users').document(user_id).get()
        
        customer_id = None
        if user_doc.exists:
            user_data = user_doc.to_dict()
            customer_id = user_data.get('stripe_customer_id')
        
        # If no customer ID, create a new customer
        if not customer_id:
            customer = stripe.Customer.create(
                email=email,
                metadata={
                    'user_id': user_id
                }
            )
            customer_id = customer.id
            
            # Update the user document with the Stripe customer ID
            db.collection('users').document(user_id).update({
                'stripe_customer_id': customer_id,
                'email': email
            })
        
        # Create the checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'LightYearAI Premium Plan',
                        'description': 'Monthly subscription for enhanced token limits',
                    },
                    'unit_amount': MONTHLY_PRICE,
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        
        return checkout_session.id
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return None

# Import referral utilities
from referral_utils import complete_referral

def handle_stripe_webhook(payload, signature):
    """Handle Stripe webhook events."""
    try:
        db = get_db()
        if not db:
            return {'success': False, 'error': 'Database connection not available'}
            
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_id = session.get('customer')
            subscription_id = session.get('subscription')
            
            # Find the user with this customer ID
            users_ref = db.collection('users').where('stripe_customer_id', '==', customer_id).get()
            
            for user_doc in users_ref:
                user_id = user_doc.id
                
                # Update user with subscription details
                db.collection('users').document(user_id).update({
                    'plan': 'premium',
                    'stripe_subscription_id': subscription_id,
                    'subscription_status': 'active',
                    'subscription_updated_at': firestore.SERVER_TIMESTAMP
                })
                
                # Process referral if this user was referred
                user_data = user_doc.to_dict()
                if user_data.get('referred_by') and user_data.get('referral_code_used'):
                    # Complete the referral and reward the referrer with the same plan type
                    complete_referral(user_id, 'premium')
        
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            customer_id = subscription.get('customer')
            subscription_id = subscription.get('id')
            status = subscription.get('status')
            
            # Find the user with this customer ID
            users_ref = db.collection('users').where('stripe_customer_id', '==', customer_id).get()
            
            for user_doc in users_ref:
                user_id = user_doc.id
                
                # Update subscription status
                update_data = {
                    'subscription_status': status,
                    'subscription_updated_at': firestore.SERVER_TIMESTAMP
                }
                
                # If active, set to premium plan, otherwise set to free
                if status == 'active':
                    update_data['plan'] = 'premium'
                else:
                    update_data['plan'] = 'free'
                
                db.collection('users').document(user_id).update(update_data)
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            customer_id = subscription.get('customer')
            
            # Find the user with this customer ID
            users_ref = db.collection('users').where('stripe_customer_id', '==', customer_id).get()
            
            for user_doc in users_ref:
                user_id = user_doc.id
                
                # Downgrade to free plan
                db.collection('users').document(user_id).update({
                    'plan': 'free',
                    'subscription_status': 'canceled',
                    'subscription_updated_at': firestore.SERVER_TIMESTAMP
                })
                
        return {'success': True}
    except Exception as e:
        print(f"Error handling webhook: {e}")
        return {'success': False, 'error': str(e)}

def reset_all_daily_token_usage():
    """
    Reset all users' daily token usage. This would be triggered by Cloud Scheduler.
    """
    db = get_db()
    if not db:
        return False
        
    # Get all documents in the token_usage collection
    usage_docs = db.collection('token_usage').get()
    
    batch = db.batch()
    today = datetime.now().strftime('%Y-%m-%d')
    
    for usage_doc in usage_docs:
        # Create a new empty document for today for each user
        new_daily_ref = db.collection('token_usage').document(usage_doc.id).collection('daily').document(today)
        batch.set(new_daily_ref, {
            'tokens_used': 0,
            'date': today,
            'created_at': firestore.SERVER_TIMESTAMP,
            'last_updated': firestore.SERVER_TIMESTAMP
        })
    
    # Commit the batch
    batch.commit()
    
    return True

def get_admin_dashboard_data():
    """Get data for the admin dashboard."""
    db = get_db()
    if not db:
        return {
            'total_users': 0,
            'premium_users': 0,
            'daily_usage': 0,
            'monthly_usage': 0,
            'budget_percentage': 0,
            'usage_by_user': [],
            'monthly_budget': TOTAL_MONTHLY_BUDGET_TOKENS,
            'today': datetime.now().strftime('%Y-%m-%d')
        }
        
    # Get total users
    users_count = len(list(db.collection('users').stream()))
    
    # Get premium users count
    premium_users = list(db.collection('users').where('plan', '==', 'premium').stream())
    premium_count = len(premium_users)
    
    # Get daily token usage for today
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    current_month = datetime.now().strftime('%Y-%m')
    
    # Get today's usage across all users
    daily_usage = 0
    usage_by_user = []
    
    # Collect all users' usage for today
    users = list(db.collection('users').stream())
    
    for user in users:
        user_id = user.id
        user_data = user.to_dict()
        
        today_usage_doc = db.collection('token_usage').document(user_id).collection('daily').document(today).get()
        today_usage = 0
        if today_usage_doc.exists:
            today_usage = today_usage_doc.to_dict().get('tokens_used', 0)
        
        yesterday_usage_doc = db.collection('token_usage').document(user_id).collection('daily').document(yesterday).get()
        yesterday_usage = 0
        if yesterday_usage_doc.exists:
            yesterday_usage = yesterday_usage_doc.to_dict().get('tokens_used', 0)
        
        daily_usage += today_usage
        
        # Add to user-specific usage list
        usage_by_user.append({
            'user_id': user_id,
            'email': user_data.get('email', 'Unknown'),
            'plan': user_data.get('plan', 'free'),
            'today_usage': today_usage,
            'yesterday_usage': yesterday_usage,
            'subscription_status': user_data.get('subscription_status', None)
        })
    
    # Sort by usage (highest first)
    usage_by_user.sort(key=lambda x: x['today_usage'], reverse=True)
    
    # Get monthly total usage
    monthly_usage_doc = db.collection('token_usage_monthly').document(current_month).get()
    monthly_usage = 0
    if monthly_usage_doc.exists:
        monthly_usage = monthly_usage_doc.to_dict().get('tokens_used', 0)
    
    # Calculate budget status
    budget_percentage = (monthly_usage / TOTAL_MONTHLY_BUDGET_TOKENS) * 100 if TOTAL_MONTHLY_BUDGET_TOKENS > 0 else 0
    
    return {
        'total_users': users_count,
        'premium_users': premium_count,
        'daily_usage': daily_usage,
        'monthly_usage': monthly_usage,
        'budget_percentage': budget_percentage,
        'usage_by_user': usage_by_user,
        'monthly_budget': TOTAL_MONTHLY_BUDGET_TOKENS,
        'today': today
    }

def update_user_limit(user_id, new_limit):
    """Update a user's custom token limit."""
    if not user_id:
        return False
    
    db = get_db()
    if not db:
        return False
        
    db.collection('users').document(user_id).update({
        'custom_token_limit': new_limit,
        'limit_updated_at': firestore.SERVER_TIMESTAMP
    })
    
    return True

def get_user_limit(user_id):
    """Get a user's token limit, considering custom limits if set."""
    if not user_id:
        return FREE_PLAN_DAILY_LIMIT
    
    db = get_db()
    if not db:
        return FREE_PLAN_DAILY_LIMIT
        
    user_doc = db.collection('users').document(user_id).get()
    if not user_doc.exists:
        return FREE_PLAN_DAILY_LIMIT
    
    user_data = user_doc.to_dict()
    
    # Check for custom limit first
    if 'custom_token_limit' in user_data:
        return user_data['custom_token_limit']
    
    # Otherwise use plan-based limit
    plan = user_data.get('plan', 'free')
    return FREE_PLAN_DAILY_LIMIT if plan == 'free' else PAID_PLAN_DAILY_LIMIT