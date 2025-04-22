from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import subprocess
from datetime import timedelta
import speech_recognition as sr
from googletrans import Translator
import ffmpeg

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Make sure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    source_lang = request.form.get('source_lang', 'en')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the video (transcription and translation)
        try:
            # Step 1: Extract audio
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio.wav')
            (
                ffmpeg.input(filepath)
                .output(audio_path, ac=1, ar=16000)
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Step 2: Transcribe audio
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language=source_lang)
            
            # Step 3: Translate to Kurdish
            translator = Translator()
            translation = translator.translate(text, src=source_lang, dest='ku')
            
            # Step 4: Create subtitle file
            subtitle_path = os.path.join(app.config['UPLOAD_FOLDER'], 'subtitles.srt')
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write(f"1\n00:00:00,000 --> 00:00:10,000\n{translation.text}")
            
            # Step 5: Burn subtitles into video
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.mp4')
            (
                ffmpeg.input(filepath)
                .filter('subtitles', subtitle_path, force_style='FontName=Noto Sans Arabic,FontSize=24,PrimaryColour=&HFFFFFF&')
                .output(output_path)
                .overwrite_output()
                .run(quiet=True)
            )
            
            return send_file(output_path, as_attachment=True)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)