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