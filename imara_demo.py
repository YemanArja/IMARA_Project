import json
import os
import pyaudio
from vosk import Model, KaldiRecognizer
import ollama
from gtts import gTTS
import pygame
import time
from datetime import datetime

# ==========================================
# 1. إعداد الصوت (يدعم تغيير اللغة آلياً)
# ==========================================
def speak(text, lang='ar'):
    print(f"IMARA: {text}")
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save("reply.mp3")
        
        pygame.mixer.init()
        pygame.mixer.music.load("reply.mp3")
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1) 
            
        pygame.mixer.quit()
        if os.path.exists("reply.mp3"):
            os.remove("reply.mp3")
    except Exception as e:
        print("تأكد من اتصال اللابتوب بالإنترنت لنطق الصوت.")

# ==========================================
# 2. تحميل نماذج السمع
# ==========================================
print("جاري تحميل نماذج الصوت (عربي + إنجليزي)... يرجى الانتظار.")
model_ar = Model("vosk-model-ar")
rec_ar = KaldiRecognizer(model_ar, 16000)

model_en = Model("vosk-model-en")
rec_en = KaldiRecognizer(model_en, 16000)

p = pyaudio.PyAudio()
# تم تقليل الـ buffer هنا لتسريع الاستجابة
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)

# ==========================================
# 3. قاعدة البيانات (هنا يمكنك زيادة الأسماء براحتك)
# ==========================================
database = {
    "أحمد": "الدكتور أحمد متواجد في مكتب 101",
    "ahmad": "Dr. Ahmad is in office 101",
    "معتصم": "معتصم غائب اليوم",
    "motasem": "Motasem is absent today",
    "وجد": "وجد متواجدة في مختبر الروبوتات",
    "wajd": "Wajd is in the robotics lab",
    "يمان": "يمان هو مبرمج نظام إيمارا وطالب في تخصص الذكاء الاصطناعي",
    "yeman": "Yeman is the AI developer of IMARA system"
}

# ==========================================
# 4. الذكاء الاصطناعي (مع حقن التاريخ والمكان)
# ==========================================
def chat_with_imara(user_input, lang):
    # سحب التاريخ والوقت الحقيقي من اللابتوب
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")
    location = "إربد، الأردن" if lang == 'ar' else "Irbid, Jordan"
    
    context = ""
    for name, info in database.items():
        if name in user_input.lower():
            context += f"معلومة للرد: {info}. "

    # توجيه الروبوت بناءً على اللغة المختارة
    if lang == 'ar':
        prompt = f"""أنت روبوت استقبال ذكي اسمك IMARA. أجب باختصار شديد ولطف باللغة العربية.
        معلوماتك العامة اليوم: التاريخ {current_date}، الساعة {current_time}، وأنت الآن في {location}.
        إذا سئلت عن شخص، أجب باستخدام هذه المعلومة فقط: {context}"""
    else:
        prompt = f"""You are a smart reception robot named IMARA. Answer very briefly and politely in English.
        Current info: Date is {current_date}, Time is {current_time}, Location is {location}.
        If asked about a person, use only this info: {context}"""
        
    response = ollama.chat(model='qwen2.5:1.5b', messages=[
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': user_input}
    ])
    return response['message']['content']

# ==========================================
# 5. دوال الاستماع (منفصلة لمنع التقطيع)
# ==========================================
def listen_language_choice():
    print("\n[IMARA تنتظر اختيار اللغة / Waiting for language choice...]")
    stream.start_stream()
    while True:
        # تقليل القراءة لتسريع الالتقاط
        data = stream.read(2048, exception_on_overflow=False)
        
        is_ar = rec_ar.AcceptWaveform(data)
        is_en = rec_en.AcceptWaveform(data)
        
        if is_ar or is_en:
            text_ar = json.loads(rec_ar.Result()).get("text", "")
            text_en = json.loads(rec_en.Result()).get("text", "")
            
            if "عربي" in text_ar or "عربية" in text_ar:
                stream.stop_stream()
                return "ar"
            elif "english" in text_en:
                stream.stop_stream()
                return "en"

def listen_main(lang):
    prompt_text = "[IMARA تستمع الآن (عربي)...]" if lang == 'ar' else "[IMARA is listening (English)...]"
    print(f"\n{prompt_text}")
    stream.start_stream()
    while True:
        # تقليل القراءة لتسريع الالتقاط
        data = stream.read(2048, exception_on_overflow=False)
        
        # لتخفيف الضغط: نشغل فقط الأذن الخاصة باللغة المختارة
        if lang == 'ar':
            if rec_ar.AcceptWaveform(data):
                text = json.loads(rec_ar.Result()).get("text", "")
                if text.strip():
                    print(f"أنت قلت: {text}")
                    stream.stop_stream()
                    return text
        else:
            if rec_en.AcceptWaveform(data):
                text = json.loads(rec_en.Result()).get("text", "")
                if text.strip():
                    print(f"You said: {text}")
                    stream.stop_stream()
                    return text

# ==========================================
# 6. حلقة التشغيل الرئيسية
# ==========================================
if __name__ == "__main__":
    # السؤال الأولي
    speak("مرحباً بك. هل تتحدث العربية؟ أم الإنجليزية؟ Welcome, do you speak Arabic or English?", lang='ar')
    
    # انتظار الإجابة من المستخدم
    active_lang = listen_language_choice()
    
    # تأكيد الاختيار
    if active_lang == 'ar':
        speak("أهلاً بك. نظام إيمارا جاهز للاستقبال باللغة العربية.", lang='ar')
    else:
        speak("Welcome. IMARA system is ready in English.", lang='en')

    # الاستمرار باللغة المختارة
    while True:
        user_text = listen_main(active_lang)
        if user_text:
            # إضافة استجابة فورية للمستخدم للشعور بالسرعة
            if active_lang == 'ar':
                print("IMARA: ثواني، جاري التفكير...")
            else:
                print("IMARA: Thinking...")
                
            if active_lang == 'ar' and any(word in user_text for word in ["خروج", "توقف"]):
                speak("إلى اللقاء، سعدت بخدمتك.", lang='ar')
                break
            elif active_lang == 'en' and any(word in user_text for word in ["exit", "stop", "quit"]):
                speak("Goodbye, happy to help.", lang='en')
                break
            
            reply = chat_with_imara(user_text, active_lang)
            speak(reply, lang=active_lang)