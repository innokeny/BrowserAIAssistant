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
                const startTime = performance.now();
                let result;
                let status = "success";
                let errorMessage = null;

                try {
                    result = await Scenario.execute(commandText);
                    console.log("Scenario result:", result);
                } catch (error) {
                    status = "error";
                    errorMessage = error.message;
                    throw error;
                } finally {
                    const endTime = performance.now();
                    const processingTime = Math.round(endTime - startTime);

                    // Log scenario usage in request history
                    try {
                        const token = (await chrome.storage.local.get('authToken')).authToken;
                        if (token) {
                            let qwenData = null;
                            if (Scenario.name === "Общение с ИИ" && result) {
                                qwenData = {
                                    prompt: result.input,
                                    response: result.output,
                                    tokens_used: 0  // TODO: Add token counting
                                };
                            }
                            console.log("Qwen data:", qwenData);

                            await fetch('http://localhost:8000/api/analytics/history', {
                                method: 'POST',
                                headers: {
                                    'Authorization': `Bearer ${token}`,
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    request_data: {
                                        request_type: Scenario.name,
                                        request_data: commandText,
                                        status: status,
                                        error_message: errorMessage,
                                        processing_time: processingTime
                                    },
                                    qwen_data: qwenData
                                })
                            });
                        }
                    } catch (error) {
                        console.error('Ошибка при логировании сценария:', error);
                    }
                }
                
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