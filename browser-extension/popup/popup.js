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
        // Обновляем баланс после выполнения сценария
        await updateBalance();
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
  try {
    const result = await chrome.storage.local.get('authToken');
    const token = result.authToken;
    
    if (!token) {
      showUnauthenticatedUI();
      return;
    }

    // Проверяем валидность токена
    const response = await fetch('http://localhost:8000/api/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      const userData = await response.json();
      document.getElementById('current-user').textContent = userData.name;
      
      // Сохраняем роль пользователя
      await chrome.storage.local.set({ 
        userRole: userData.user_role 
      });
      
      // Получаем баланс пользователя
      await updateBalance();
      
      // Логируем роль пользователя
      console.log('Авторизованный пользователь:', {
        name: userData.name,
        email: userData.email,
        role: userData.user_role
      });
      
      // Добавляем индикатор роли
      const roleIndicator = document.createElement('span');
      roleIndicator.className = 'user-role';
      const iconRole = document.createElement('img');
      iconRole.className = 'crown-icon';
      if (userData.user_role === 'admin') {
        roleIndicator.innerHTML = 'Администратор';
        iconRole.src = '../icons/crown-icon.png';
      } else {
        roleIndicator.innerHTML = 'Пользователь';
        iconRole.src = '../icons/user-icon.png';
      }
      document.getElementById('current-user-section').appendChild(roleIndicator);
      document.getElementById('icon-section').appendChild(iconRole);
    showAuthenticatedUI();
    } else {
      // Если токен невалиден, очищаем его
      await chrome.storage.local.remove('authToken');
      await chrome.storage.local.remove('userRole');
      showUnauthenticatedUI();
    }
  } catch (error) {
    console.error('Auth check failed:', error);
    showUnauthenticatedUI();
  }
}

async function updateBalance() {
  try {
    const result = await chrome.storage.local.get('authToken');
    const token = result.authToken;
    
    if (!token) return;
    
    const balanceResponse = await fetch('http://localhost:8000/api/credits/balance', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (balanceResponse.ok) {
      const balanceData = await balanceResponse.json();
      document.getElementById('user-balance').textContent = balanceData.balance + ' ₮';
    }
  } catch (error) {
    console.error('Failed to update balance:', error);
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
    const errorElement = document.getElementById('login-error');
    
    try {
      console.log('Attempting to connect to server...');
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
        errorElement.textContent = ''; // Очищаем ошибку при успешном входе
        // Проверяем статус авторизации после сохранения токена
        await checkAuthStatus();
      } else {
        const errorData = await response.json();
        errorElement.textContent = errorData.detail || 'Ошибка авторизации';
        console.error('Login failed:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData.detail || 'Ошибка авторизации'
        });
      }
    } catch (error) {
      errorElement.textContent = 'Ошибка соединения с сервером';
      console.error('Login error:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      });
    }
  });

  // Обработка регистрации
  document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('register-name').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const messageElement = document.getElementById('register-message');
  
    // Валидация
    if (!name || name.length < 2) {
      messageElement.textContent = 'Имя должно содержать минимум 2 символа';
      messageElement.className = 'error-message';
      return;
    }
    
    if (password !== confirmPassword) {
      messageElement.textContent = 'Пароли не совпадают';
      messageElement.className = 'error-message';
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
        messageElement.textContent = 'Регистрация успешна! Войдите в систему';
        messageElement.className = 'error-message success';
        document.querySelector('[data-tab="login"]').click();
      } else {
        messageElement.textContent = data.detail || 'Ошибка регистрации';
        messageElement.className = 'error-message';
      }
    } catch (error) {
      messageElement.textContent = 'Ошибка сети';
      messageElement.className = 'error-message';
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

// Добавляем обработчик для кнопки добавления кредитов
document.getElementById('add-credits-btn').addEventListener('click', async () => {
  try {
    const result = await chrome.storage.local.get('authToken');
    const token = result.authToken;
    
    if (!token) {
      console.log('Необходима авторизация');
      return;
    }
    
    const response = await fetch('http://localhost:8000/api/credits/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        amount: 100,
        description: 'Пополнение баланса'
      })
    });
    
    if (response.ok) {
      await updateBalance();
      console.log('Баланс успешно пополнен');
    } else {
      const errorData = await response.json();
      console.log(errorData.detail || 'Ошибка при пополнении баланса');
    }
  } catch (error) {
    console.log('Ошибка при пополнении баланса');
}
});
