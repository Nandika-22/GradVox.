import os, requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
res = requests.get(url)
models = res.json().get('models', [])

found_ok = False
for m in models:
    if 'generateContent' in m.get('supportedGenerationMethods', []):
        m_name = m['name'].replace('models/', '')
        if '2.5-flash' not in m_name: continue
        post_url = f'https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={api_key}'
        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'hi'}]}]}
        res2 = requests.post(post_url, json=payload)
        data = res2.json()
        if 'error' in data:
            print(m_name, 'ERROR', data['error']['code'])
        else:
            print(m_name, 'OK!!!')
            found_ok = True
