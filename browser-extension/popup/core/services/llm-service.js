export class LLMService {
    static async generate(prompt) {
        try {
            const response = await fetch('http://localhost:8000/qwen/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt.slice(0, 1000), // Ограничение длины запроса
                    temperature: 0.7,
                    max_length: 256
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const data = await response.json();
            return data.text || 'Не получилось сгенерировать ответ';

        } catch (error) {
            console.error('LLM Request Failed:', error);
            throw new Error('Ошибка связи с ИИ');
        }
    }
}