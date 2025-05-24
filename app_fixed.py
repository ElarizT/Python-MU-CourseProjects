"""
LightYearAI - An AI-powered assistant
"""
import os
import json
import uuid
import tempfile
import sys
import re
import time
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, g, flash
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
