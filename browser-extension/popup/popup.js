import { STTService } from './core/services/stt-service.js';
import { TTSService } from './core/services/tts-service.js';
import { CommandRouter } from './core/command-router.js';
import { AudioRecorder } from './core/services/recorder.js';

document.addEventListener('DOMContentLoaded', () => {
  const recorder = new AudioRecorder();
  const startBtn = document.getElementById('startBtn');
  const statusEl = document.getElementById('status');

  startBtn.addEventListener('click', async () => {
    try {
      if (recorder.isRecording) {
        // Остановка записи
        const audioBlob = await recorder.stopRecording();
        startBtn.classList.remove('recording');
        statusEl.textContent = 'Обработка...';
        
        const commandText = await STTService.transcribe(audioBlob);
        const { scenario, data } = await CommandRouter.handle(commandText);
        
        if (scenario !== "Общение с ИИ") {
          await TTSService.speak(`Выполняю: ${scenario}`);
        }
        statusEl.textContent = 'Нажмите и говорите';
      } else {
        // Начало записи
        await recorder.startRecording();
        startBtn.classList.add('recording');
        statusEl.textContent = 'Идёт запись...';
      }
    } catch (err) {
      startBtn.classList.remove('recording');
      statusEl.textContent = 'Ошибка! Нажмите снова';
      console.error('Error:', err);
      TTSService.speak(`Ошибка: ${err.message}`);
    }
  });
});

// Инициализация аутентификации
document.addEventListener('DOMContentLoaded', () => {
  checkAuthStatus();
  initAuthForms();
});

async function checkAuthStatus() {
  const token = await chrome.storage.local.get('authToken');
  if (token) {
    showAuthenticatedUI();
  }
}

function initAuthForms() {
  // Переключение табов
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      const tab = btn.dataset.tab;
      document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.toggle('active', form.id === `${tab}-form`);
      });
    });
  });

  // Обработка входа
  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      if (response.ok) {
        const data = await response.json();
        await chrome.storage.local.set({ 
          authToken: data.access_token 
        });
        showAuthenticatedUI();
      }
    } catch (error) {
      showError('Ошибка авторизации');
    }
  });

  // Обработка регистрации
  document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('register-name').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
  
    // Валидация
    if (!name || name.length < 2) {
      showError('Имя должно содержать минимум 2 символа');
      return;
    }
    
    if (password !== confirmPassword) {
      showError('Пароли не совпадают');
      return;
    }
  
    try {
      console.log('Sending:', { 
        name, 
        email, 
        password, 
        password_confirm: confirmPassword 
      });
      
      const response = await fetch('http://localhost:8000/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name, 
          email, 
          password, 
          password_confirm: confirmPassword 
        })
      });
  
      const data = await response.json();
      
      if (response.ok) {
        showSuccess('Регистрация успешна! Войдите в систему');
        document.querySelector('[data-tab="login"]').click();
      } else {
        showError(data.detail || 'Ошибка регистрации');
      }
    } catch (error) {
      showError('Ошибка сети');
    }
  });

  // Выход
  document.getElementById('logout-btn').addEventListener('click', async () => {
    await chrome.storage.local.remove('authToken');
    showUnauthenticatedUI();
  });
}

function showAuthenticatedUI() {
  document.getElementById('auth-forms').style.display = 'none';
  document.getElementById('auth-status').style.display = 'block';
  document.getElementById('main-interface').style.display = 'block';
}

function showUnauthenticatedUI() {
  document.getElementById('auth-forms').style.display = 'block';
  document.getElementById('auth-status').style.display = 'none';
  document.getElementById('main-interface').style.display = 'none';
}

function showError(message) {
  const errorEl = document.createElement('div');
  errorEl.className = 'error-message';
  errorEl.textContent = message;
  document.querySelector('.container').prepend(errorEl);
  setTimeout(() => errorEl.remove(), 3000);
}