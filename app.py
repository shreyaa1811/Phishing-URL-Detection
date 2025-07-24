import streamlit as st
import joblib
import pandas as pd
from urllib.parse import urlparse
import re
from difflib import SequenceMatcher
import time

# Feature Extraction to pass through the ML model

def extract_features_from_url(url) :
  
  #Fixing malformed url's if any
  url = url.replace("\\","/")

  #Ensure http:// or https:// has 2 slashes
  if url.startswith("http:/") and not url.startswith("http://") :
    url = url.replace("http:/","http://")
  elif url.startswith("https:/") and not url.startswith("https://") :
    url = url.replace("https:/","https://")

  #Parsed URL
  parsed = urlparse(url)
  domain = parsed.netloc

  #Domain based features
  has_dash = int('-' in domain)
  has_ip = int(bool(re.match(r'^(\d{1,3}\.){3}\d{1,3}$',domain)))
  hostname_length = len(domain)
  num_dots_domain = domain.count('.')

  #URL based features
  length = len(url)
  num_dots = url.count('.')
  has_https = int(parsed.scheme == 'https')
  has_at = int('@' in domain)
  num_digits = sum(c.isdigit() for c in url)

  path = parsed.path if parsed.path else ''
  num_subdirs = max(path.count('/')-1,0)
  path_length = len(path)

  features =  {
      'length' : length,
      'num_dots': num_dots,
      'has_https': has_https,
      'has_at': has_at,
      'has_dash': has_dash,
      'num_digits': num_digits,
      'has_ip': has_ip,
      'num_subdirs': num_subdirs,
      'hostname_length': hostname_length,
      'path_length': path_length,
      'num_dots_domain': num_dots_domain
  }

  return pd.DataFrame([features])


#Typo-squatting detection helper
def is_typo_squatting(domain,known_domains,threshold=0.8) :
  domain = domain.lower().strip()
  domain_name = domain.split('.')[0]
  for kd in known_domains :
    kd = kd.lower().strip()
    kd_name = kd.split('.')[0]
    ratio = SequenceMatcher(None,domain,kd).ratio()
    if ratio > threshold and domain!=kd :
      if domain_name == kd_name:
         continue
      return True
    
  return False

#Conditions based on rule based overriding
def after_prediction(domain,ml_prediction,known_domains,suspicious_patterns) :

  #If ML model returns safe but there is some kind of spelling mishap it will be checked through this
  if ml_prediction == 0 and is_typo_squatting(domain,known_domains) :
    return 1
  
  #If ML model returns phishing but this domain exists - just looks suspicious
  if ml_prediction == 1 and domain in known_domains :
    return 0
  
  #If ML model fails to detect any suspicious pattern
  for pattern in suspicious_patterns :
    if pattern in domain :
      return 1

  return ml_prediction

# Loading my model 
model = joblib.load('phishing_model.pkl')

#List of known domains
known_domains = [
    "google.com", "gmail.com", "youtube.com", "google.co.in",
    "facebook.com", "instagram.com", "whatsapp.com", "meta.com",
    "microsoft.com", "office.com", "live.com", "outlook.com", "office365.com",
    "apple.com", "icloud.com", "itunes.com", "me.com",
    "amazon.com", "primevideo.com", "amazon.in",
    "netflix.com", "disneyplus.com", "hulu.com",
    "paypal.com", "venmo.com", "paypalobjects.com",
    "linkedin.com", "twitter.com", "x.com",
    "snapchat.com", "tiktok.com", "pinterest.com",
    "ebay.com", "alibaba.com", "aliexpress.com", "etsy.com",
    "dhl.com", "fedex.com", "ups.com", "usps.com",
    "chase.com", "bankofamerica.com", "wellsfargo.com",
    "hsbc.com", "santander.com", "barclays.co.uk", "lloydsbank.com",
    "monzo.com", "starlingbank.com", "natwest.com", "halifax.co.uk",
    "americanexpress.com", "amex.com", "capitalone.com",
    "coinbase.com", "binance.com", "crypto.com",
    "naver.com", "rakuten.co.jp", "jcb.co.jp",
    "dpd.com", "royalmail.com", "canadapost-postescanada.ca",
    "lexisnexis.com", "dropbox.com", "zoom.us",
    "steamcommunity.com", "epicgames.com", "origin.com", "battle.net",
    "icloud.com", "me.com", "mac.com",
    "verizon.com", "att.com", "tmobile.com", "sprint.com",
    "orange.fr", "vodafone.com", "telefonica.com",
    "gov.uk", "gov.in", "irs.gov", "ssa.gov", "nhs.uk"
]

suspicious_patterns = ['secure-', 'account-', 'login-', 'verify-', 'update-', 'signin-', 'authenticate-']

#Streamlit app UI
st.set_page_config(page_title="Phishing URL Detector", layout="centered")



st.title("🔍 Phishing URL Detector")
st.markdown("Enter a URL to check if it's **phishing** or **legitimate**.")

url = st.text_input("🔗 Enter URL",value="https://")



if st.button("Check URL") :
  if url :
    try :
        if not url.startswith('http') :
            st.error("Please enter a valid url starting with http:// or https://")
        else :
            with st.spinner('Analyzing URL...'):
              time.sleep(1)  
        
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
              domain = domain[4:]  # strip www.
            X_input = extract_features_from_url(url)
            ml_pred = model.predict(X_input)[0]
            final = after_prediction(domain, ml_pred, known_domains, suspicious_patterns)

            if final == 1:
                st.error(f"🚨 This URL is likely **phishing**.")
            elif final == 0:
                st.success(f"✅ This URL appears **legitimate**.")
            with st.expander("🔎 See extracted features"):
                st.json(X_input.iloc[0].to_dict())



    except Exception as e:
        st.error(f"Error processing the URL: {e}")

  