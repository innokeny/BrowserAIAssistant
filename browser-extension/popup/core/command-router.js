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
                return {
                    scenario: Scenario.name,
                    result: await Scenario.execute(commandText)
                };
            }
        }
        throw new Error('Сценарий не найден');
    }
}