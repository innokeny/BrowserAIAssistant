import { ScrollScenario } from './scenarios/scroll.js';
import { LLMChatScenario } from './scenarios/llm-chat.js';
import { SearchScenario } from './scenarios/search.js';
import { NewTabScenario } from './scenarios/new-tab-scenario.js';


const SCENARIOS = [
    ScrollScenario,
    SearchScenario,
    NewTabScenario,
    LLMChatScenario // Всегда последний!
];

export class CommandRouter {
    static async handle(commandText) {
        for (const Scenario of SCENARIOS) {
            if (Scenario.match(commandText)) {
                const result = await Scenario.execute(commandText);
                
                // Получаем и логируем баланс после выполнения сценария
                try {
                    const token = (await chrome.storage.local.get('authToken')).authToken;
                    if (token) {
                        const balanceResponse = await fetch('http://localhost:8000/api/credits/balance', {
                            headers: {
                                'Authorization': `Bearer ${token}`
                            }
                        });
                        
                        if (balanceResponse.ok) {
                            const balanceData = await balanceResponse.json();
                            console.log('Баланс после выполнения сценария:', {
                                scenario: Scenario.name,
                                balance: balanceData.balance
                            });
                        }
                    }
                } catch (error) {
                    console.error('Ошибка при получении баланса:', error);
                }
                
                return {
                    scenario: Scenario.name,
                    result
                };
            }
        }
        throw new Error('Сценарий не найден');
    }
}