from flask import Flask, request, jsonify, send_file
import os
import tempfile
import speech_recognition as sr
from googletrans import Translator
import ffmpeg
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ڕێگای پاشەکەوتکردنی فایلەکان
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# جۆرە فایلە ڕێگامەدراوەکان
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_subtitle_file(text, duration, output_path):
    """ دروستکردنی فایلی ژێرنووسی .srt """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"1\n00:00:00,000 --> {duration}\n{text}")

def extract_audio(video_path, audio_path):
    """ دەرکردنی دەنگ لە ڤیدیۆ """
    try:
        (
            ffmpeg.input(video_path)
            .output(audio_path, ac=1, ar=16000, acodec='pcm_s16le')
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception as e:
        print(f"هەڵە لە دەرکردنی دەنگ: {e}")
        return False

def transcribe_audio(audio_path, language):
    """ ناساندنی دەنگ و گۆڕین بۆ دەق """
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=language)
            return text, None
    except sr.UnknownValueError:
        return None, "نەتوانرا دەنگەکە بناسرێتەوە"
    except sr.RequestError as e:
        return None, f"کێشەی پەیوەندی: {e}"

def translate_text(text, source_lang, target_lang='ku'):
    """ وەرگێڕانی دەق بۆ زمانی کوردی """
    translator = Translator()
    try:
        translation = translator.translate(text, src=source_lang, dest=target_lang)
        return translation.text, None
    except Exception as e:
        return None, f"هەڵە لە وەرگێڕان: {e}"

def get_video_duration(video_path):
    """ بەدەستهێنانی ماوەی ڤیدیۆ """
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['streams'][0]['duration'])
        return str(timedelta(seconds=duration)).replace('.', ',')[:12]
    except:
        return "00:05:00,000"  # ماوەی بنەڕەتی

@app.route('/api/translate', methods=['POST'])
def translate_video():
    """ ڕێگای API بۆ وەرگێڕانی ڤیدیۆ """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'هیچ فایلێک نەنێردراوە'}), 400
    
    file = request.files['file']
    source_lang = request.form.get('lang', 'en')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'هیچ فایلێک هەڵنەبژێردراوە'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'جۆری فایل نادروستە'}), 400

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            # ١. پاشەکەوتکردنی ڤیدیۆ
            video_path = os.path.join(tmp_dir, secure_filename(file.filename))
            file.save(video_path)
            
            # ٢. دەرکردنی دەنگ
            audio_path = os.path.join(tmp_dir, 'audio.wav')
            if not extract_audio(video_path, audio_path):
                return jsonify({'success': False, 'error': 'هەڵە لە دەرکردنی دەنگ'}), 500
            
            # ٣. ناساندنی دەنگ
            text, error = transcribe_audio(audio_path, source_lang)
            if error:
                return jsonify({'success': False, 'error': error}), 400
            
            # ٤. وەرگێڕان بۆ کوردی
            translated, error = translate_text(text, source_lang)
            if error:
                return jsonify({'success': False, 'error': error}), 500
            
            # ٥. دروستکردنی ژێرنووس
            duration = get_video_duration(video_path)
            subtitle_path = os.path.join(tmp_dir, 'subtitle.srt')
            create_subtitle_file(translated, duration, subtitle_path)
            
            # ٦. زیادکردنی ژێرنووس بۆ ڤیدیۆ
            output_path = os.path.join(tmp_dir, 'output.mp4')
            (
                ffmpeg.input(video_path)
                .filter('subtitles', subtitle_path, 
                      force_style="FontName=Noto Sans Kurdish,FontSize=24,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&")
                .output(output_path, vcodec='libx264', crf=23, preset='fast')
                .overwrite_output()
                .run(quiet=True)
            )
            
            # ٧. ناردنی ئەنجامەکە
            return send_file(output_path, as_attachment=True, download_name='translated_video.mp4')
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def index():
    return "خزمەتگوزاری وەرگێڕانی ڤیدیۆ بۆ ژێرنووسی کوردی"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
