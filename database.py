# database.py

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import os
import json

# --- कॉन्फ़िगरेशन ---
MINE_INTERVAL_HOURS = 8
MINE_REWARD = 10.0 # प्रति माइन 10 CHILL कॉइन

# Firebase को इनिशियलाइज़ करें
db = None
try:
    # Render Environment Variable से JSON स्ट्रिंग प्राप्त करें
    firebase_config_json = os.getenv("FIREBASE_CONFIG")
    if not firebase_config_json:
        # यदि Environment Variable नहीं मिला, तो लोकल फ़ाइल चेक करें (लोकल टेस्टिंग के लिए)
        if os.path.exists('firebase-key.json'):
            with open('firebase-key.json', 'r') as f:
                firebase_config = json.load(f)
        else:
            raise ValueError("FIREBASE_CONFIG Env Var या firebase-key.json फ़ाइल नहीं मिली।")
    else:
        # JSON स्ट्रिंग को Python डिक्शनरी में बदलें
        firebase_config = json.loads(firebase_config_json)
    
    # क्रेडेंशियल को डिक्शनरी से लोड करें
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Firestore सफलतापूर्वक कनेक्ट हो गया।")

except Exception as e:
    print(f"❌ ERROR: Firebase कनेक्शन फेल हुआ। कारण: {e}")
    db = None

# --- Firestore फंक्शन्स ---

async def get_user_data(user_id):
    """Firestore से यूजर का डेटा प्राप्त करता है, अगर यूजर नया है तो उसे इनिशियलाइज़ करता है।"""
    if db is None: return None
    
    user_ref = db.collection('users').document(str(user_id))
    doc = user_ref.get()

    if not doc.exists:
        # नए यूजर के लिए शुरुआती डेटा
        initial_data = {
            'balance': 0.0,
            # ISO फॉर्मेट में सबसे पुरानी तारीख।
            'last_mine': datetime.min.isoformat() 
        }
        user_ref.set(initial_data)
        return initial_data
    else:
        return doc.to_dict()

async def can_mine(user_id):
    """जाँच करता है कि यूजर अभी माइन कर सकता है या नहीं।"""
    user = await get_user_data(user_id)
    if user is None: return False, timedelta(seconds=0)
    
    # ISO string को datetime ऑब्जेक्ट में बदलें
    last_mine_dt = datetime.fromisoformat(user['last_mine'])
    
    time_since_last_mine = datetime.now() - last_mine_dt
    
    can_do = time_since_last_mine >= timedelta(hours=MINE_INTERVAL_HOURS)
    return can_do, time_since_last_mine

async def perform_mine(user_id, current_balance):
    """माइनिंग ऑपरेशन करता है और Firestore में डेटा अपडेट करता है।"""
    if db is None: return None
    
    new_balance = current_balance + MINE_REWARD
    
    user_ref = db.collection('users').document(str(user_id))
    
    # डेटा अपडेट करें
    update_data = {
        'balance': new_balance,
        'last_mine': datetime.now().isoformat()
    }
    user_ref.update(update_data)
    
    return MINE_REWARD, new_balance

def get_time_left(time_since_last_mine):
    """माइनिंग के लिए बचा हुआ समय कैलकुलेट करता है।"""
    required_time = timedelta(hours=MINE_INTERVAL_HOURS)
    time_left = required_time - time_since_last_mine
        
    total_seconds = int(time_left.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return f"{hours} घंटे, {minutes} मिनट, {seconds} सेकंड"
