export class CreditService {
    static async deductCredits(scenarioType) {
        try {
            const result = await chrome.storage.local.get('authToken');
            const token = result.authToken;
            
            if (!token) {
                throw new Error('Необходима авторизация');
            }

            // Определяем количество кредитов для каждого сценария
            const creditCosts = {
                'search': 5,
                'scroll': 5,
                'llm-chat': 10
            };

            const amount = creditCosts[scenarioType] || 1;
            
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

            if (response.status === 401) {
                await chrome.storage.local.remove('authToken');
                document.getElementById('auth-forms').style.display = 'block';
                document.getElementById('main-interface').style.display = 'none';
                throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка списания кредитов');
            }

            const transactionResult = await response.json();
            return transactionResult.balance;

        } catch (error) {
            console.error('Credit deduction failed:', error);
            throw error;
        }
    }
} 