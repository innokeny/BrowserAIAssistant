export class CreditService {
    static async deductCredits(scenarioType) {
        try {
            // Получаем токен авторизации из локального хранилища
            const result = await chrome.storage.local.get('authToken');
            const token = result.authToken;
            
            if (!token) {
                throw new Error('Необходима авторизация');
            }

            // Стоимость кредитов для каждого типа сценария
            const creditCosts = {
                'search': 5,    // Поиск стоит 5 кредитов
                'scroll': 5,    // Прокрутка стоит 5 кредитов
                'llm-chat': 10  // Чат с LLM стоит 10 кредитов
            };

            // Получаем стоимость для текущего сценария или используем значение по умолчанию (1)
            const amount = creditCosts[scenarioType] || 1;
            
            // Отправляем запрос на списание кредитов
            const response = await fetch('http://localhost:8000/api/credits/deduct', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    amount: amount,
                    transaction_type: 'scenario_usage',
                    description: `Использование сценария ${scenarioType} (${amount} кредитов)`
                })
            });

            // Проверяем авторизацию
            if (response.status === 401) {
                await chrome.storage.local.remove('authToken');
                document.getElementById('auth-forms').style.display = 'block';
                document.getElementById('main-interface').style.display = 'none';
                throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
            }

            // Проверяем успешность запроса
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка списания кредитов');
            }

            // Получаем результат транзакции и возвращаем новый баланс
            const transactionResult = await response.json();
            return transactionResult.balance;

        } catch (error) {
            console.error('Credit deduction failed:', error);
            throw error;
        }
    }
} 