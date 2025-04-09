// Элементы интерфейса
const startButton = document.getElementById('startListening');
const statusDiv = document.getElementById('status');

// Состояние записи
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];

// Обработчик клика по кнопке
startButton.addEventListener('click', async () => {
  if (isRecording) {
    // Остановить запись при повторном нажатии
    mediaRecorder.stop();
    return;
  }

  try {
    isRecording = true;
    startButton.textContent = "⏹ Остановить запись";
    statusDiv.textContent = "Запрос доступа к микрофону...";
    startButton.disabled = true;

    // Запрос доступа к микрофону
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        noiseSuppression: true,
        echoCancellation: true
      }
    });

    // Начать запись
    statusDiv.textContent = "Говорите сейчас...";
    startButton.disabled = false;
    startButton.classList.add('recording');
    
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    // Обработчик данных
    mediaRecorder.ondataavailable = (e) => {
      audioChunks.push(e.data);
    };

    // Остановка записи
    mediaRecorder.onstop = async () => {
      isRecording = false;
      startButton.textContent = "🎤 Начать запись";
      startButton.classList.remove('recording');

      try {
        statusDiv.textContent = "Отправка на сервер...";
        const audioBlob = new Blob(audioChunks, { 
          type: 'audio/webm; codecs=opus' 
        });

        console.log("Формат:", audioBlob.type);
        console.log("Размер:", audioBlob.size, "байт");
        console.log("Длительность:", audioBlob.duration, "сек");

        // Цепочка обработки
        const text = await transcribeAudio(audioBlob);
        const responseText = await generateText(text);
        await playAudio(responseText);
        
        statusDiv.textContent = "Готово!";
      } catch (err) {
        statusDiv.textContent = `Ошибка: ${err.message}`;
      } finally {
        stream.getTracks().forEach(track => track.stop());
        audioChunks = [];
      }
    };

    // Ошибки записи
    mediaRecorder.onerror = (e) => {
      console.error("Ошибка:", e.error);
      statusDiv.textContent = "Ошибка записи";
      isRecording = false;
    };

    mediaRecorder.start();

    // Автоостановка через 60 сек
    setTimeout(() => {
      if (mediaRecorder?.state === "recording") {
        mediaRecorder.stop();
      }
    }, 60000);

  } catch (err) {
    isRecording = false;
    startButton.textContent = "🎤 Начать запись";
    startButton.disabled = false;
    statusDiv.textContent = err.name === 'NotAllowedError' 
      ? "Разрешите доступ в настройках браузера 🔒" 
      : `Ошибка: ${err.message}`;
  }
});

// Отправка аудио на STT
async function transcribeAudio(audioBlob) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'audio.wav');

  const response = await fetch('http://localhost:8000/stt/transcribe', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) throw new Error("Ошибка распознавания");
  const data = await response.json();
  return data.text;
}

// Генерация ответа через LLM
async function generateText(text) {
  const response = await fetch('http://localhost:8000/gemini/generate', {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json' 
    },
    body: JSON.stringify({
      prompt: text,          // Строка с текстом
      max_length: 512,       // Опциональные параметры
      temperature: 0.7       // Можно задать значения по умолчанию
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Ошибка генерации");
  }
  
  const data = await response.json();
  return data.text;
}

// Воспроизведение TTS
async function playAudio(text) {
  const response = await fetch(
    `http://localhost:8000/tts/synthesize?text=${encodeURIComponent(text)}`
  );
  
  if (!response.ok) throw new Error("Ошибка синтеза");
  const audioBlob = await response.blob();
  const audio = new Audio(URL.createObjectURL(audioBlob));
  
  return new Promise((resolve) => {
    audio.onended = resolve;
    audio.play();
  });
}