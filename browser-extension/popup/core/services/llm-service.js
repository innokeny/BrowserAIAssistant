export class LLMService {
    static async generate(prompt) {
        try {
            const result = await chrome.storage.local.get('authToken');
            const authToken = result.authToken;

            console.log('Current auth token:', authToken);
            
            if (!authToken) {
                throw new Error('Необходима авторизация');
            }
            
            const response = await fetch('http://localhost:8000/api/qwen/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    prompt: prompt.slice(0, 1000),
                    temperature: 0.7,
                    max_tokens: 256
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