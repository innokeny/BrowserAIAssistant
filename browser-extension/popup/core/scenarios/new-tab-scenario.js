import { BaseScenario } from './base-scenario.js';

export class NewTabScenario extends BaseScenario {
    static name = "Новая вкладка";
    
    static match(text) {
        return /(создай|открой)\s*(новую)?\s*вкладку/i.test(text);
    }

    static async execute() {
        try {
            const [currentTab] = await chrome.tabs.query({active: true, currentWindow: true});
            
            // Создаем новую вкладку в фоне
            const newTab = await chrome.tabs.create({
                url: "chrome://newtab",  
                active: false
            });

            // Возвращаем фокус на исходную вкладку
            await chrome.tabs.update(currentTab.id, {active: true});
            
            return {
                success: true,
                data: {
                    newTabId: newTab.id,
                    currentTabId: currentTab.id
                }
            };
        } catch (error) {
            console.error('New tab error:', error);
            return {
                success: false,
                error: 'Не удалось создать вкладку'
            };
        }
    }
}