# Token Usage & Subscription System Documentation

## Overview

This document explains the implementation of the subscription and token usage tracking system for LightYearAI. The system consists of:

1. **Token Usage Tracking**: Monitors token consumption per user per day
2. **Subscription Management**: Handles paid subscriptions via Stripe
3. **Admin Dashboard**: Provides oversight of token usage and user management
4. **Automated Reset**: Resets daily token counters at midnight UTC

## Data Structure in Firestore

### Collections and Documents

- `users/{userId}` - User profile information
  - `plan`: String ('free' or 'premium')
  - `stripe_customer_id`: String (Stripe customer ID)
  - `stripe_subscription_id`: String (Stripe subscription ID)
  - `subscription_status`: String ('active', 'canceled', etc.)
  - `subscription_end_date`: Timestamp (end date for subscription)
  - `is_admin`: Boolean (whether user has admin privileges)
  - `custom_token_limit`: Number (optional custom limit)

- `token_usage/{userId}` - Container for user's token usage records
  - `daily/{date}` - Daily token usage subcollection
    - `tokens_used`: Number (tokens used on this date)
    - `date`: String (YYYY-MM-DD format)
    - `created_at`: Timestamp
    - `last_updated`: Timestamp

- `token_usage_monthly/{month}` - Monthly aggregated token usage
  - `tokens_used`: Number (total tokens used by all users this month)
  - `month`: String (YYYY-MM format)
  - `created_at`: Timestamp
  - `last_updated`: Timestamp
  - `budget_limit`: Number (monthly token budget)

## Token Tracking Implementation

The system tracks tokens used in each API call with these steps:

1. Before each API call, `check_user_token_limit()` verifies if the user can continue
2. After generating AI content, `track_token_usage_for_api_call()` counts tokens in both prompt and response
3. The tokens are recorded in both the user's daily document and the monthly aggregated document
4. Transactions are used to ensure atomic updates to the token counts

Token counting uses the `tiktoken` library which provides accurate token counting for large language models. A fallback character-based approximation is used if `tiktoken` fails.

## Subscription System

### Subscription Plans

- **Free Plan**: ~30,000 tokens per day
- **Premium Plan**: ~100,000 tokens per day ($9/month)

### Stripe Integration

1. The `/create-checkout-session` endpoint creates a Stripe checkout session
2. After successful payment, Stripe sends a webhook to `/webhook/stripe`
3. The webhook handler updates the user's subscription status in Firestore
4. Users can view their subscription status on the `/account` page

### Webhook Events Handled

- `checkout.session.completed`: Initial subscription created
- `customer.subscription.updated`: Subscription status changes
- `customer.subscription.deleted`: Subscription canceled

## Automated Reset System

Daily token usage counters reset at midnight UTC through:

1. **Firebase Cloud Functions**: The `scheduledResetTokenUsage` function runs at midnight UTC via a Pub/Sub trigger
2. **HTTP Endpoint**: The `resetDailyTokenUsage` function can be triggered via HTTP for manual resets
3. **Monthly Initialization**: The `initializeMonthlyUsage` function sets up a new monthly tracking document on the 1st of each month

## Global Budget Management

To prevent exceeding the 100 PLN (~$27) monthly Gemini API budget:

1. Every API call checks the total monthly token usage
2. If the global budget (2 million tokens) is reached, the system prevents non-admin users from making new requests
3. The admin dashboard shows a warning when approaching budget limits
4. Admins can still use the system when the budget is exceeded to handle essential tasks

## User Notifications

Users are notified about their token usage through:

1. A toast notification when approaching or reaching limits
2. Status information on the account page
3. Error messages when trying to make requests after reaching limits

## Admin Features

The admin dashboard at `/admin` provides:

1. Overview of total users, premium users, and token usage
2. Token usage by user, sortable by consumption
3. Reset functionality for daily token counters
4. Ability to set custom token limits for specific users
5. Budget monitoring with percentage visualization

## Deployment Instructions

1. Set environment variables in `.env` file (see `.env.sample` for required variables)
2. Deploy Firebase functions using `deploy_functions.sh`
3. Set up Cloud Scheduler for automated resets (instructions printed after deployment)
4. Configure Stripe webhook in Stripe dashboard to point to `/webhook/stripe` endpoint

## Maintenance Tasks

- **Daily Reset Monitoring**: Check logs to ensure daily resets are working properly
- **Monthly Budget Review**: Adjust the global budget cap if necessary based on actual usage
- **Webhook Verification**: Periodically verify Stripe webhook delivery is functioning
- **Backup Strategy**: Regular backups of Firestore data using Firebase export tools

## Future Enhancements

- Implement tiered subscription plans with different token limits
- Add usage analytics and charts to user accounts
- Create a notification system for users approaching their limits
- Implement auto-scaling of budgets based on revenue
- Add family/team plans for shared token allocations