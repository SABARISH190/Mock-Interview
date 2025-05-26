// Main JavaScript for Mock Interview Platform

// Wait for jQuery to be ready
jQuery(document).ready(function($) {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Flash message auto-dismiss
    setTimeout(function() {
        $('.alert-dismissible').alert('close');
    }, 5000);
    
    // Form validation styles
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // File input custom styling
    document.querySelectorAll('.custom-file-input').forEach(function(input) {
        input.addEventListener('change', function(e) {
            var fileName = this.files[0]?.name || 'No file chosen';
            var nextSibling = this.nextElementSibling;
            nextSibling.innerText = fileName;
        });
    });

    // Countdown timer functionality
    function initializeCountdown() {
        const countdownElement = document.getElementById('countdown');
        if (countdownElement && countdownElement.dataset.scheduled) {
            const scheduledTime = new Date(countdownElement.dataset.scheduled).getTime();
            
            const updateCountdown = function() {
                const now = new Date().getTime();
                const distance = scheduledTime - now;
                
                if (distance < 0) {
                    countdownElement.innerHTML = "Ready to Start!";
                    clearInterval(interval);
                    
                    // Show the start button
                    const startButton = document.getElementById('startInterviewBtn');
                    if (startButton) {
                        startButton.classList.remove('d-none');
                    }
                    return;
                }
                
                const hours = Math.floor(distance / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);
                
                countdownElement.innerHTML = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            };
            
            // Update countdown immediately
            updateCountdown();
            
            // Update countdown every second
            const interval = setInterval(updateCountdown, 1000);
        }
    }
    
    // Initialize countdown if element exists
    initializeCountdown();
    
    // Audio recording functionality
    function initializeAudioRecording() {
        const micBtn = document.getElementById('micBtn');
        const audioControls = document.getElementById('audioControls');
        const recordBtn = document.getElementById('recordBtn');
        const recordingBar = document.getElementById('recordingBar');
        const recordingTime = document.getElementById('recordingTime');
        const answerTextarea = document.getElementById('answerTextarea');
        
        if (!micBtn) return;
        
        let isRecording = false;
        let mediaRecorder = null;
        let audioChunks = [];
        let recordingInterval = null;
        
        micBtn.addEventListener('click', function() {
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        });
        
        recordBtn.addEventListener('click', function() {
            stopRecording();
        });
        
        function startRecording() {
            // Check if browser supports audio recording
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                alert("Your browser doesn't support audio recording. Please use a modern browser like Chrome or Firefox.");
                return;
            }
            
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    isRecording = true;
                    micBtn.classList.add('active');
                    audioControls.style.display = 'flex';
                    
                    // Start recording
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.start();
                    
                    mediaRecorder.addEventListener('dataavailable', event => {
                        audioChunks.push(event.data);
                    });
                    
                    mediaRecorder.addEventListener('stop', () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        
                        // Here you would usually send the audio to a speech-to-text service
                        // For demo purposes, we'll just indicate recording happened
                        if (answerTextarea.value) {
                            answerTextarea.value += "\n\n[Voice input recorded - transcription would appear here]";
                        } else {
                            answerTextarea.value = "[Voice input recorded - transcription would appear here]";
                        }
                        
                        // Reset recording state
                        audioChunks = [];
                    });
                    
                    // Update recording timer
                    let recordingSeconds = 0;
                    recordingInterval = setInterval(() => {
                        if (!isRecording) {
                            clearInterval(recordingInterval);
                            return;
                        }
                        
                        recordingSeconds++;
                        const minutes = Math.floor(recordingSeconds / 60);
                        const seconds = recordingSeconds % 60;
                        
                        recordingTime.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                        
                        // Update progress bar (max 3 minutes)
                        const progressPercent = Math.min(100, (recordingSeconds / 180) * 100);
                        recordingBar.style.width = `${progressPercent}%`;
                        
                        // Auto-stop after 3 minutes
                        if (recordingSeconds >= 180) {
                            stopRecording();
                        }
                    }, 1000);
                })
                .catch(error => {
                    console.error('Error accessing microphone:', error);
                    alert("Error accessing your microphone. Please check your permissions.");
                });
        }
        
        function stopRecording() {
            if (!isRecording || !mediaRecorder) return;
            
            isRecording = false;
            micBtn.classList.remove('active');
            audioControls.style.display = 'none';
            
            mediaRecorder.stop();
            
            // Stop and clear interval
            clearInterval(recordingInterval);
            
            // Reset recording UI
            recordingTime.textContent = '00:00';
            recordingBar.style.width = '0';
        }
    }
    
    // Initialize audio recording if needed elements exist
    initializeAudioRecording();
    
    // Handle file size validation for uploads
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const maxSize = parseInt(this.dataset.maxSize || 5) * 1024 * 1024; // Default to 5MB
            
            if (this.files.length > 0) {
                const fileSize = this.files[0].size;
                if (fileSize > maxSize) {
                    const maxSizeMB = maxSize / (1024 * 1024);
                    alert(`File size exceeds ${maxSizeMB}MB limit. Please choose a smaller file.`);
                    this.value = '';
                }
            }
        });
    });
    
    // Handle domain and difficulty selection in interview scheduling
    function initializeSelectionCards() {
        // Domain selection
        const domainCards = document.querySelectorAll('.domain-card');
        const domainInput = document.getElementById('selected-domain');
        
        if (domainCards.length && domainInput) {
            domainCards.forEach(card => {
                card.addEventListener('click', function() {
                    // Remove selected class from all cards
                    domainCards.forEach(c => c.classList.remove('selected'));
                    // Add selected class to clicked card
                    this.classList.add('selected');
                    // Set the hidden input value
                    domainInput.value = this.dataset.domain;
                });
            });
            
            // Set default selections if form has values (e.g. on form error)
            if (domainInput.value) {
                const selectedDomainCard = document.querySelector(`.domain-card[data-domain="${domainInput.value}"]`);
                if (selectedDomainCard) {
                    selectedDomainCard.classList.add('selected');
                }
            }
        }
        
        // Difficulty selection
        const difficultyCards = document.querySelectorAll('.difficulty-card');
        const difficultyInput = document.getElementById('selected-difficulty');
        
        if (difficultyCards.length && difficultyInput) {
            difficultyCards.forEach(card => {
                card.addEventListener('click', function() {
                    // Remove selected class from all cards
                    difficultyCards.forEach(c => c.classList.remove('selected'));
                    // Add selected class to clicked card
                    this.classList.add('selected');
                    // Set the hidden input value
                    difficultyInput.value = this.dataset.difficulty;
                });
            });
            
            // Set default selections if form has values (e.g. on form error)
            if (difficultyInput.value) {
                const selectedDifficultyCard = document.querySelector(`.difficulty-card[data-difficulty="${difficultyInput.value}"]`);
                if (selectedDifficultyCard) {
                    selectedDifficultyCard.classList.add('selected');
                }
            }
        }
    }
    
    // Initialize selection cards
    initializeSelectionCards();
});
