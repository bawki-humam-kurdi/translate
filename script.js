document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const translateBtn = document.getElementById('translateBtn');
    const progressSection = document.getElementById('progressSection');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultSection = document.getElementById('resultSection');
    const translatedVideo = document.getElementById('translatedVideo');
    const downloadVideoBtn = document.getElementById('downloadVideoBtn');
    const downloadSubtitleBtn = document.getElementById('downloadSubtitleBtn');
    
    let uploadedFile = null;

    // Drag and drop functionality
    dropArea.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length) {
            handleFiles(e.target.files);
        }
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    dropArea.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    function handleFiles(files) {
        const file = files[0];
        if (file.type.startsWith('video/')) {
            uploadedFile = file;
            dropArea.querySelector('p').textContent = file.name;
            translateBtn.disabled = false;
        } else {
            alert('تکایە تەنها ڤیدیۆ باربکە!');
        }
    }

    // Translate button click
    translateBtn.addEventListener('click', function() {
        if (!uploadedFile) {
            alert('تکایە یەک ڤیدیۆ هەڵبژێرە!');
            return;
        }

        const sourceLang = document.getElementById('sourceLang').value;
        startTranslation(uploadedFile, sourceLang);
    });

    // Simulate translation process (in a real app, this would call your backend)
    function startTranslation(file, sourceLang) {
        progressSection.style.display = 'block';
        progressText.textContent = 'دەنگەکە دەنووسرێتەوە...';
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            progressBar.style.width = `${progress}%`;
            
            if (progress === 25) {
                progressText.textContent = 'نووسراوەکە دەوەرگێردرێت...';
            } else if (progress === 60) {
                progressText.textContent = 'ژێرنووسەکە زیاد دەکرێت بۆ ڤیدیۆکە...';
            } else if (progress >= 100) {
                clearInterval(interval);
                progressText.textContent = 'وەرگێران تەواو بوو!';
                showResult(file);
            }
        }, 300);
    }

    function showResult(file) {
        resultSection.style.display = 'block';
        
        // In a real app, this would be the translated video from the server
        const videoURL = URL.createObjectURL(file);
        translatedVideo.src = videoURL;
        
        // Setup download buttons
        downloadVideoBtn.addEventListener('click', () => {
            downloadFile(videoURL, 'translated_video.mp4');
        });
        
        // In a real app, this would download the actual subtitle file
        downloadSubtitleBtn.addEventListener('click', () => {
            const subtitleContent = `1\n00:00:00,000 --> 00:00:05,000\nئەمە نموونەیەکی ژێرنووسی کوردییە`;
            const blob = new Blob([subtitleContent], { type: 'text/plain' });
            const subtitleURL = URL.createObjectURL(blob);
            downloadFile(subtitleURL, 'kurdish_subtitle.srt');
        });
    }

    function downloadFile(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
});