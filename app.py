import os
import json
import uuid
import tempfile
import sys
import re
import time
import random
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, g, flash, make_response
from file_optimizer import convert_to_serializable, read_csv_optimized
from json_utils import EnhancedJSONEncoder, convert_to_json_serializable

# Define a safer jsonify function that handles non-serializable types
def safe_jsonify(data):
    """
    A safer version of jsonify that handles non-JSON-serializable types like NumPy arrays/values.
    Falls back to string representation for truly unserializable objects.
    """
    try:
        # First try normal jsonify
        return jsonify(data)
    except (TypeError, ValueError, OverflowError) as e:
        # On serialization error, try to convert the data
        try:
            # convert_to_json_serializable is already imported at module level
            serializable_data = convert_to_json_serializable(data)
            return jsonify(serializable_data)
        except Exception as e2:
            # If all else fails, return an error message
            print(f"JSON Serialization Error: {e} -> {e2}")
            return jsonify({
                'error': 'Failed to serialize response',
                'details': str(e)
            }), 500
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import requests
import firebase_admin
from firebase_admin import credentials, auth, firestore
from subscription_utils import (
    track_token_usage_for_api_call, 
    check_user_token_limit,
    get_user_subscription,
    create_stripe_checkout_session,
    handle_stripe_webhook,
    get_admin_dashboard_data,
    update_user_limit,
    reset_all_daily_token_usage,
    get_user_daily_token_usage
)
import shutil
import stripe
from agents import (
    initialize_agent, 
    execute_agent_with_plan,
    get_agent, 
    proofread_and_summarize_plan,
    study_assistant_plan
)
from agents.utils import track_agent_usage
from excel_generator import generate_excel_from_prompt
from presentation_builder import (
    generate_presentation_from_file,
    generate_presentation_from_text
)
from llm_presentation_generator import generate_presentation_from_topic
# Import referral utilities
from referral_utils import (
    get_referral_code, 
    get_referral_stats, 
    track_referral,
    complete_referral
)

# Import Firebase diagnostics
from firebase_diagnostics import register_firebase_diagnostics

# Get environment variables
from referral_utils import check_expired_referral_plans

# Load environment variables
load_dotenv()

# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Token usage limits
FREE_PLAN_DAILY_LIMIT = 25000  # 25K tokens per day for free users
PAID_PLAN_DAILY_LIMIT = 100000  # 100K tokens per day for premium users
TOTAL_MONTHLY_BUDGET_TOKENS = int(os.getenv("MONTHLY_TOKEN_BUDGET", "1000000"))  # Default 1M tokens monthly budget

# Print current directory and files for debugging
print("Current working directory:", os.getcwd())
print("Directory contents:", os.listdir())
if (os.path.exists('templates')):
    print("Templates directory contents:", os.listdir('templates'))
else:
    print("Templates directory not found in current directory")

# Try to find template directory
template_dir = None
possible_template_dirs = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
    os.path.join(os.getcwd(), 'templates'),
    '/opt/render/project/src/templates',
]

for dir_path in possible_template_dirs:
    if (os.path.isdir(dir_path)):
        template_dir = dir_path
        print(f"Found template directory at: {template_dir}")
        break

if (not template_dir):
    print("Could not find templates directory!")
    # As a fallback, use the first option anyway
    template_dir = possible_template_dirs[0]

# Initialize Flask app with explicit static and template folders
app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Set a secret key for the session
secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY")
if not secret_key:
    # Generate a random secret key if none is provided
    import secrets
    secret_key = secrets.token_hex(24)  # 48 character random hex string
    print("Warning: Using a randomly generated secret key. Sessions will not persist between restarts.")
else:
    print("Using provided secret key from environment variables.")

app.secret_key = secret_key

# Configure custom JSON encoder to handle NumPy types and other non-standard JSON serializable types
try:
    from json_utils import EnhancedJSONEncoder
    app.json_encoder = EnhancedJSONEncoder
    print("[JSON CONFIG] Using enhanced JSON encoder for improved serialization")
except ImportError:
    print("[JSON CONFIG] Warning: Could not load enhanced JSON encoder. Some data types may not serialize properly.")

# Add a context processor to provide the current datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Set session lifetime to 30 days
app.permanent_session_lifetime = timedelta(days=30)

# Register Firebase diagnostics
register_firebase_diagnostics(app)

# Debug session configuration
print(f"[SESSION CONFIG] Secret key set: {'Yes' if app.secret_key else 'No'}")
print(f"[SESSION CONFIG] Session interface: {app.session_interface.__class__.__name__}")
print(f"[SESSION CONFIG] Session lifetime: {app.permanent_session_lifetime.total_seconds() / 86400} days")

# Initialize Firebase Admin SDK (only once)
if (not firebase_admin._apps):
    try:
        print("\n" + "="*30 + " FIREBASE INITIALIZATION " + "="*30)
        # First, try to get credentials from environment variables
        firebase_credentials_base64 = os.environ.get('FIREBASE_CREDENTIALS_BASE64')
        storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET', 'lightyearai-app.firebasestorage.app')
        
        # Use the bucket name as-is instead of trying to convert it
        print(f"Using Firebase Storage bucket: {storage_bucket}")
        
        if firebase_credentials_base64:
            print("Found FIREBASE_CREDENTIALS_BASE64 environment variable")
            # Decode base64 credentials and save to a temporary file
            import base64
            import tempfile
            
            # Decode the base64 string to JSON content
            try:
                print(f"Decoding base64 credentials (first 20 chars: {firebase_credentials_base64[:20]}...)")
                json_content = base64.b64decode(firebase_credentials_base64).decode('utf-8')
                
                # Debug: print part of decoded content to verify it's valid JSON
                print(f"Decoded credentials JSON starts with: {json_content[:50]}...")
                
                # Write the JSON to a temporary file
                temp_cred_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
                temp_cred_file.write(json_content)
                temp_cred_file.close()
                
                print(f"Wrote credentials to temporary file: {temp_cred_file.name}")
                
                # Initialize with the temporary credentials file
                cred = credentials.Certificate(temp_cred_file.name)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': storage_bucket,
                    'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', 'https://lightyearai-app-default-rtdb.europe-west1.firebasedatabase.app')
                })
                print(f"Firebase initialized with credentials from environment variable")
                
                # Test auth API with a simple call
                try:
                    test_user = auth.list_users(max_results=1)
                    print(f"Successfully verified Firebase Admin SDK by querying users")
                except Exception as auth_test_error:
                    print(f"WARNING: Firebase initialized but auth test failed: {auth_test_error}")
            except Exception as e:
                print(f"Error decoding Firebase credentials from environment: {e}")
                raise        
        else:
            # Fallback to credential file
            cred_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or 'lightyearai-app-firebase-adminsdk-fbsvc-a1c778d686.json'
        
            # Check if the file exists
            if not os.path.exists(cred_file):
                print(f"Warning: Credentials file not found at: {cred_file}")
                
                # Try to find it in the current directory as a fallback
                base_filename = os.path.basename(cred_file)
                if os.path.exists(base_filename):
                    cred_file = base_filename
                    print(f"Found credentials file in current directory: {cred_file}")
                else:
                    print(f"Searching for service account JSON files in current directory...")
                    json_files = [f for f in os.listdir('.') if f.endswith('.json') and 'firebase' in f.lower()]
                    if json_files:
                        cred_file = json_files[0]
                        print(f"Using alternative credentials file: {cred_file}")
            
            print(f"Using credentials file: {cred_file}")
            cred = credentials.Certificate(cred_file)
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket,
                'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', 'https://lightyearai-app-default-rtdb.europe-west1.firebasedatabase.app')
            })
            print(f"Firebase initialized with credentials file: {cred_file}")
            
        # Get Firestore client
        db = firestore.client()
        print("Firestore client initialized successfully")
        print("="*80 + "\n")
    except Exception as e:
        print(f"ERROR initializing Firebase: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # For development purposes, create a fallback mock implementation
        # In production, this should raise an error
        if os.environ.get('FLASK_ENV') == 'development':
            print("Running in development mode. Creating mock Firebase implementation.")
            from firebase_utils import MockDatabase, MockFirestore
            db = MockDatabase()
        else:
            print("*** CRITICAL ERROR: Firebase initialization failed in production mode! ***")
            raise

# Helper: Check if user is authenticated
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"[LOGIN_REQUIRED] Checking session for route: {request.path}")
        print(f"[LOGIN_REQUIRED] Session keys present: {list(session.keys())}")
        print(f"[LOGIN_REQUIRED] Session cookie present: {'session' in request.cookies}")
        
        try:
            # First, check if user_id is in session
            if 'user_id' not in session or not session.get('user_id'):
                print(f"[LOGIN_REQUIRED] No user_id in session, redirecting to login")
                
                # Store the requested URL for redirecting after login
                next_url = request.url
                # Redirect to login page with the next parameter
                return redirect(url_for('login', next=next_url))
            
            # Then perform full session validation
            if not validate_session():
                # Store the requested URL for redirecting after login
                next_url = request.url
                print(f"[LOGIN_REQUIRED] Session validation failed, redirecting to login with next={next_url}")
                # Clear any invalid session data
                session.clear()
                # Redirect to login page with the next parameter
                return redirect(url_for('login', next=next_url))
                
            print(f"[LOGIN_REQUIRED] Session is valid for user {session.get('user_id')}")
            return f(*args, **kwargs)
        except Exception as e:
            print(f"[LOGIN_REQUIRED] Unexpected error during authentication: {e}")
            import traceback
            print(f"[LOGIN_REQUIRED] Error traceback: {traceback.format_exc()}")
            
            session.clear()
            flash('An authentication error occurred. Please log in again.', 'danger')
            return redirect(url_for('login', next=request.url))
    return decorated_function

# Helper: Check if user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ('user_id' not in session):
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        user_doc = db.collection('users').document(user_id).get()
        
        if (not user_doc.exists or not user_doc.to_dict().get('is_admin', False)):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    return decorated_function

# Helper: Validate session state and handle refresh if needed
def validate_session():
    """
    Validates the current session and handles any issues.
    Returns True if the session is valid, False otherwise.
    """
    # Log detailed session state for debugging
    print(f"[SESSION VALIDATE] Session keys: {list(session.keys())}")
    print(f"[SESSION VALIDATE] User ID: {session.get('user_id', 'None')}")
    print(f"[SESSION VALIDATE] Explicitly logged out: {session.get('explicitly_logged_out', False)}")
    
    # Check if user has explicitly logged out
    if session.get('explicitly_logged_out'):
        print(f"[SESSION VALIDATE] User explicitly logged out")
        return False
    
    # First check if user_id exists and is not empty
    if 'user_id' not in session or not session.get('user_id'):
        print(f"[SESSION VALIDATE] No valid user_id in session")
        return False
        
    # Check for session age (optional security feature)
    current_time = time.time()
    login_time = session.get('login_time', 0)
    
    # Force re-login after 30 days (2592000 seconds) of inactivity
    if current_time - login_time > 2592000:
        print(f"[SESSION VALIDATE] Session too old, clearing")
        session.clear()
        return False
    
    # Check if the user still exists in Firebase (optional verification)
    try:
        uid = session.get('user_id')
        if uid:
            # Only verify with Firebase occasionally to reduce load
            # Increased verification frequency to 25% during debug
            should_verify = random.random() < 0.25  # 25% chance to verify while debugging
            
            if should_verify:
                try:
                    from firebase_admin import auth
                    auth.get_user(uid)  # Will raise exception if user doesn't exist
                    
                    # Update the login time after verification
                    session['login_time'] = current_time
                    session.modified = True
                    print(f"[SESSION VALIDATE] Firebase verification successful for {uid}")
                except Exception as firebase_error:
                    print(f"[SESSION VALIDATE] Firebase verification failed for {uid}: {firebase_error}")
                    session.clear()
                    return False
    except Exception as e:
        print(f"[SESSION VALIDATE] Session validation error: {e}")
        session.clear()
        return False
        
    # Update the login time if we're near the threshold
    if current_time - login_time > 3600:  # Update every hour
        print(f"[SESSION VALIDATE] Updating login time, old: {login_time}, new: {current_time}")
        session['login_time'] = current_time
        session.modified = True
        # Double check that the update was applied
        print(f"[SESSION VALIDATE] Verified updated login time: {session.get('login_time')}")
        
    print(f"[SESSION VALIDATE] Session is valid")
    return True

# Translations for multilingual support
translations = {
    'en': {  # English
        'name': 'English',
        'nav_study': 'Study Buddy',
        'nav_proofread': 'Proofreading',
        'nav_entertainment': 'Entertainment',
        'nav_feedback': 'Feedback',
        'nav_account': 'Account',
        'login': 'Login',
        'sign_up': 'Sign Up',
        'logout': 'Logout',
        'welcome_title': 'Welcome to LightYearAI',
        'welcome_subtitle': 'Your Intelligent Virtual Assistant',
        'welcome_desc': 'Choose from our suite of AI-powered tools to help with your tasks',
        'footer_text': 'Powered by Gemini 2.0 Flash',
        'study_desc': 'Get help with homework, learning new subjects, and understanding complex topics',
        'proofread_desc': 'Upload your document for comprehensive proofreading and receive a corrected PDF version.',
        'entertainment_desc': 'Chat about entertainment topics and get creative content',
        'proofread_upload_mode': 'Upload File',
        'proofread_write_mode': 'Write Text',
        'proofread_drop_files': 'Drop your file here or click to browse',
        'proofread_supported_formats': 'Supported formats: TXT, DOCX, PDF (up to 10MB)',
        'proofread_text_placeholder': 'Paste or write your text here...',
        'proofread_proofread_text': 'Proofread Text',
        'loading': 'Loading...',
        'proofread_processing': 'Proofreading your document...',
        'proofread_analyzing': 'Analyzing text and identifying errors',
        'proofread_complete': 'Proofreading complete! Download your corrected document below.',
        'proofread_download': 'Download Corrected PDF',
        'proofread_another': 'Proofread Another Document',
        'proofread_summary': 'Summary of Corrections',
        'start_studying': 'Start Studying',
        'proofread_document': 'Proofread Document',
        'start_chatting': 'Start Chatting',
        'about_title': 'About LightYearAI',
        'about_description': 'LightYearAI is your multipurpose AI-powered helper for a variety of tasks:',
        'about_study_title': 'Study Buddy',
        'about_study_desc': 'Get help with homework, explanations, and learning guidance',
        'about_proofreading_title': 'Proofreading',
        'about_proofreading_desc': 'Check your documents for grammar, spelling, and style improvements',
        'about_entertainment_title': 'Entertainment',
        'about_entertainment_desc': 'Chat about entertainment topics and get creative content',
        'entertainment_subtitle': 'Chat about movies, music, games, and more!',
        'entertainment_tips_title': 'Entertainment Tips',
        'entertainment_tip_fun': 'Keep it fun!',
        'entertainment_tip_fun_desc': 'Ask about movies, music, games, and more!',
        'entertainment_tip_specific': 'Be specific',
        'entertainment_tip_specific_desc': 'Mention genres, artists, or titles for better results',
        'entertainment_tip_explore': 'Explore categories',
        'entertainment_tip_explore_desc': 'Switch topics using the colored chips above',
        'entertainment_tip_emoji': 'Use emojis',
        'entertainment_tip_emoji_desc': 'Express yourself and get creative!',
        'entertainment_welcome': 'Hi there! I\'m Liya, your entertainment buddy. What would you like to chat about today?',
        'study_greeting': 'Hello! I\'m Liya, your study buddy powered by LightYearAI. How can I help you with your studies today?',
        'study_can_ask_about': 'You can ask me about:',
        'study_homework_help': 'Homework help and solving practice problems',
        'study_concept_explanations': 'Explaining difficult concepts in simple terms',
        'study_tips': 'Study techniques and exam preparation tips',
        'study_research': 'Research assistance and finding reliable sources',
        'study_more': 'And much more!',
        'study_placeholder': 'Ask about a subject, concept, or homework question...',
        'study_tip_specific': 'Be specific in your questions',
        'study_tip_specific_desc': 'to get more accurate and helpful answers',
        'study_tip_subject': 'Mention the subject or grade level',
        'study_tip_subject_desc': 'for context-appropriate responses',
        'study_tip_complex': 'Break complex topics into smaller parts',
        'study_tip_complex_desc': 'to understand each component better',
        'study_tip_examples': 'Ask for examples or practice problems',
        'study_tip_examples_desc': 'to reinforce your understanding',
        'study_upload_pdf': 'Upload PDF',
        'study_upload_desc': 'Upload a PDF to ask questions about its content',
        'study_file_supported': 'Supported files: PDF, DOCX (up to 10MB)',
        'study_analyzing_pdf': 'Analyzing your PDF...',
        'study_pdf_ready': 'PDF ready! You can now ask questions about this document.',
        'entertainment_welcome': 'Hi there! I\'m Liya, your entertainment buddy. What would you like to chat about today?',
        'suggestion_popular_movies': 'What are some popular movies right now?',
        'suggestion_tv_show': 'Recommend a TV show like Stranger Things',
        'suggestion_video_games': 'Tell me about new video games',
        'suggestion_music': 'Who are the trending music artists?',
        'type_message': 'Type your message here...',
        'category_all': 'All Topics',
        'category_movies': 'Movies',
        'category_tvshows': 'TV Shows',
        'category_videogames': 'Video Games',
        'category_music': 'Music',
        'category_books': 'Books',
        'category_all_topics': 'all entertainment topics',
        'now_chatting_about': 'Now chatting about',
        'entertainment_tooltip': 'Chat about movies, music, TV shows, video games, books and more!',
        'feedback_title': 'Feedback',
        'feedback_desc': 'Share your suggestions or improvements with us!',
        'feedback_placeholder': 'What would you like to see improved or new features added?',
        'feedback_submit': 'Submit Feedback',
        'feedback_thanks': 'Thank you for your feedback!',
        'feedback_error_empty': 'Please enter feedback before submitting.',
        # Account page translations
        'account_title': 'Your Account',
        'subscription_status': 'Subscription Status',
        'status_label': 'Status',
        'next_billing_date': 'Next billing date',
        'plan': 'Plan',
        'free': 'Free',
        'premium': 'Premium',
        'upgrade_to_premium': 'Upgrade to Premium',
        'manage_subscription': 'Manage Subscription',
        'daily_token_usage': 'Daily Token Usage',
        'used_today': 'Used today',
        'tokens': 'tokens',
        'upgrade_info': 'Upgrade to Premium for a higher daily token limit (100000 tokens) and enhanced features.',
        'plan_comparison': 'Plan Comparison',
        'feature': 'Feature',
        'free_plan': 'Free Plan',
        'premium_plan': 'Premium Plan',
        'daily_token_limit': 'Daily Token Limit',
        'priority_high_usage': 'Priority During High Usage',
        'advanced_features': 'Advanced Features',
        'price': 'Price',
        'price_per_month': '$9/month',
        'get_started': 'Get Started',
        'explore_features': 'Explore Features',
        'vision_title': 'Our Vision',
        'vision_text': 'At LightYearAI, we’re building the next generation of agentic AI—intelligent, autonomous assistants that don’t just respond, but take action. Our vision is to empower individuals, creators, and small teams with AI that can think, adapt, and execute tasks across digital workflows. We’re making cutting-edge AI accessible, practical, and safe—designed to evolve with users and act with purpose. By bridging autonomy with usability, our goal is to free people from repetitive work so they can focus on what really matters: building, dreaming, and living fully.',
    },
    'pl': {  # Polish
        'name': 'Polski',
        'nav_study': 'Nauka',
        'nav_proofread': 'Korekta',
        'nav_entertainment': 'Rozrywka',
        'nav_feedback': 'Opinie',
        'nav_account': 'Konto',
        'login': 'Zaloguj się',
        'sign_up': 'Zarejestruj się',
        'logout': 'Wyloguj się',
        'welcome_title': 'Witamy w LightYearAI',
        'welcome_subtitle': 'Twój Inteligentny Wirtualny Asystent',
        'welcome_desc': 'Wybierz spośród naszych narzędzi opartych na sztucznej inteligencji, aby pomóc w wykonywaniu zadań',
        'footer_text': 'Zasilany przez Gemini 2.0 Flash',
        'study_desc': 'Uzyskaj pomoc w odrabianiu lekcji, nauce nowych przedmiotów i zrozumieniu złożonych tematów',
        'proofread_desc': 'Prześlij dokumenty do sprawdzenia gramatyki i profesjonalnej edycji',
        'proofread_upload_mode': 'Prześlij plik',
        'proofread_write_mode': 'Wpisz tekst',
        'proofread_drop_files': 'Upuść plik tutaj lub kliknij, aby przeglądać',
        'proofread_supported_formats': 'Obsługiwane formaty: TXT, DOCX, PDF (do 10MB)',
        'proofread_text_placeholder': 'Wklej lub wpisz tutaj swój tekst...',
        'proofread_proofread_text': 'Sprawdź tekst',
        'loading': 'Ładowanie...',
        'proofread_processing': 'Sprawdzanie dokumentu...',
        'proofread_analyzing': 'Analizowanie tekstu i identyfikowanie błędów',
        'proofread_complete': 'Korekta zakończona! Pobierz poprawiony dokument poniżej.',
        'proofread_download': 'Pobierz poprawiony PDF',
        'proofread_another': 'Sprawdź inny dokument',
        'proofread_summary': 'Podsumowanie poprawek',
        'entertainment_desc': 'Rozmawiaj o filmach, muzyce, książkach i uzyskaj kreatywne treści',
        'start_studying': 'Rozpocznij Naukę',
        'proofread_document': 'Sprawdź Dokument',
        'start_chatting': 'Rozpocznij Czat',
        'about_title': 'O LightYearAI',
        'about_description': 'LightYearAI to Twój wielofunkcyjny pomocnik oparty na sztucznej inteligencji do różnych zadań:',
        'about_study_title': 'Nauka',
        'about_study_desc': 'Uzyskaj pomoc z pracami domowymi, wyjaśnieniami i wskazówkami dotyczącymi nauki',
        'about_proofreading_title': 'Korekta',
        'about_proofreading_desc': 'Sprawdź swoje dokumenty pod kątem gramatyki, pisowni i ulepszeń stylistycznych',
        'about_entertainment_title': 'Rozrywka',
        'about_entertainment_desc': 'Rozmawiaj na tematy rozrywkowe i uzyskaj kreatywne treści',
        'choose_feature': 'Wybierz dowolną funkcję powyżej, aby rozpocząć!',
        'study_greeting': 'Cześć! Jestem Liya, Twój asystent do nauki od LightYearAI. Jak mogę Ci dzisiaj pomóc w nauce?',
        'study_can_ask_about': 'Możesz mnie zapytać o:',
        'study_homework_help': 'Pomoc w pracach domowych i rozwiązywanie zadań',
        'study_concept_explanations': 'Wyjaśnianie trudnych pojęć w prosty sposób',
        'study_tips': 'Techniki nauki i wskazówki do przygotowania do egzaminów',
        'study_research': 'Pomoc w badaniach i znajdowaniu wiarygodnych źródeł',
        'study_more': 'I wiele więcej!',
        'study_placeholder': 'Zapytaj o przedmiot, pojęcie lub zadanie domowe...',
        'study_tip_specific': 'Zadawaj konkretne pytania',
        'study_tip_specific_desc': 'aby uzyskać dokładniejsze i pomocne odpowiedzi',
        'study_tip_subject': 'Wspomnij przedmiot lub poziom nauczania',
        'study_tip_subject_desc': 'dla odpowiedzi dostosowanych do kontekstu',
        'study_tip_complex': 'Podziel złożone tematy na mniejsze części',
        'study_tip_complex_desc': 'aby lepiej zrozumieć każdy element',
        'study_tip_examples': 'Poproś o przykłady lub zadania praktyczne',
        'study_tip_examples_desc': 'aby wzmocnić swoje zrozumienie',
        'study_upload_pdf': 'Prześlij PDF',
        'study_upload_desc': 'Prześlij plik PDF, aby zadać pytania o jego zawartość',
        'study_file_supported': 'Wspierane formaty: PDF, DOCX (do 10MB)',
        'study_analyzing_pdf': 'Analizuję Twój PDF...',
        'study_pdf_ready': 'PDF gotowy! Możesz teraz zadawać pytania dotyczące tego dokumentu.',
        'entertainment_welcome': 'Cześć! Jestem Liya, Twój asystent rozrywki. O czym chciałbyś dziś porozmawiać?',
        'suggestion_popular_movies': 'Jakie są teraz popularne filmy?',
        'suggestion_tv_show': 'Poleć mi serial podobny do Stranger Things',
        'suggestion_video_games': 'Opowiedz mi o nowych grach wideo',
        'suggestion_music': 'Którzy artyści muzyczni są teraz na topie?',
        'type_message': 'Wpisz swoją wiadomość tutaj...',
        'category_all': 'Wszystkie Tematy',
        'category_movies': 'Filmy',
        'category_tvshows': 'Seriale',
        'category_videogames': 'Gry Wideo',
        'category_music': 'Muzyka',
        'category_books': 'Książki',
        'category_all_topics': 'wszystkie tematy rozrywkowe',
        'now_chatting_about': 'Teraz rozmawiamy o',
        'entertainment_tooltip': 'Rozmawiaj o filmach, muzyce, serialach, grach wideo, książkach i nie tylko!',
        'feedback_title': 'Opinie',
        'feedback_desc': 'Podziel się swoimi sugestiami lub udoskonaleniami!',
        'feedback_placeholder': 'Co chciałbyś ulepszyć lub jakie nowe funkcje dodać?',
        'feedback_submit': 'Prześlij opinię',
        'feedback_thanks': 'Dziękujemy za Twoją opinię!',
        'feedback_error_empty': 'Proszę wpisać opinię przed wysłaniem.',
        # Account page translations
        'account_title': 'Twoje konto',
        'subscription_status': 'Status subskrypcji',
        'plan': 'Plan',
        'free': 'Darmowy',
        'premium': 'Premium',
        'upgrade_to_premium': 'Przejdź na Premium',
        'manage_subscription': 'Zarządzaj subskrypcją',
        'daily_token_usage': 'Dzienne użycie tokenów',
        'used_today': 'Użyto dzisiaj',
        'tokens': 'tokeny',
        'upgrade_info': 'Przejdź na Premium, aby uzyskać wyższy dzienny limit tokenów (100000 tokenów) oraz dodatkowe funkcje.',
        'plan_comparison': 'Porównanie planów',
        'feature': 'Funkcja',
        'free_plan': 'Plan darmowy',
        'premium_plan': 'Plan Premium',
        'daily_token_limit': 'Dzienne limity tokenów',
        'priority_high_usage': 'Priorytet przy dużym obciążeniu',
        'advanced_features': 'Zaawansowane funkcje',
        'price': 'Cena',
        'price_per_month': '9 USD/miesiąc',
        'get_started': 'Zaczynamy',
        'explore_features': 'Poznaj funkcje',
        'vision_title': 'Nasza Wizja',
        'vision_text': 'Budujemy następną generację agentowego AI — inteligentnych, autonomicznych asystentów, którzy nie tylko odpowiadają, ale też podejmują działania. Naszą wizją jest wspieranie osób, twórców i małych zespołów AI, które potrafi myśleć, adaptować się i wykonywać zadania w ramach cyfrowych przepływów pracy. Umożliwiamy dostęp do najnowszych technologii AI, czyniąc je praktycznymi i bezpiecznymi — zaprojektowanymi tak, aby rozwijały się razem z użytkownikami i działały z zamiarem. Łącząc autonomię z użytecznością, naszym celem jest uwolnienie ludzi od monotonnego, rutynowego zajęcia, aby mogli skupić się na tym, co naprawdę ma znaczenie: tworzeniu, marzeniu i pełnym życiu.',
    },
    'az': {  # Azerbaijani
        'name': 'Azərbaycanca',
        'nav_study': 'Təhsil Köməkçisi',
        'nav_proofread': 'Redaktə',
        'nav_entertainment': 'Əyləncə',
        'nav_feedback': 'Rəy',
        'nav_account': 'Hesab',
        'login': 'Daxil ol',
        'sign_up': 'Qeydiyyatdan keç',
        'logout': 'Çıxış',
        'welcome_title': 'LightYearAI-a Xoş Gəlmisiniz',
        'welcome_subtitle': 'Sizin İntellektual Virtual Köməkçiniz',
        'welcome_desc': 'Tapşırıqlarınıza kömək etmək üçün süni intellekt əsaslı alətlərimizdən seçin',
        'footer_text': 'Gemini 2.0 Flash tərəfindən təchiz edilmişdir',
        'study_desc': 'Ev tapşırıqları, yeni mövzuların öyrənilməsi və mürəkkəb mövzuların başa düşülməsi ilə bağlı kömək alın',
        'proofread_desc': 'Qrammatik yoxlama və peşəkar redaktə üçün sənədlər yükləyin',
        'proofread_upload_mode': 'Faylı Yükləyin',
        'proofread_write_mode': 'Mətn Yazın',
        'proofread_drop_files': 'Faylı buraya sürüşdürün və ya klikləyin',
        'proofread_supported_formats': 'Dəstəklənən formatlar: TXT, DOCX, PDF (10MB-dək)',
        'entertainment_desc': 'Filmlər, musiqi, kitablar haqqında söhbət edin və yaradıcı məzmun əldə edin',
        'start_studying': 'Öyrənməyə Başlayın',
        'proofread_document': 'Sənədi Redaktə Et',
        'start_chatting': 'Söhbətə Başlayın',
        'about_title': 'LightYearAI Haqqında',
        'about_description': 'LightYearAI müxtəlif tapşırıqlar üçün süni intellektlə işləyən çoxməqsədli köməkçinizdir:',
        'about_study_title': 'Təhsil Köməkçisi',
        'about_study_desc': 'Ev tapşırıqları, izahatlar və öyrənmə təlimatları ilə kömək alın',
        'about_proofreading_title': 'Redaktə',
        'about_proofreading_desc': 'Sənədlərinizi qrammatika, imla və üslub təkmilləşdirmələri üçün yoxlayın',
        'about_entertainment_title': 'Əyləncə',
        'about_entertainment_desc': 'Əyləncə mövzuları haqqında söhbət edin və yaradıcı məzmun əldə edin',
        'entertainment_subtitle': 'Filmlər, musiqi, oyunlar və daha çox barədə söhbət edin!',
        'entertainment_tips_title': 'Əyləncə Məsləhətləri',
        'entertainment_tip_fun': 'Əyləncəli saxlayın!',
        'entertainment_tip_fun_desc': 'Filmlər, musiqi, oyunlar və daha çox barədə soruşun!',
        'entertainment_tip_specific': 'Dəqiq olun',
        'entertainment_tip_specific_desc': 'Daha yaxşı nəticələr üçün janrları, sənətçiləri və ya başlıqları qeyd edin',
        'entertainment_tip_explore': 'Kateqoriyaları araşdırın',
        'entertainment_tip_explore_desc': 'Yuxarıdakı rəngli çiplərdən istifadə edərək mövzuları dəyişin',
        'entertainment_tip_emoji': 'Emoji istifadə edin',
        'entertainment_tip_emoji_desc': 'Özünüzü ifadə edin və yaradıcı olun!',
        'type_message': 'Mesajınızı buraya yazın...',
        'suggestion_popular_movies': 'Hal-hazırda hansı filmlər məşhurdur?',
        'suggestion_tv_show': 'Stranger Things-ə bənzər bir serial tövsiyə et',
        'suggestion_video_games': 'Yeni video oyunlar haqqında danış',
        'suggestion_music': 'Trend olan musiqi ifaçıları kimlərdir?',
        # Proofread page translations
        'proofread_text_placeholder': 'Mətn yapışdırın və ya buraya yazın...',
        'proofread_proofread_text': 'Mətn Redaktə et',
        # Entertainment page title and categories
        'entertainment_title': 'Əyləncə',
        'category_all': 'Bütün Mövzular',
        'category_movies': 'Filmlər',
        'category_tvshows': 'TV Seriallar',
        'category_videogames': 'Video Oyunlar',
        'category_music': 'Musiqi',
        'category_books': 'Kitablar',
        'category_all_topics': 'bütün əyləncə mövzuları',
        # Feedback page translations
        'feedback_title': 'Rəy',
        'feedback_desc': 'Təkliflərinizi və ya təkmilləşdirmələrinizi bizimlə bölüşün!',
        'feedback_placeholder': 'Təkmilləşdirmək istədiyiniz və ya əlavə olunmasını istədiyiniz yeni xüsusiyyətləri yazın',
        'feedback_submit': 'Rəy göndər',
        # Account page translations
        'account_title': 'Twoje konto',
        'subscription_status': 'Status subskrypcji',
        'plan': 'Plan',
        'free': 'Darmowy',
        'premium': 'Premium',
        'upgrade_to_premium': 'Przejdź na Premium',
        'manage_subscription': 'Zarządzaj subskrypcją',
        'daily_token_usage': 'Dzienne użycie tokenów',
        'used_today': 'Użyto dzisiaj',
        'tokens': 'tokeny',
        'upgrade_info': 'Przejdź na Premium, aby uzyskać wyższy dzienny limit tokenów (100000 tokenów) oraz dodatkowe funkcje.',
        'plan_comparison': 'Porównanie planów',
        'feature': 'Funkcja',
        'free_plan': 'Plan darmowy',
        'premium_plan': 'Plan Premium',
        'daily_token_limit': 'Dzienne limity tokenów',
        'priority_high_usage': 'Priorytet przy dużym obciążeniu',
        'advanced_features': 'Zaawansowane funkcje',
        'price': 'Cena',
        'price_per_month': '9 USD/miesiąc',
        'get_started': 'Zaczynamy',
        'explore_features': 'Poznaj funkcje',
        'vision_title': 'Nasza Wizja',
        'vision_text': 'Budujemy następną generację agentowego AI — inteligentnych, autonomicznych asystentów, którzy nie tylko odpowiadają, ale też podejmują działania. Naszą wizją jest wspieranie osób, twórców i małych zespołów AI, które potrafi myśleć, adaptować się i wykonywać zadania w ramach cyfrowych przepływów pracy. Umożliwiamy dostęp do najnowszych technologii AI, czyniąc je praktycznymi i bezpiecznymi — zaprojektowanymi tak, aby rozwijały się razem z użytkownikami i działały z zamiarem. Łącząc autonomię z użytecznością, naszym celem jest uwolnienie ludzi od monotonnego, rutynowego zajęcia, aby mogli skupić się na tym, co naprawdę ma znaczenie: tworzeniu, marzeniu i pełnym życiu.',
    }
}

language_names = {
    'en': 'English',
    'pl': 'Polski',
    'az': 'Azərbaycanca'
}

# Set up upload folder for production or development
if (os.environ.get('RENDER')):
    # For Render.com deployment - use a folder in the app directory
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
else:
    # For local development - use temp directory
    app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'uploads')

app.config['MAX_CONTENT_LENGTH'] = (10 * 1024 * 1024)  # 10MB max upload

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

# Function to get AI response
def get_ai_response(prompt, history=None, system_prompt=None, language=None):
    try:
        # Determine language for response if not explicitly provided
        if (language is None):
            language = (g.current_language if hasattr(g, 'current_language') else 'en')
        
        # Add language instruction to system_prompt
        language_instructions = {
            'en': "Please respond in English.",
            'pl': "Proszę odpowiadać w języku polskim.",
            'az': "Zəhmət olmasa Azərbaycan dilində cavab verin."
        }
        
        # Define identity information (only to be used when directly asked)
        identity_info = {
            'en': "Your name is Liya. You are an AI assistant created by LightYearAI, powered by Google's Gemini model. If asked about your creator, founder, or who made you, mention that you were developed by LightYearAI.",
            'pl': "Nazywasz się Liya. Jesteś asystentem AI stworzonym przez LightYearAI, opartym na modelu Gemini od Google. Jeśli zapytają o twojego twórcę, założyciela lub kto cię stworzył, wspomnij, że zostałaś stworzona przez LightYearAI.",
            'az': "Sizin adınız Liya-dır. Siz Google-ın Gemini modeli ilə işləyən LightYearAI tərəfindən yaradılmış AI köməkçisisiniz. Əgər yaradıcınız, təsisçiniz və ya sizi kimin yaratdığı haqqında soruşsalar, LightYearAI tərəfindən yaradıldığınızı qeyd edin."
        }
        
        language_instruction = language_instructions.get(language, "Please respond in English.")
        identity_information = identity_info.get(language, identity_info['en'])

        # Instruction to keep responses natural and never mention AI/limitations
        natural_instruction = {
            'en': "Never mention that you are an AI, language model, or chatbot. Do not use disclaimers about your abilities or limitations. Respond as a friendly, knowledgeable assistant in a natural, casual, and human-like way.",
            'pl': "Nigdy nie wspominaj, że jesteś AI, modelem językowym lub chatbotem. Nie używaj zastrzeżeń dotyczących swoich możliwości lub ograniczeń. Odpowiadaj jako przyjazny, kompetentny asystent w naturalny, swobodny i ludzki sposób.",
            'az': "Heç vaxt süni intellekt, dil modeli və ya çatbot olduğunuzu qeyd etməyin. Bacarıq və məhdudiyyətləriniz barədə heç bir açıqlama verməyin. Cavablarınızı səmimi, bilikli və insan kimi təbii şəkildə verin."
        }
        natural_instruction_text = natural_instruction.get(language, natural_instruction['en'])
        
        # Check if user is asking about identity
        is_identity_question = False
        identity_keywords = [
            'your name', 'who are you', 'who made you', 'who created you', 
            'your creator', 'what are you called', 'what\'s your name',
            'what is your name', 'kim olduğun', 'kim yaratdı', 'adın nədir',
            'kim seni yarattı', 'kim jesteś', 'kto cię stworzył', 'jak się nazywasz',
            'twój twórca', 'twoje imię', 'nazywasz się', 'founder', 'made by',
            'developed by', 'company', 'LightYearAI', 'Liya', 'your identity'
        ]
        
        # Check if prompt contains identity-related keywords
        for keyword in identity_keywords:
            if (keyword.lower() in prompt.lower()):
                is_identity_question = True
                break
        
        # Prepare the conversation
        if (history):
            # For ongoing conversations, use identity only if specifically asked
            chat = model.start_chat(history=history)
            if (is_identity_question):
                response = chat.send_message(f"{identity_information}\n\n{natural_instruction_text}\n\n{prompt}\n\n{language_instruction}")
            else:
                response = chat.send_message(f"{natural_instruction_text}\n\n{prompt}\n\n{language_instruction}")
        else:
            # For new conversations
            if (system_prompt):
                # Only include identity in system prompt if specifically asked
                if (is_identity_question):
                    system_prompt = f"{system_prompt}\n\n{identity_information}\n\n{natural_instruction_text}\n\n{language_instruction}"
                else:
                    system_prompt = f"{system_prompt}\n\n{natural_instruction_text}\n\n{language_instruction}"
                
                combined_prompt = f"{system_prompt}\n\nUser request: {prompt}"
                response = model.generate_content(combined_prompt)
            else:
                # When no system prompt, still check if identity question
                if (is_identity_question):
                    response = model.generate_content(f"{identity_information}\n\n{natural_instruction_text}\n\n{prompt}\n\n{language_instruction}")
                else:
                    response = model.generate_content(f"{natural_instruction_text}\n\n{prompt}\n\n{language_instruction}")
        
        return response.text
    except Exception as e:
        print(f"Error getting AI response: {e}")
        if (language == 'pl'):
            return f"Przepraszam, napotkałem błąd: {str(e)}"
        elif (language == 'az'):
            return f"Üzr istəyirəm, bir xəta baş verdi: {str(e)}"
        else:
            return f"Sorry, I encountered an error: {str(e)}"

# Language route
@app.route('/set_language/<lang>')
def set_language(lang):
    # Set the language in session
    if (lang in translations):
        session['language'] = lang
    # Get the 'next' parameter for redirect, defaulting to the home page
    next_page = request.args.get('next', '/')
    return redirect(next_page)

# Before request handler to set language
@app.before_request
def before_request():
    # IMMEDIATE AZERI_TEXT.TXT CLEARING - catch this problematic file early
    if 'current_file' in session:
        current_file = session.get('current_file', {})
        filename = current_file.get('filename', '')
        if filename == 'azeri_text.txt':
            print(f"[IMMEDIATE CLEAR] Detected problematic azeri_text.txt - removing immediately")
            session.pop('current_file', None)
            session.modified = True
            print(f"[IMMEDIATE CLEAR] azeri_text.txt removed from session")
    
    # Session persistence debugging
    has_current_file = 'current_file' in session
    current_file_size = len(session.get('current_file', {}).get('content', '')) if has_current_file else 0
    has_file_id = bool(session.get('current_file', {}).get('file_id')) if has_current_file else False
    endpoint = request.endpoint
    
    if '/static/' not in request.path and request.path != '/favicon.ico':
        print(f"[SESSION TRACKING] Request to {request.path} ({endpoint})")
        print(f"[SESSION TRACKING] Has current_file: {has_current_file}, Content size: {current_file_size}, Has file_id: {has_file_id}")
        if has_current_file:
            current_filename = session.get('current_file', {}).get('filename', 'unknown')
            print(f"[SESSION TRACKING] Current filename: {current_filename}")
      # ENHANCED STALE SESSION DATA CLEANUP: More aggressive clearing for problematic files
    if has_current_file and '/static/' not in request.path and request.path != '/favicon.ico':
        current_file = session.get('current_file', {})
        upload_timestamp = current_file.get('upload_timestamp') or current_file.get('upload_time')
        filename = current_file.get('filename', 'unknown')
        
        # Check if file data should be cleared (more aggressive criteria)
        should_clear = False
        clear_reason = ""
        
        # IMMEDIATE CLEAR: Any file from 2025-05-21 or azeri_text.txt
        if filename == 'azeri_text.txt':
            should_clear = True
            clear_reason = "problematic file azeri_text.txt detected - force clearing"
        elif filename == 'dataset_part1.csv' and upload_timestamp:
            # Also clear any old dataset uploads from that problematic day
            if '2025-05-21' in str(upload_timestamp):
                should_clear = True
                clear_reason = "file from problematic date 2025-05-21 detected"
        elif upload_timestamp:
            try:
                from datetime import datetime
                # Handle multiple timestamp formats
                if isinstance(upload_timestamp, str):
                    if 'T' in upload_timestamp:
                        upload_time = datetime.fromisoformat(upload_timestamp.replace('Z', '+00:00'))
                    else:
                        upload_time = datetime.strptime(upload_timestamp, '%Y-%m-%d %H:%M:%S')
                else:
                    upload_time = upload_timestamp
                
                time_diff = datetime.now() - upload_time.replace(tzinfo=None)
                # Reduce threshold to 30 minutes for more aggressive clearing
                if time_diff.total_seconds() > 1800:  # 30 minutes
                    should_clear = True
                    clear_reason = f"file data older than 30 minutes ({time_diff.total_seconds():.0f} seconds)"
            except Exception as date_error:
                print(f"[STALE SESSION CLEANUP] Date parsing error: {date_error}")
                should_clear = True
                clear_reason = "invalid timestamp format - clearing as precaution"
          # FORCE CLEAR: Any file with no timestamp (probably old)
        if not upload_timestamp and filename != 'unknown':
            should_clear = True
            clear_reason = "no timestamp - likely old session data"
        
        if should_clear:
            print(f"[STALE SESSION CLEANUP] FORCE CLEARING: {filename} ({clear_reason})")
            try:
                # Import clearing functions
                from file_optimizer import aggressive_session_clear, clear_flask_session_data
                
                # Log session state before clearing
                session_keys_before = list(session.keys())
                print(f"[STALE SESSION CLEANUP] Session keys before clearing: {session_keys_before}")
                
                # Use aggressive clearing for persistent data
                aggressive_result = aggressive_session_clear(session)
                print(f"[STALE SESSION CLEANUP] Aggressive clear result: {aggressive_result}")
                
                # Follow up with standard clearing
                clear_result = clear_flask_session_data(session)
                print(f"[STALE SESSION CLEANUP] Standard clear result: {clear_result}")
                
                # Additional direct clearing - force removal
                if 'current_file' in session:
                    print(f"[STALE SESSION CLEANUP] WARNING: File data STILL present after both clearing methods!")
                    # Force delete the key directly
                    session.pop('current_file', None)
                    session.modified = True
                    print(f"[STALE SESSION CLEANUP] Direct pop() executed")
                
                # Nuclear option if STILL present
                if 'current_file' in session:
                    print(f"[STALE SESSION CLEANUP] CRITICAL: File data persisting despite all clearing attempts!")
                    # Complete session rebuild
                    user_id = session.get('user_id')
                    user_name = session.get('user_name')
                    user_picture = session.get('user_picture')
                    language = session.get('language', 'en')
                    
                    # Clear everything
                    session.clear()
                    
                    # Rebuild with only essential data
                    session['user_id'] = user_id
                    session['user_name'] = user_name
                    session['user_picture'] = user_picture
                    session['language'] = language
                    session.modified = True
                    session.permanent = True
                    print(f"[STALE SESSION CLEANUP] NUCLEAR CLEAR: Complete session rebuild executed")
                else:
                    print(f"[STALE SESSION CLEANUP] SUCCESS: Old file data successfully removed")
                
                # Final verification
                final_keys = list(session.keys())
                print(f"[STALE SESSION CLEANUP] Final session keys: {final_keys}")
                    
            except Exception as e:
                print(f"[STALE SESSION CLEANUP] Error during enhanced clearing: {e}")
                # Ultimate emergency fallback: force clear everything file-related
                keys_to_remove = []
                for key in session.keys():
                    if 'file' in key.lower() or 'upload' in key.lower():
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    session.pop(key, None)
                    print(f"[STALE SESSION CLEANUP] Emergency removal of key: {key}")
                
                session.modified = True
                print(f"[STALE SESSION CLEANUP] Emergency fallback clearing completed")
    
    # Set default language if not set
    if ('language' not in session):
        session['language'] = 'en'
      # Make current language and translations available to all templates
    g.current_language = session.get('language', 'en')
    g.current_language_name = translations[g.current_language]['name']
    g.translations = translations[g.current_language]
    g.available_languages = language_names  # Provide available languages to templates    # User info for navbar
    g.user_name = session.get('user_name')
    g.user_picture = session.get('user_picture')
    g.user_id = session.get('user_id')  # Make user_id available to templates
    
    # Add Firebase configuration to all templates
    g.firebase_api_key = os.environ.get('FIREBASE_API_KEY', '')
    g.firebase_auth_domain = os.environ.get('FIREBASE_AUTH_DOMAIN', '')
    g.firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
    g.firebase_storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET', '')
    g.firebase_messaging_sender_id = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '')
    g.firebase_app_id = os.environ.get('FIREBASE_APP_ID', '')
    
    # Add token usage data for authenticated users
    user_id = session.get('user_id')
    # Import inside function to avoid circular imports
    from firebase_admin import firestore
    
    # Initialize token usage variables with default values
    g.plan = 'free'
    g.current_usage = 0
    g.daily_limit = FREE_PLAN_DAILY_LIMIT
    g.usage_percentage = 0
    g.remaining_tokens = FREE_PLAN_DAILY_LIMIT
    
    try:
        # Make sure user_id is a valid value, not None or empty string
        if user_id and str(user_id).strip():
            db = firestore.client()
            
            # Get user's subscription status
            subscription = get_user_subscription(user_id)
            plan = subscription.get('plan', 'free')
            
            # Get user's token usage for today
            current_usage = get_user_daily_token_usage(user_id)
            
            # Handle case where current_usage might be a dictionary or integer
            if isinstance(current_usage, dict):
                tokens_used = current_usage.get('tokens_used', 0)
            else:
                tokens_used = current_usage
            
            # Get plan limits
            daily_limit = FREE_PLAN_DAILY_LIMIT if (plan == 'free') else PAID_PLAN_DAILY_LIMIT
            
            # Calculate percentage used
            usage_percentage = min(round((tokens_used / daily_limit) * 100), 100) if (daily_limit > 0) else 0
            
            # Set token data for all templates
            g.plan = plan
            g.current_usage = tokens_used
            g.daily_limit = daily_limit
            g.usage_percentage = usage_percentage
            g.remaining_tokens = daily_limit - tokens_used
    except Exception as e:
        print(f"[TOKEN ERROR] Failed to retrieve token usage data: {e}")
        # Error handling is not needed here since we already set default values
    
    # Additional session debugging only for non-static requests
    if '/static/' not in request.path and request.path != '/favicon.ico':
        print(f"[SESSION DEBUG] Cookie session ID: {request.cookies.get('session', 'no-session-cookie')[:10]}...")
        print(f"[SESSION DEBUG] Session modified flag: {session.modified}")
        if has_current_file:
            print(f"[SESSION DEBUG] File metadata: {session['current_file'].get('filename')}, uploaded: {session['current_file'].get('upload_time')}")
    # Add Firestore client to template context
    g.db = firestore.client() if firebase_admin._apps else None
    print('SESSION:', dict(session))
    print('g.user_name:', g.user_name, 'g.user_picture:', g.user_picture)

    # Add Firebase configuration to all templates
    g.firebase_api_key = os.environ.get('FIREBASE_API_KEY', '')
    g.firebase_auth_domain = os.environ.get('FIREBASE_AUTH_DOMAIN', '')
    g.firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
    g.firebase_storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET', '')
    g.firebase_messaging_sender_id = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '')
    g.firebase_app_id = os.environ.get('FIREBASE_APP_ID', '')

@app.route('/')
def index():
    # Debug session content
    print(f"[INDEX ROUTE] Session keys: {list(session.keys())}")
    print(f"[INDEX ROUTE] User ID in session: {session.get('user_id')}")
    print(f"[INDEX ROUTE] Session modified flag: {session.modified}")
    print(f"[INDEX ROUTE] Session cookie: {request.cookies.get('session', 'no-session-cookie')[:10]}...")
    print(f"[INDEX ROUTE] Has session cookie: {'session' in request.cookies}")
    try:
        # Check for user_id first
        if 'user_id' not in session or not session.get('user_id'):
            print(f"[INDEX ROUTE] No user_id in session, showing landing page")
            # Add flag to indicate this is the homepage so we can disable loading screen
            return render_template('index.html', is_homepage=True)
            
        # If user_id exists, validate the full session
        if validate_session():
            print(f"[INDEX ROUTE] User is logged in with valid session ID {session.get('user_id')}, redirecting to unified_chat")
            return redirect(url_for('unified_chat'))
        else:
            # If validation fails, clear the session
            print(f"[INDEX ROUTE] Invalid session detected, clearing session")
            session.clear()
            # Add a flash message to inform the user
            flash('Your session has expired. Please log in again.', 'warning')
            # Add flag to indicate this is the homepage so we can disable loading screen
            return render_template('index.html', is_homepage=True)
    except Exception as e:
        print(f"[INDEX ROUTE] Unexpected error during session validation: {e}")
        import traceback
        print(f"[INDEX ROUTE] Error traceback: {traceback.format_exc()}")
        session.clear()
        flash('An error occurred during session validation. Please log in again.', 'danger')
      # Show landing page for non-logged in users
    print("[INDEX ROUTE] User is not logged in, showing landing page")
    # Add flag to indicate this is the homepage so we can disable loading screen
    return render_template('index.html', is_homepage=True)

@app.route('/unified_chat')
@login_required
def unified_chat():
    # Double check that the user is properly authenticated
    print(f"[UNIFIED_CHAT] User ID in session: {session.get('user_id')}")
    print(f"[UNIFIED_CHAT] Session modified flag: {session.modified}")
    print(f"[UNIFIED_CHAT] Session login time: {session.get('login_time')}")
    print(f"[UNIFIED_CHAT] Session cookie present: {'session' in request.cookies}")
    
    # Redundant check since @login_required should already validate
    # but keeping it for extra safety
    if not session.get('user_id') or not validate_session():
        # Clear any invalid session data
        print("[UNIFIED_CHAT] Invalid session detected, clearing session and redirecting to login")
        session.clear()
        flash('Your session has expired. Please login again.', 'warning')
        return redirect(url_for('login'))
    
    # Unified single-page chat interface with all features
    print(f"[UNIFIED_CHAT] Loading chat interface for user {session.get('user_id')}")
    
    try:
        # Ensure Firebase connection is still valid
        from firebase_admin import auth
        user = auth.get_user(session.get('user_id'))
        print(f"[UNIFIED_CHAT] Firebase verified user: {user.uid}")
    except Exception as e:
        print(f"[UNIFIED_CHAT] Firebase verification failed: {e}")
        session.clear()
        flash('Authentication error. Please login again.', 'warning')
        return redirect(url_for('login'))
    
    # Additional diagnostic logging
    print(f"[UNIFIED_CHAT] Session data before rendering: {dict(session)}")
    
    try:
        return render_template('base.html', active_page='unified_chat')
    except Exception as e:
        print(f"[UNIFIED_CHAT] Template rendering error: {e}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"[UNIFIED_CHAT] Error traceback: {error_trace}")
        
        # Provide a more graceful fallback
        return """
        <html>
        <head>
            <title>LightYearAI - Error</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                .error-container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                h1 { color: #c00; }
                .btn { display: inline-block; padding: 10px 20px; background: #0066cc; color: white; text-decoration: none; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>An error occurred</h1>
                <p>We're sorry, but something went wrong while loading the application. This might be due to a temporary issue.</p>
                <p>Please try:</p>
                <ul>
                    <li>Refreshing the page</li>
                    <li><a href="/logout">Logging out</a> and logging back in</li>
                    <li>Clearing your browser cookies and cache</li>
                </ul>
                <p><a href="/login" class="btn">Return to Login Page</a></p>
            </div>
        </body>
        </html>
        """, 500

# The routes below are kept for API endpoints but the UI redirects to unified_chat
@app.route('/chat')
@login_required
def chat():
    return redirect(url_for('unified_chat'))

@app.route('/study')
@login_required
def study():
    return redirect(url_for('unified_chat'))

@app.route('/proofread')
@login_required
def proofread():
    return redirect(url_for('unified_chat'))

@app.route('/entertainment')
@login_required
def entertainment():
    return redirect(url_for('unified_chat'))

@app.route('/command_test')
def command_fallback_test():
    # Test page for command fallback UI
    return render_template('command_fallback_test.html')

@app.route('/nl_command_test')
def nl_command_test():
    # Test page for natural language command detection
    return render_template('nl_command_test.html')

# Study Buddy Routes
# --- User Memory Store (Firestore persistent) ---
def update_user_memory(user_id, key, value):
    if (not user_id):
        return
    
    # Get the Firestore client from g or import it directly
    from firebase_admin import firestore
    db = firestore.client()
    
    try:
        # Update the memory in Firestore
        db.collection('user_memories').document(user_id).set({
            key: value
        }, merge=True)
        return True
    except Exception as e:
        print(f"Error updating user memory: {e}")
        return False

def get_user_memory(user_id, key, default=None):
    if (not user_id):
        return default
    
    # Get the Firestore client
    from firebase_admin import firestore
    db = firestore.client()
    
    doc = db.collection('user_memories').document(user_id).get()
    if (doc.exists):
        return doc.to_dict().get(key, default)
    return default

@app.route('/study/chat', methods=['POST'])
@login_required
async def study_chat():
    """
    Process study chat requests with MCP integration and improved file handling.
    This is an async route that properly uses Flask's async support.
    """
    # Double check that the user is properly authenticated
    if not session.get('user_id'):
        # Clear any invalid session data
        session.clear()
        return jsonify({
            'response': "<p>You need to be logged in to use the chat. Please login first.</p>",
            'error': 'authentication_required'
        }), 401
    # Use the helper function to verify session state at the beginning of the request
    verify_session_state("study_chat_start")
    
    data = request.json
    print(f"DEBUG: study_chat called with data keys: {list(data.keys())}")
    user_message = data.get('message', '')
    pdf_content = data.get('pdfContent', None)
    file_id = data.get('fileId', None)
    formatted_response = "<p>Response processing error</p>"  # Default value in case of errors
    
    # Log session information to help debug
    print(f"DEBUG: Session info - user_id: {session.get('user_id')}")
    if 'current_file' in session:
        print(f"DEBUG: Session has current_file with keys: {list(session['current_file'].keys())}")
        print(f"DEBUG: Current file in session - filename: {session['current_file'].get('filename')}, id: {session['current_file'].get('file_id')}")
        print(f"DEBUG: Content length in session: {len(session['current_file'].get('content', ''))}")
    
    # Support front-end upload flags to load file context
    # First check if hasFile or hasFileId flags are set
    has_file_flag = data.get('hasFile', False)
    has_file_id_flag = data.get('hasFileId', False)
    print(f"DEBUG: Upload flags: hasFileId={has_file_id_flag}, hasFile={has_file_flag}")
    print(f"DEBUG: File data: pdf_content={bool(pdf_content)}, file_id={file_id}")
    print(f"DEBUG: Current file in session: {'current_file' in session}")
    
    # If flags are set but we don't have content yet, get it from session
    if (has_file_flag or has_file_id_flag) and not pdf_content and 'current_file' in session:
        print("Loading file content from session due to flags")
        pdf_content = session['current_file'].get('content')
        file_id = session['current_file'].get('file_id')
        print(f"Loaded file from session: id={file_id}, content_length={len(pdf_content) if pdf_content else 0}")
    user_id = session.get('user_id')
    session_id = (data.get('sessionId') or str(int((time.time() * 1000))))
    
    try:
        # Check if user has exceeded their token limit
        can_use, remaining_tokens = check_user_token_limit(user_id)
        
        if (not can_use):
            return jsonify({
                'response': "<p>You've reached your daily token limit. Please try again tomorrow or upgrade to premium for a higher limit.</p>",
                'error': 'token_limit_exceeded'
            })

        # Import the chat history functions
        from firebase_utils import get_chat_history, save_chat_message, format_chat_history_for_api

        # Get chat history from Firestore
        chat_history = get_chat_history(user_id, 'study')        # Add file context to user message if needed
        enhanced_user_message = user_message
        if pdf_content and ('current_file' in session):
            filename = session['current_file'].get('filename', 'document.pdf')
            file_context = f"I'm asking about the document I uploaded titled: '{filename}'. Please answer using the content of this document."
            enhanced_user_message = f"{file_context}\n\n{user_message}"

        # Save the user message to Firestore
        save_chat_message(user_id, 'study', user_message, 'user')

        # --- Memory: Extract and save facts if user shares them ---
        import re

        # Trigger words for memory extraction
        trigger_patterns = [
            r"i like ([\w\s'\-]+)",
            r"my favorite ([\w\s'\-]+) is ([\w\s'\-]+)",
            r"i love ([\w\s'\-]+)",
            r"i did ([\w\s'\-]+)",
            r"i went to ([\w\s'\-]+)",
            r"i go to ([\w\s'\-]+)",
            r"i watch ([\w\s'\-]+)",
            r"i made ([\w\s'\-]+)",
            r"i build ([\w\s'\-]+)",
            r"i built ([\w\s'\-]+)",
            r"i enjoy ([\w\s'\-]+)",
            r"my ([\w\s'\-]+) is ([\w\s'\-]+)",
            r"call me ([\w\s'\-]+)"
        ]

        # Check for memory patterns in user message and save to memory
        for pattern in trigger_patterns:
            matches = re.findall(pattern, user_message.lower())
            if (matches):
                # Extract and save facts to memory
                pass

        # Debug: print what is being saved
        print(f"[MEMORY SAVE] user_id={user_id} | extracted_facts={matches if ('matches' in locals() and matches) else 'None'} | message='{user_message}'")

        # Extract any command from the text
        command_regex = r"^\/(\w+)(?:\s+(.*))?$"
        command_match = re.match(command_regex, user_message)
        command = None
        if command_match:
            command = {
                'type': command_match.group(1).lower(),
                'text': command_match.group(2) or ''
            }

        # For simple case where we can use traditional methods
        if (command and command.get('type')):
            command_type = command.get('type')
            command_text = command.get('text', '')

            # Check for special PDF proofreading/processing requests
            pdf_reference_terms = ["pdf", "document", "file", "attached", "attachment"]
            is_pdf_reference = (any((term in command_text.lower()) for term in pdf_reference_terms) or (command_text.strip() == ""))

            # Use traditional approach for commands
            memory_facts = []
            if (user_id):
                # Load memory facts
                pass
            memory_context = '\n'.join(memory_facts)

            # Format chat history for the model API using the updated function
            formatted_history = format_chat_history_for_api(chat_history)

            # Process with traditional approach
            # Handle different command types
            if (command_type == 'proofread'):
                # Handle proofread command
                system_prompt = """
                You are a professional proofreader and editor. Your task is to:
                1. Fix any spelling errors, grammatical mistakes, or typos
                2. Improve sentence structure for clarity
                3. Enhance word choice where appropriate
                4. Fix punctuation and formatting issues
                
                Return the corrected text along with a brief explanation of changes made.
                """
                
                if (is_pdf_reference and pdf_content):
                    enhanced_prompt = f"Please proofread and improve the following document: \n\n{pdf_content}"
                else:
                    enhanced_prompt = f"Please proofread and improve the following text: \n\n{command_text}"
                
                response = get_ai_response(enhanced_prompt, formatted_history, system_prompt, g.current_language)
                formatted_response = f"<div class='proofread-result'><h5>Proofreading Results</h5>{response}</div>"
            
            elif (command_type == 'summarize'):
                system_prompt = """
                You are a professional summarizer. Your task is to:
                1. Read the content thoroughly 
                2. Extract the main points, key arguments, and conclusions
                3. Create a concise and comprehensive summary
                4. Maintain the original meaning and intent
                
                Provide the summary in a well-structured format with bullet points for key takeaways.
                """
                
                if (is_pdf_reference and pdf_content):
                    enhanced_prompt = f"Please summarize the following document: \n\n{pdf_content}"
                else:
                    enhanced_prompt = f"Please summarize the following text: \n\n{command_text}"
                
                response = get_ai_response(enhanced_prompt, formatted_history, system_prompt, g.current_language)
                formatted_response = f"<div class='summary-result'><h5>Summary Results</h5>{response}</div>"
                
            # Add other command types as needed...
            else:
                # Default to study assistance
                system_prompt = """
                You are a study assistant AI specialized in education and learning.
                Your goal is to provide clear, educational responses that help the user understand concepts.
                When explaining difficult topics:
                - Break them down into simpler components
                - Use examples and analogies where appropriate
                - Connect new information to concepts the user likely already understands
                - Encourage critical thinking rather than giving direct answers to homework questions
                """
                
                enhanced_prompt = enhanced_user_message  # Use the enhanced message with file context
                if (memory_context):
                    enhanced_prompt = f"{memory_context}\n\n{enhanced_prompt}"
                
                response = get_ai_response(enhanced_prompt, formatted_history, system_prompt, g.current_language)
                formatted_response = "<p>" + response.replace("\n", "<br>") + "</p>"
        else:
            # USE MCP FOR NORMAL CHAT INTERACTIONS
            from mcp.model_adapter import MCPModelFactory
            from agents.utils import create_mcp_context_from_inputs, extract_metrics_from_mcp_response

            # Initialize MCP context
            context_type = "study"

            # Get file name if available
            filename = None
            if 'current_file' in session and pdf_content:
                filename = session['current_file'].get('filename')            # Create MCP context from inputs, including file content
            mcp_context = create_mcp_context_from_inputs(
                user_input=user_message,
                user_id=user_id,
                session_id=session_id,
                document_text=pdf_content,  # The PDF content will be properly included here
                chat_history=chat_history,
                context_type=context_type
            )
            
            # Add a system instruction to emphasize using the document content in responses
            if pdf_content:
                mcp_context.add_system_instruction(
                    "This conversation includes an uploaded document. When the user asks about the document or its contents, " +
                    "you MUST reference and use information from the document in your response. " +
                    "The document text has been provided in the context."
                )            # If file is present, add explicit metadata to help MCP understand the context better
            if 'current_file' in session and pdf_content:
                from mcp.context import ContextType, ContextMetadata

                # Add file metadata to the context
                file_metadata = {
                    "filename": session['current_file'].get('filename', 'document.pdf'),
                    "file_id": session['current_file'].get('file_id', ''),
                    "file_type": os.path.splitext(session['current_file'].get('filename', ''))[1][1:].lower() or 'pdf',
                    "has_content": bool(pdf_content),
                    "content_length": len(pdf_content) if pdf_content else 0
                }

                # Use the correct ContextType with more explicit instructions about using the document content
                file_context_message = {
                    "file_context": f"The user has uploaded a document named '{file_metadata['filename']}'. " +
                                   f"The content of this document has been included in the conversation context. " +
                                   f"When the user asks about 'the file' or 'the document', they are referring to this document. " +
                                   f"IMPORTANT: You must reference the document content when responding to questions about it.",
                    "response_requirements": "When the user asks about the document, make sure to extract and use relevant information from the document in your response. " +
                                            "If the user asks for information that may be contained in the document, check the document content first.",
                    "file_metadata": file_metadata                        
                }

                # Create and add the element with high importance to ensure it's prioritized
                mcp_context.add_element(
                    content=file_context_message,
                    type_=ContextType.USER_MEMORY,  # Use USER_MEMORY which is a valid ContextType
                    metadata=ContextMetadata(source="file_upload", importance=10)
                )

            # Get model adapter
            model_adapter = MCPModelFactory.create(model_name="gemini")

            # Generate response using MCP
            response_obj = await model_adapter.generate_with_context(enhanced_user_message, mcp_context)
            response = response_obj.text

            # Format the response for display
            formatted_response = "<p>" + response.replace("\n", "<br>") + "</p>"

            # Extract token metrics for usage tracking
            metrics = extract_metrics_from_mcp_response(response_obj)
            tokens_used = metrics.get('total_tokens', 0)            # Track token usage
            track_token_usage_for_api_call(user_id, user_message, response, tokens_used)
        
        # Save assistant response to Firestore
        save_chat_message(user_id, 'study', response, 'assistant')
          
        # Make sure to check if current_file exists in session and has content
        has_file = bool((pdf_content and 'current_file' in session) or ('current_file' in session and session['current_file'].get('content')))
        
        # Final verification of session state before returning response
        final_state = verify_session_state("study_chat_end")
        print(f"[FINAL SESSION] hasFile = {has_file}, content available: {bool(pdf_content)}")
        
        if has_file:
            print(f"[FINAL SESSION] Filename: {session.get('current_file', {}).get('filename')}")
            print(f"[FINAL SESSION] File ID: {session.get('current_file', {}).get('file_id')}")
            print(f"[FINAL SESSION] Content length: {len(session.get('current_file').get('content', ''))}")
        
        return jsonify({
            'response': formatted_response,
            'hasFile': has_file,
            'fileName': session.get('current_file', {}).get('filename') if has_file else None,
            'fileId': session.get('current_file', {}).get('file_id') if has_file else None
        })
    except Exception as e:
        print(f"Error in study chat: {e}")
        import traceback
        traceback.print_exc()
        error_message = "Sorry, I encountered an error processing your request. Please try again."

        # Try to save the error to Firestore to help with debugging
        try:
            save_chat_message(user_id, 'study', f"ERROR: {str(e)}", 'system')
        except:
            pass
        return jsonify({'response': f"<p>{error_message}</p>"})
@app.route('/study/upload', methods=['POST'])
@login_required
def study_upload():
    # CRITICAL FIX: Clear any old cached files AND Flask session data at the start of each upload
    from file_optimizer import clear_all_session_data, aggressive_session_clear
    
    # Use aggressive clearing for debugging persistent session data
    aggressive_result = aggressive_session_clear(session)
    print(f"[CACHE FIX] Aggressive session clearing result: {aggressive_result}")
    
    clear_result = clear_all_session_data(session)
    print(f"[CACHE FIX] Standard session clearing result: {clear_result}")
    
    # Verify session state before processing upload
    before_state = verify_session_state("pre_upload")
    
    # Double check that the user is properly authenticated
    if not session.get('user_id'):
        # Clear any invalid session data
        session.clear()
        return jsonify({
            'error': 'authentication_required'
        }), 401
    
    if ('file' not in request.files):
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    print(f"[UPLOAD DEBUG] Received upload request for file: {file.filename}")
    print(f"[SESSION CONFIG] Session implementation: {app.session_interface.__class__.__name__}")
    
    if (file.filename == ''):
        return jsonify({'error': 'No selected file'}), 400
        
    if (file):
        try:

            # Save the uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            print(f"[UPLOAD DEBUG] File saved to: {file_path}")
            print(f"[UPLOAD DEBUG] File exists: {os.path.exists(file_path)}")
            print(f"[UPLOAD DEBUG] File size: {os.path.getsize(file_path)} bytes")

            # Extract text from the file
            print(f"[UPLOAD DEBUG] Starting text extraction from file: {filename}")
            text = extract_text_from_file(file_path)
            
            if (not text):
                print(f"[UPLOAD DEBUG] Failed to extract text from file: {filename}")
                return jsonify({'error': 'Could not extract text from the file'}), 400
            
            text_length = len(text) if text else 0
            print(f"[UPLOAD DEBUG] Successfully extracted text, length: {text_length} characters")
            print(f"[UPLOAD DEBUG] Text sample (first 100 chars): {text[:100] if text else 'EMPTY'}")
            
            # Check if this will be stored to Firebase/session
            user_id = session.get('user_id')
            print(f"[UPLOAD DEBUG] User ID from session: {user_id}")
            
            # Store in current_file session variable to enable context in future conversations
            if text:
                print(f"[UPLOAD DEBUG] Storing file content in session, length: {len(text)} characters")
                
                # Generate a random file ID if we don't have one
                file_id = str(uuid.uuid4())
                
                # Store in session                # Save session state before update for comparison
                before_session = session.get('current_file', {})
                before_keys = list(before_session.keys()) if before_session else []
                  # Using convert_to_serializable that was imported at the top of the file
                # No need to redefine or import the function here
                
                # Create file metadata with proper serialization
                session['current_file'] = {
                    'file_id': file_id,
                    'filename': filename,
                    'content': text,
                    'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                session.modified = True
                
                # Force session save by accessing it again
                print(f"[UPLOAD DEBUG] Session updated with file: {filename}, ID: {file_id}")
                print(f"[UPLOAD DEBUG] Verify content in session: {len(session['current_file']['content'])} characters")
                print(f"[UPLOAD DEBUG] Session content first 50 chars: {session['current_file']['content'][:50]}")
                
                # Verify session persistence by checking if the data was properly saved
                print(f"[SESSION PERSISTENCE] Before update - keys: {before_keys}")
                print(f"[SESSION PERSISTENCE] After update - keys: {list(session['current_file'].keys())}")
                print(f"[SESSION PERSISTENCE] Session implementation: {app.session_interface.__class__.__name__}")
                  # Double check session storage
                file_content_len = len(session['current_file']['content'])
                session_id = request.cookies.get('session', 'no-session-cookie')
                print(f"[SESSION PERSISTENCE] Content length in session: {file_content_len} bytes")
                print(f"[SESSION PERSISTENCE] Session cookie exists: {'session' in request.cookies}")
                print(f"[SESSION PERSISTENCE] Session ID: {session_id[:10]}... (truncated)")
                
                # Final verification after session update
                after_state = verify_session_state("post_upload")
                
                # Log the differences between before and after states
                print(f"[SESSION COMPARE] Content before: {before_state.get('content_length', 0)}, after: {after_state.get('content_length', 0)}")
                print(f"[SESSION COMPARE] File ID before: {before_state.get('file_id', 'None')}, after: {after_state.get('file_id', 'None')}")
                print(f"[SESSION COMPARE] Filename before: {before_state.get('filename', 'None')}, after: {after_state.get('filename', 'None')}")
            
            return jsonify({
                'success': True,
                'filename': filename,
                'content': text,
                'message': 'File processed successfully'
            })
            
        except Exception as e:
            print(f"[UPLOAD DEBUG] Global error in file processing: {e}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file'}), 400

# Proofreading Routes
@app.route('/proofread/upload', methods=['POST'])
@login_required
def proofread_upload():
    # Double check that the user is properly authenticated
    if not session.get('user_id'):
        # Clear any invalid session data
        session.clear()
        return jsonify({
            'error': 'authentication_required'
        }), 401
        
    if ('file' not in request.files):
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    
    if (file.filename == ''):
        return jsonify({'error': 'No selected file'}), 400
        
    if (file):
        try:

            # Save the uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            print(f"File saved to: {file_path}")
            print(f"File exists: {os.path.exists(file_path)}")
            print(f"File size: {os.path.getsize(file_path)} bytes")

            # Extract text from the file
            text = extract_text_from_file(file_path)
            
            if (not text):
                return jsonify({'error': 'Could not extract text from the file'}), 400
            
            print(f"Successfully extracted text, length: {len(text)} characters")

            # Get AI to proofread the text

            # Limit text size to avoid token limits
            text_to_process = (text[:4000] if (len(text) > 4000) else text)
            
            prompt = f"""
            You are a professional proofreader and editor. Please carefully proofread the following text and identify ANY errors or improvements, no matter how small.

            Look for:
            - Spelling errors
            - Grammar mistakes
            - Punctuation issues
            - Awkward phrasing
            - Run-on sentences
            - Inconsistencies

            Even if the text seems mostly correct, examine it critically and find areas for improvement.
            
            Text to proofread:
            {text_to_process}

            Format your response as a JSON with the following structure:
            {{
                "corrected_text": "The full corrected text with all errors fixed",
                "corrections": [
                    {{
                        "original": "original text with error",
                        "corrected": "corrected text",
                        "explanation": "detailed explanation of why this needed correction"
                    }}
                ]
            }}

            If there are truly no errors at all (which is rare), return an empty list for "corrections".
            """
            
            response = get_ai_response(prompt)
            print(f"AI proofreading response received, length: {len(response)} characters")
            
            try:

                # Try to parse as JSON, but handle if it's not valid JSON
                json_start = response.find('{')
                json_end = (response.rfind('}') + 1)
                if ((json_start >= 0) and (json_end > json_start)):
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)

                    # Make sure corrections is a list, even if empty
                    if ("corrections" not in result):
                        result["corrections"] = []

                    # If no corrections found but texts differ, create a fallback correction
                    if ((len(result["corrections"]) == 0) and (result["corrected_text"] != text_to_process)):
                        result["corrections"] = [{
                            "original": "Original text",
                            "corrected": "Corrected text",
                            "explanation": "The text contained errors that have been corrected."
                        }]
                        
                else:

                    # Fall back to parsing the response manually
                    corrected_text = text  # Default to original text
                    corrections = []
                    
                    lines = response.split('\n')
                    for i, line in enumerate(lines):
                        if (("original:" in line.lower()) and ((i + 1) < len(lines)) and ("corrected:" in lines[(i + 1)].lower())):
                            original = line.split(":", 1)[1].strip()
                            corrected = lines[(i + 1)].split(":", 1)[1].strip()
                            explanation = ""
                            if (((i + 2) < len(lines)) and ("explanation:" in lines[(i + 2)].lower())):
                                explanation = lines[(i + 2)].split(":", 1)[1].strip()
                            
                            corrections.append({
                                "original": original,
                                "corrected": corrected,
                                "explanation": explanation
                            })
                    
                    result = {
                        "corrected_text": corrected_text,
                        "corrections": corrections
                    }
            except Exception as e:
                print(f"Error parsing JSON response: {e}")
                print(f"Response content: {response[:500]}...")

                # Create a basic structure if parsing fails
                result = {
                    "corrected_text": text,
                    "corrections": [{
                        "original": "Error parsing response",
                        "corrected": "Please try again",
                        "explanation": str(e)
                    }]
                }
            
            try:

                # Generate PDF with corrected text
                pdf_path = create_proofread_pdf(result["corrected_text"], result["corrections"], file_path)
                print(f"PDF created at: {pdf_path}")

                # Generate a unique filename for the PDF
                pdf_filename = f"{os.path.splitext(filename)[0]}_{uuid.uuid4().hex[:8]}_corrected.pdf"
                final_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

                # Copy the PDF to the uploads directory
                import shutil
                shutil.copy2(pdf_path, final_pdf_path)
                print(f"PDF copied to: {final_pdf_path}")
                print(f"PDF exists at destination: {os.path.exists(final_pdf_path)}")

                # Make sure the upload folder has proper permissions (for Render deployment)
                if (os.environ.get('RENDER')):
                    os.chmod(final_pdf_path, 0o644)  # Read/write for owner, read for others
                    print(f"Set permissions on PDF file")

                # Create a URL for the PDF
                pdf_url = url_for('download_file', filename=pdf_filename, _external=True)
                
                return jsonify({
                    'pdf_url': pdf_url,
                    'corrections': result["corrections"]
                })
            except Exception as e:
                print(f"Error generating or saving PDF: {e}")
                return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500
        except Exception as e:
            print(f"Global error in file processing: {e}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file'}), 400

# New route: proofread text input
@app.route('/proofread/text', methods=['POST'])
@login_required
async def proofread_text():
    # Double check that the user is properly authenticated
    if not session.get('user_id'):
        # Clear any invalid session data
        session.clear()
        return jsonify({
            'response': "<p>You need to be logged in to use the chat. Please login first.</p>",
            'error': 'authentication_required'
        }), 401
        
    data = (request.get_json() or {})
    text = data.get('text', '').strip()
    user_id = session.get('user_id')
    session_id = (data.get('sessionId') or str(int((time.time() * 1000))))
    
    if (not text):
        return jsonify({'error': 'No text provided'}), 400
        
    try:

        # Check token limits
        can_use, remaining_tokens = check_user_token_limit(user_id)
        if (not can_use):
            return jsonify({
                'error': 'Token limit exceeded',
                'message': "You've reached your daily token limit. Please try again tomorrow or upgrade to premium for a higher limit."
            }), 429

        # Limit length for tokens
        text_to_process = (text[:4000] if (len(text) > 4000) else text)

        # USE MCP FOR PROOFREADING
        from mcp.model_adapter import MCPModelFactory
        from agents.utils import create_mcp_context_from_inputs, extract_metrics_from_mcp_response
        from mcp.context import ContextType, ContextMetadata

        # Create MCP context
        mcp_context = create_mcp_context_from_inputs(
            user_input=text_to_process,
            user_id=user_id,
            session_id=session_id,
            context_type="proofread"
        )

        # Add specific proofreading instructions
        mcp_context.add_system_instruction(
            """
            You are a professional proofreader and editor. Please carefully proofread the following text and identify ANY errors or improvements.
            Look for:
            - Spelling errors
            - Grammar mistakes
            - Punctuation issues
            - Awkward phrasing
            - Run-on sentences
            - Inconsistencies
            
            Format your response as a JSON with the following structure:
            {
                "corrected_text": "The full corrected text with all errors fixed",
                "corrections": [
                    {
                        "original": "original text with error",
                        "corrected": "corrected text",
                        "explanation": "detailed explanation of why this needed correction"
                    }
                ]
            }
            
            If there are truly no errors at all (which is rare), return an empty list for "corrections".
            """
        )

        # Get model adapter
        model_adapter = MCPModelFactory.create(model_name="gemini")

        # Generate response
        response_obj = await model_adapter.generate_with_context("Please proofread this text", mcp_context)
        response = response_obj.text

        # Extract metrics for usage tracking
        metrics = extract_metrics_from_mcp_response(response_obj)
        tokens_used = metrics.get('total_tokens', 0)

        # Track token usage
        track_token_usage_for_api_call(user_id, "Proofread text", response, tokens_used)

        # Parse JSON from AI response
        json_start = response.find('{')
        json_end = (response.rfind('}') + 1)
        result = {'corrected_text': text_to_process, 'corrections': []}
        
        if ((json_start >= 0) and (json_end > json_start)):
            try:
                import json
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
            except Exception as json_error:
                print(f"Error parsing JSON from AI response: {json_error}")

        # Prepare a temporary original file for PDF header
        temp_txt = os.path.join(tempfile.gettempdir(), f"text_{uuid.uuid4().hex}.txt")
        with open(temp_txt, 'w', encoding='utf-8') as f:
            f.write(text_to_process)

        # Generate PDF
        pdf_path = create_proofread_pdf(result['corrected_text'], result['corrections'], temp_txt)

        # Copy PDF to uploads
        pdf_filename = f"text_{uuid.uuid4().hex}_corrected.pdf"
        final_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        shutil.copy2(pdf_path, final_pdf_path)

        # Build URL for download
        if (os.environ.get('RENDER')):
            domain = os.environ.get('RENDER_EXTERNAL_URL', request.host_url.rstrip('/'))
            pdf_url = f"{domain}/download/{pdf_filename}"
        else:
            pdf_url = url_for('download_file', filename=pdf_filename, _external=True)
            
        return jsonify({'pdf_url': pdf_url, 'corrections': result['corrections']})
    except Exception as e:
        print(f"Error in proofread_text: {e}")
        return jsonify({'error': str(e)}), 500

# Excel LangGraph Agent Routes
@app.route('/excel_agent', methods=['POST'])
@login_required
def excel_agent_process():
    """
    Process Excel files with natural language instructions using LangGraph agent
    
    POST Parameters:
        file: Uploaded Excel file (optional)
        instruction: Natural language instruction for the agent
        
    Returns:
        JSON with agent response and thinking log
    """
    try:
        instruction = request.form.get('instruction', '')
        if not instruction:
            return jsonify({'error': 'No instruction provided'}), 400

        # Check if user has exceeded their token limit
        user_id = session.get('user_id')
        can_use, remaining_tokens = check_user_token_limit(user_id)
        
        if not can_use:
            subscription = get_user_subscription(user_id)
            plan = subscription.get('plan', 'free')
            
            limit_message = {
                'en': "You've reached your daily free token limit. Please upgrade to our Premium plan for higher limits.",
                'fr': "Vous avez atteint votre limite quotidienne de jetons gratuits. Veuillez passer au forfait Premium pour des limites plus élevées.",
                'tr': "Günlük ücretsiz token limitinize ulaştınız. Daha yüksek limitler için Premium planına yükseltin.",
                'es': "Has alcanzado tu límite diario de tokens gratuitos. Por favor, actualiza a nuestro plan Premium para límites más altos.",
                'de': "Sie haben Ihr tägliches kostenloses Token-Limit erreicht. Bitte upgraden Sie auf unseren Premium-Plan für höhere Limits.",
                'pt': "Você atingiu seu limite diário de tokens gratuitos. Por favor, atualize para nosso plano Premium para limites mais altos.",
                'ar': "لقد وصلت إلى حد الرموز المجانية اليومية. يرجى الترقية إلى خطة Premium للحصول على حدود أعلى.",
                'az': "Gündəlik pulsuz token limitinə çatmısınız. Daha yüksək limitlər üçün Premium planımıza yüksəldin."
            }
            return jsonify({
                'error': limit_message.get(g.current_language, limit_message['en']),
                'limit_reached': True,
                'plan': plan
            }), 429

        # Import the LangGraph Excel agent
        from langgraph_excel_agent import get_excel_agent
        agent = get_excel_agent()
        
        # Handle file upload
        uploaded_file = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and file.filename.endswith(('.xlsx', '.xls')):
                # Save file temporarily
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
                file.save(temp_file.name)
                
                uploaded_file = {
                    "path": temp_file.name,
                    "filename": file.filename,
                    "type": "file"
                }
            elif file and file.filename:
                return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
        
        # If no file uploaded, treat as Excel generation request
        if not uploaded_file:
            # Create a dummy file reference for generation
            uploaded_file = {
                "path": None,
                "filename": "generated_file.xlsx", 
                "type": "generation"
            }

        # Process with the agent
        import asyncio
        result = asyncio.run(agent.process_request(uploaded_file, instruction))
        
        # Track token usage
        track_token_usage_for_api_call(user_id, instruction, "Excel Agent Processing")
        
        # Clean up temporary file if created
        if uploaded_file and uploaded_file.get("path") and uploaded_file["type"] == "file":
            try:
                os.unlink(uploaded_file["path"])
            except:
                pass
        
        return jsonify({
            'success': True,
            'thinking_log': result.get('thinking_log', []),
            'final_output': result.get('final_output', {}),
            'session_id': result.get('session_id')
        })
        
    except Exception as e:
        print(f"Error in Excel agent processing: {e}")
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500

@app.route('/excel_agent_thinking/<session_id>', methods=['GET'])
@login_required
def get_excel_agent_thinking(session_id):
    """
    Get real-time thinking updates for an Excel agent session
    
    Parameters:
        session_id: The session ID from the agent process
        
    Returns:
        JSON with current thinking log
    """
    try:
        # For now, return empty thinking log
        # In a full implementation, this would track live agent progress
        return jsonify({
            'success': True,
            'thinking_log': [],
            'is_complete': True
        })
        
    except Exception as e:
        print(f"Error getting agent thinking: {e}")
        return jsonify({'error': f'Error retrieving thinking log: {str(e)}'}), 500

@app.route('/excel_agent_upload', methods=['POST'])
@login_required
def excel_agent_file_upload():
    """
    Handle file upload for Excel agent (returns file info for frontend)
    
    Returns:
        JSON with file information for display
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
        
        # Read file info without processing
        import pandas as pd
        import tempfile
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        file.save(temp_file.name)
        
        try:
            df = pd.read_excel(temp_file.name)
            file_info = {
                'filename': file.filename,
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'preview': df.head(3).to_dict('records'),
                'file_path': temp_file.name
            }
            
            return jsonify({
                'success': True,
                'file_info': file_info
            })
            
        except Exception as e:
            os.unlink(temp_file.name)
            return jsonify({'error': f'Error reading Excel file: {str(e)}'}), 400
            
    except Exception as e:
        print(f"Error in file upload: {e}")
        return jsonify({'error': f'Error uploading file: {str(e)}'}), 500
        

# ...existing code...
