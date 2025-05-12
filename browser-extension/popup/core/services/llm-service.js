export class LLMService {
    static async generate(prompt) {
        try {
            const result = await chrome.storage.local.get(['authToken', 'userRole']);
            const authToken = result.authToken;
            const userRole = result.userRole;
            
            if (!authToken) {
                throw new Error('Необходима авторизация');
            }

            // Проверяем только наличие роли, так как оба типа пользователей имеют доступ
            if (!userRole) {
                throw new Error('Ошибка авторизации: роль пользователя не определена');
            }
            
            const response = await fetch('http://localhost:8000/api/qwen/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                    'X-User-Role': userRole
                },
                body: JSON.stringify({
                    prompt: prompt.slice(0, 1000),
                    temperature: 0.7,
                    max_tokens: 256
                })
            });

            if (response.status === 401) {
                // Если токен истек, очищаем его и показываем форму входа
                await chrome.storage.local.remove('authToken');
                await chrome.storage.local.remove('userRole');
                document.getElementById('auth-forms').style.display = 'block';
                document.getElementById('main-interface').style.display = 'none';
                throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
            }

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const data = await response.json();
            return data.text || 'Не получилось сгенерировать ответ';

        } catch (error) {
            console.error('LLM Request Failed:', error);
            throw error;
        }
    }
}