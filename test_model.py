import os
import google.generativeai as genai
from dotenv import load_dotenv

# 載入金鑰
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("=== 支援圖片辨識與內容生成的模型清單 ===")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)