import aiohttp
import logging
from config import settings

async def get_ai_support_suggestion(user_msg: str, user_stats: str = ""):
    """Uses Gemini API to suggest a professional and 'mogger' style response."""
    if not settings.GEMINI_API_KEY:
        return None
        
    prompt = f"""
    You are the support AI for 'Mogosu Elite', a premium LTC-based automated store.
    The customer had the following issue: "{user_msg}"
    Customer context: {user_stats}
    
    TONE: Confident, elite, professional, with a touch of Romanian 'mogger' energy (Sigma vibe). 
    Keep it high-end and helpful. Avoid generic corporate talk.
    If it's a payment issue, tell them to wait 1-2 mins and then check again.
    
    Provide a draft response for the admin to use.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logging.error(f"Gemini API Error: {e}")
        
    return None
