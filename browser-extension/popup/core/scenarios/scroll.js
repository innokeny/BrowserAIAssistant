import { BaseScenario } from './base-scenario.js';

export class ScrollScenario extends BaseScenario {
    static name = "Прокрутка страницы";

    static match(text) {
        return /прокрути|скролл|проскроль/i.test(text) &&
            /на (\d+%)|на половину| наполовину/i.test(text);
    }

    static async execute(text) {
        try {
            const percent = this.#parsePercent(text);
            const direction = this.#parseDirection(text);

            const [tab] = await new Promise(resolve =>
                chrome.tabs.query({ active: true, currentWindow: true }, resolve)
            );

            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: (p, dir) => {
                    const amount = window.innerHeight * (p / 100);
                    window.scrollBy({
                        top: dir === 'down' ? amount : -amount,
                        left: 0,
                        behavior: 'smooth'
                    });
                },
                args: [percent, direction]
            });

            return { success: true };
        } catch (error) {
            console.error('Scroll error:', error);
            return { success: false, error: error.message };
        }
    }

    static #parsePercent(text) {
        const match = text.match(/(\d+)%|половину/);
        if (match?.[1]) return parseInt(match[1]);
        if (match?.[0] === 'половину') return 50;
        return 20;
    }

    static #parseDirection(text) {
        return text.includes('вверх') ? 'up' : 'down';
    }
}