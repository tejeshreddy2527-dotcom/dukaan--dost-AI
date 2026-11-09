/**
 * Dukaan Dost AI - Voice Assistant Engine
 * Real Gnani AI STT (Prisma) & TTS (Timbre) integration with WAV recorder,
 * browser SpeechSynthesis fallback, animated waveform visualizer, and multilingual greeting.
 */

class VoiceAssistantEngine {
  constructor(options = {}) {
    this.currentLanguage = options.defaultLanguage || 'te-IN';
    this.status = 'idle'; // 'idle' | 'listening' | 'thinking' | 'speaking'
    this.isMuted = false;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.audioContext = null;
    this.currentAudio = null;
    this.pendingConfirmation = null;

    // DOM Elements bindings
    this.orbElement = document.getElementById(options.orbId || 'aiOrb');
    this.statusElement = document.getElementById(options.statusId || 'assistantStatus');
    this.transcriptElement = document.getElementById(options.transcriptId || 'liveTranscript');
    this.soundWavesElement = document.getElementById(options.wavesId || 'soundWaves');
    this.chatHistoryElement = document.getElementById(options.historyId || 'chatHistory');
    this.langSelector = document.getElementById(options.langSelectorId || 'langSelector');

    this.init();
  }

  init() {
    if (this.langSelector) {
      this.langSelector.value = this.currentLanguage;
      this.langSelector.addEventListener('change', (e) => {
        this.setLanguage(e.target.value);
      });
    }

    // Bind orb click to toggle listening
    if (this.orbElement) {
      this.orbElement.addEventListener('click', () => {
        if (this.status === 'listening') {
          this.stopListening();
        } else if (this.status === 'idle') {
          this.startListening();
        }
      });
    }
  }

  setLanguage(lang) {
    this.currentLanguage = lang;
    if (this.langSelector) this.langSelector.value = lang;
    this.playGreeting(false);
  }

  setStatus(newStatus, customText = '') {
    this.status = newStatus;

    if (this.orbElement) {
      this.orbElement.className = `ai-orb ${newStatus}`;
    }

    if (this.soundWavesElement) {
      if (newStatus === 'listening' || newStatus === 'speaking') {
        this.soundWavesElement.classList.add('active');
      } else {
        this.soundWavesElement.classList.remove('active');
      }
    }

    if (this.statusElement) {
      this.statusElement.className = `assistant-status ${newStatus}`;
      const statusLabels = {
        'idle': 'Dukaan Dost Ready',
        'listening': 'Listening to your voice...',
        'thinking': 'Consulting Kirana Database...',
        'speaking': 'Speaking response...'
      };
      const textSpan = this.statusElement.querySelector('.status-text');
      if (textSpan) {
        textSpan.textContent = customText || statusLabels[newStatus] || newStatus;
      }
    }
  }

  async playGreeting(forceAutoplay = false) {
    try {
      const res = await fetch(`/api/greeting?language=${encodeURIComponent(this.currentLanguage)}`);
      const data = await res.json();
      if (!data.success) return;

      const greetingText = data.greeting_text;
      if (this.transcriptElement) {
        this.transcriptElement.textContent = `“${greetingText}”`;
      }

      if (data.audio_url && !this.isMuted) {
        this.playAudioUrl(data.audio_url, greetingText);
      } else if (!this.isMuted) {
        this.speakWithFallback(greetingText, this.currentLanguage);
      }
    } catch (err) {
      console.warn('Greeting fetch failed:', err);
    }
  }

  async startListening() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Microphone access is not supported by your browser. Please use text input.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.setStatus('listening');
      if (this.transcriptElement) {
        this.transcriptElement.textContent = 'Listening... Speak in Telugu, English or Hindi';
      }

      this.audioChunks = [];
      const supportedTypes = [
        'audio/webm;codecs=opus',
        'audio/ogg;codecs=opus',
        'audio/mp4'
      ];
      const mimeType = supportedTypes.find(type => MediaRecorder.isTypeSupported(type));

      this.mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blobType = this.mediaRecorder.mimeType || this.audioChunks[0]?.type || 'audio/webm';
        const rawBlob = new Blob(this.audioChunks, { type: blobType });
        await this.processRecordedAudio(rawBlob);
      };

      this.mediaRecorder.start(250);

      // Avoid cutting off ordinary speech while still bounding the recording length.
      this.recordingTimeout = setTimeout(() => {
        if (this.status === 'listening') {
          this.stopListening();
        }
      }, 60000);

    } catch (err) {
      console.error('Microphone access error:', err);
      this.setStatus('idle');
      alert('Could not access microphone: ' + err.message + '. Please allow microphone permissions in your browser.');
    }
  }

  stopListening() {
    if (this.recordingTimeout) clearTimeout(this.recordingTimeout);
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    this.setStatus('thinking');
  }

  // Convert raw WebM/OGG browser recording into clean 16kHz WAV for Gnani Prisma
  async processRecordedAudio(rawBlob) {
    try {
      const ext = rawBlob.type.includes('ogg') ? '.ogg'
        : (rawBlob.type.includes('mp4') ? '.m4a' : '.webm');
      await this.submitAudio(rawBlob, `recording${ext}`);
    } catch (err) {
      this.showAudioError(err);
    }
  }

  async processAudioFile(file) {
    this.setStatus('thinking', `Processing ${file.name}...`);
    await this.submitAudio(file, file.name);
  }

  async submitAudio(file, filename) {
    try {
      const formData = new FormData();
      formData.append('audio', file, filename);
      formData.append('language', this.currentLanguage);

      const res = await fetch('/api/voice', { method: 'POST', body: formData });
      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || 'Speech transcription failed');
      }

      this.appendMessage('user', data.transcript);
      if (data.command_result) {
        this.handleAssistantResponse(data.command_result, data.audio_url);
      } else {
        this.setStatus('idle');
      }
    } catch (err) {
      this.showAudioError(err);
    }
  }

  showAudioError(err) {
    console.warn('Voice API processing error:', err);
    this.setStatus('idle');
    if (this.transcriptElement) {
      this.transcriptElement.textContent = 'Voice processing note: ' + err.message;
    }
  }

  // Quick WAV encoder in Web Audio API
  async convertToWav(blob) {
    const arrayBuffer = await blob.arrayBuffer();
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    let audioBuffer;
    try {
      audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    } catch (e) {
      // Return raw blob if decoding fails
      return blob;
    }

    const numOfChan = 1;
    const sampleRate = 16000; // 16kHz ideal for Gnani Prisma
    const length = audioBuffer.length * (sampleRate / audioBuffer.sampleRate);
    const offlineCtx = new OfflineAudioContext(numOfChan, length, sampleRate);

    const src = offlineCtx.createBufferSource();
    src.buffer = audioBuffer;
    src.connect(offlineCtx.destination);
    src.start();

    const rendered = await offlineCtx.startRendering();
    const wavBytes = this.bufferToWav(rendered);
    return new Blob([wavBytes], { type: 'audio/wav' });
  }

  bufferToWav(abuffer) {
    const numOfChan = abuffer.numberOfChannels;
    const length = abuffer.length * numOfChan * 2 + 44;
    const out = new DataView(new ArrayBuffer(length));
    const channels = [];
    let sampleRate = abuffer.sampleRate;
    let offset = 0;
    let pos = 0;

    function setUint16(data) { out.setUint16(pos, data, true); pos += 2; }
    function setUint32(data) { out.setUint32(pos, data, true); pos += 4; }

    setUint32(0x46464952); // "RIFF"
    setUint32(length - 8);
    setUint32(0x45564157); // "WAVE"
    setUint32(0x20746d66); // "fmt "
    setUint32(16);
    setUint16(1); // PCM
    setUint16(numOfChan);
    setUint32(sampleRate);
    setUint32(sampleRate * 2 * numOfChan);
    setUint16(numOfChan * 2);
    setUint16(16); // 16-bit
    setUint32(0x61746164); // "data"
    setUint32(length - pos - 4);

    for (let i = 0; i < abuffer.numberOfChannels; i++) {
      channels.push(abuffer.getChannelData(i));
    }

    while (pos < length) {
      for (let i = 0; i < numOfChan; i++) {
        let sample = Math.max(-1, Math.min(1, channels[i][offset]));
        sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
        out.setInt16(pos, sample, true);
        pos += 2;
      }
      offset++;
    }
    return out.buffer;
  }

  // Handle Command Submission (via Voice or Text input)
  async sendCommand(text, confirmed = false) {
    if (!text || !text.trim()) return;

    this.setStatus('thinking');
    if (!confirmed) {
      this.appendMessage('user', text);
    }

    try {
      const res = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          confirmed: confirmed,
          language: this.currentLanguage,
          speak: !this.isMuted
        })
      });

      const data = await res.json();
      this.handleAssistantResponse(data, data.audio_url);

    } catch (err) {
      console.error('Command API error:', err);
      this.setStatus('idle');
      this.appendMessage('assistant', 'Error communicating with server: ' + err.message);
    }
  }

  handleAssistantResponse(data, audioUrl) {
    const replyText = data.reply || (data.success ? 'Operation completed.' : 'Sorry, could not process request.');
    this.appendMessage('assistant', replyText, data.requires_confirmation ? data.pending : null);

    if (this.transcriptElement) {
      this.transcriptElement.textContent = `“${replyText}”`;
    }

    if (data.requires_confirmation) {
      this.pendingConfirmation = data.pending;
      this.setStatus('idle', 'Confirmation Required');
    } else {
      this.pendingConfirmation = null;
    }

    // Speak response
    if (!this.isMuted) {
      if (audioUrl) {
        this.playAudioUrl(audioUrl, replyText);
      } else {
        this.speakWithFallback(replyText, data.language || this.currentLanguage);
      }
    } else {
      this.setStatus('idle');
    }

    // Dispatch global event for dashboard refresh if inventory changed
    if (data.intent === 'add_stock' || data.intent === 'record_sale') {
      window.dispatchEvent(new CustomEvent('inventoryUpdated'));
    }
  }

  playAudioUrl(url, textFallback) {
    this.setStatus('speaking');
    if (this.currentAudio) {
      this.currentAudio.pause();
    }

    this.currentAudio = new Audio(url);
    this.currentAudio.onended = () => {
      this.setStatus('idle');
    };
    this.currentAudio.onerror = () => {
      console.warn('Audio playback error, falling back to speech synthesis');
      this.speakWithFallback(textFallback, this.currentLanguage);
    };

    this.currentAudio.play().catch(e => {
      console.warn('Audio play blocked:', e);
      this.setStatus('idle');
    });
  }

  speakWithFallback(text, language = 'te-IN') {
    if (!window.speechSynthesis) {
      this.setStatus('idle');
      return;
    }

    window.speechSynthesis.cancel();
    this.setStatus('speaking');

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.rate = 0.95;

    // Pick appropriate voice if available
    const voices = window.speechSynthesis.getVoices();
    const match = voices.find(v => v.lang.startsWith(language.split('-')[0]));
    if (match) utterance.voice = match;

    utterance.onend = () => {
      this.setStatus('idle');
    };
    utterance.onerror = () => {
      this.setStatus('idle');
    };

    window.speechSynthesis.speak(utterance);
  }

  appendMessage(sender, text, confirmationData = null) {
    if (!this.chatHistoryElement) return;

    const row = document.createElement('div');
    row.style.cssText = `
      display: flex;
      flex-direction: column;
      align-items: ${sender === 'user' ? 'flex-end' : 'flex-start'};
      margin-bottom: 1rem;
      animation: fadeIn 0.3s ease;
    `;

    const bubble = document.createElement('div');
    bubble.style.cssText = `
      max-width: 82%;
      padding: 0.85rem 1.25rem;
      border-radius: ${sender === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px'};
      background: ${sender === 'user' ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)' : 'rgba(20, 27, 52, 0.85)'};
      border: 1px solid ${sender === 'user' ? 'rgba(255,255,255,0.2)' : 'rgba(139, 92, 246, 0.25)'};
      color: #ffffff;
      font-size: 0.92rem;
      line-height: 1.5;
      box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    `;
    bubble.textContent = text;
    row.appendChild(bubble);

    // If confirmation is needed, add confirmation buttons!
    if (confirmationData) {
      const btnGroup = document.createElement('div');
      btnGroup.style.cssText = 'display: flex; gap: 0.5rem; margin-top: 0.5rem;';

      const confirmBtn = document.createElement('button');
      confirmBtn.className = 'btn-primary btn-mint';
      confirmBtn.style.padding = '0.35rem 0.85rem';
      confirmBtn.style.fontSize = '0.8rem';
      confirmBtn.innerHTML = '✓ Confirm & Save';
      confirmBtn.onclick = () => {
        btnGroup.remove();
        this.sendCommand(`${confirmationData.intent === 'add_stock' ? 'Add' : 'Sell'} ${confirmationData.quantity} ${confirmationData.product}`, true);
      };

      const cancelBtn = document.createElement('button');
      cancelBtn.className = 'btn-outline';
      cancelBtn.style.padding = '0.35rem 0.85rem';
      cancelBtn.style.fontSize = '0.8rem';
      cancelBtn.innerHTML = '✕ Cancel';
      cancelBtn.onclick = () => {
        btnGroup.remove();
        this.appendMessage('assistant', 'Action cancelled. Stock was not modified.');
        this.setStatus('idle');
      };

      btnGroup.appendChild(confirmBtn);
      btnGroup.appendChild(cancelBtn);
      row.appendChild(btnGroup);
    }

    this.chatHistoryElement.appendChild(row);
    this.chatHistoryElement.scrollTop = this.chatHistoryElement.scrollHeight;
  }
}

// Global initialization helper
window.VoiceAssistantEngine = VoiceAssistantEngine;
