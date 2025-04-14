import { STTService } from './core/services/stt-service.js';
import { TTSService } from './core/services/tts-service.js';
import { CommandRouter } from './core/command-router.js';
import { AudioRecorder } from './core/services/recorder.js';

// Инициализация после полной загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
  const recorder = new AudioRecorder();
  const startBtn = document.getElementById('startBtn');

  startBtn.addEventListener('click', async () => {
    try {
      const audioBlob = await recorder.toggleRecording();
      if (!audioBlob) return;

      const commandText = await STTService.transcribe(audioBlob);
      const { scenario, data } = await CommandRouter.handle(commandText);
      if (scenario !== "Общение с ИИ") {
          await TTSService.speak(`Выполняю: ${scenario}`);
      }

    } catch (err) {
      console.error('Error:', err);
      TTSService.speak(`Ошибка: ${err.message}`);
    }
  });
});