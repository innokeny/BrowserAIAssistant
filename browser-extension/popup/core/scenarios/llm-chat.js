import { BaseScenario } from './base-scenario.js';
import { TTSService } from '../services/tts-service.js';
import { LLMService } from '../services/llm-service.js'; // Выносим сервис в отдельный файл

export class LLMChatScenario extends BaseScenario {
    static name = "Общение с ИИ";

    static match(text) {
        const isOtherCommand = [
            /прокрути|скролл/i,
            /найди|поиск/i,
            /сохрани|закрой/i
        ].some(re => re.test(text));

        return !isOtherCommand;
    }

    static async execute(commandText) {
        try {
            const responseText = await LLMService.generate(commandText);

            // Очистка текста перед отправкой в TTS
            const cleanText = this.#sanitizeText(responseText);

            await TTSService.speak(cleanText);

            return {
                type: 'llm',
                input: commandText,
                output: cleanText
            };

        } catch (err) {
            console.error('LLM Error:', err);
            await TTSService.speak('Не удалось обработать запрос');
            return {
                type: 'llm',
                input: commandText,
                error: err.message
            };
        }
    }

    static #sanitizeText(text) {
        return text
            .replace(/[^\wа-яё\s,.!?-]/gi, '') // Удаляем спецсимволы
            .replace(/\s+/g, ' ') // Убираем множественные пробелы
            .slice(0, 500); // Ограничение длины
    }
}