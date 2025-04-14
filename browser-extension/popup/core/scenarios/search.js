import { BaseScenario } from './base-scenario.js';

export class SearchScenario extends BaseScenario {
    static name = "Поиск на странице";

    static match(text) {
        return /найди|найти|ищи|покажи/i.test(text);
    }

    static async execute(text) {
        try {
            const query = this.#sanitizeQuery(text);

            const [tab] = await new Promise(resolve =>
                chrome.tabs.query({ active: true, currentWindow: true }, resolve)
            );

            await chrome.scripting.insertCSS({
                target: { tabId: tab.id },
                files: ['popup/core/scenarios/search-panel.css']
            });

            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: (q) => {
                    // Удаление предыдущих элементов
                    const existingSearch = document.getElementById('voice-search-box');
                    if (existingSearch) existingSearch.remove();

                    // Состояние поиска
                    let matches = [];
                    let currentMatch = -1;
                    let originalTextNodes = new WeakMap();
                    const searchState = {
                        total: 0,
                        current: 0
                    };

                    // Создание элементов интерфейса
                    const searchBox = document.createElement('div');
                    searchBox.id = 'voice-search-box';

                    const prevBtn = document.createElement('button');
                    prevBtn.className = 'nav-btn';
                    prevBtn.textContent = '←';

                    const nextBtn = document.createElement('button');
                    nextBtn.className = 'nav-btn';
                    nextBtn.textContent = '→';

                    const counter = document.createElement('div');
                    counter.className = 'search-counter';

                    const input = document.createElement('input');
                    input.className = 'search-input';

                    const closeBtn = document.createElement('button');
                    closeBtn.className = 'close-btn';
                    closeBtn.textContent = '×';

                    searchBox.append(prevBtn, nextBtn, counter, input, closeBtn);
                    document.body.appendChild(searchBox);

                    // Функции поиска
                    const restoreOriginalContent = () => {
                        document.querySelectorAll('.voice-search-highlight').forEach(el => {
                            const original = originalTextNodes.get(el);
                            if (original) {
                                el.replaceWith(original.cloneNode(true));
                            }
                        });
                        originalTextNodes = new WeakMap();
                    };

                    const highlightMatches = (searchText) => {
                        restoreOriginalContent();
                        matches = [];
                        searchState.total = 0;
                        currentMatch = -1;

                        if (!searchText) {
                            updateCounter();
                            return;
                        }

                        const regex = new RegExp(escapeRegExp(searchText), 'gi');
                        const treeWalker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            {
                                acceptNode: node =>
                                    node.nodeValue.trim() && regex.test(node.nodeValue) ?
                                        NodeFilter.FILTER_ACCEPT :
                                        NodeFilter.FILTER_SKIP
                            }
                        );

                        const textNodes = [];
                        while (treeWalker.nextNode()) textNodes.push(treeWalker.currentNode);

                        textNodes.forEach(node => {
                            const originalNode = node.cloneNode(true);
                            const parent = node.parentNode;

                            if (parent.classList.contains('voice-search-highlight')) {
                                return;
                            }

                            const wrapper = document.createElement('span');
                            wrapper.className = 'voice-search-highlight';
                            wrapper.innerHTML = node.nodeValue.replace(
                                regex,
                                '<mark>$&</mark>'
                            );

                            originalTextNodes.set(wrapper, originalNode);
                            parent.replaceChild(wrapper, node);
                            matches.push(wrapper);
                        });

                        searchState.total = matches.length;
                        currentMatch = matches.length > 0 ? 0 : -1;
                        updateCounter();
                        scrollToCurrentMatch();
                    };

                    const scrollToCurrentMatch = () => {
                        if (currentMatch >= 0 && matches[currentMatch]) {
                            matches[currentMatch].scrollIntoView({
                                behavior: 'smooth',
                                block: 'center'
                            });
                        }
                    };

                    const updateCounter = () => {
                        counter.textContent = searchState.total > 0
                            ? `${currentMatch + 1}/${searchState.total}`
                            : '0/0';
                        prevBtn.disabled = currentMatch <= 0;
                        nextBtn.disabled = currentMatch >= matches.length - 1;
                    };

                    function escapeRegExp(string) {
                        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    }

                    // Обработчики событий
                    prevBtn.addEventListener('click', () => {
                        if (currentMatch > 0) {
                            currentMatch--;
                            searchState.current = currentMatch;
                            updateCounter();
                            scrollToCurrentMatch();
                        }
                    });

                    nextBtn.addEventListener('click', () => {
                        if (currentMatch < matches.length - 1) {
                            currentMatch++;
                            searchState.current = currentMatch;
                            updateCounter();
                            scrollToCurrentMatch();
                        }
                    });

                    input.addEventListener('input', (e) => {
                        highlightMatches(e.target.value.trim());
                    });

                    closeBtn.addEventListener('click', () => {
                        restoreOriginalContent();
                        searchBox.remove();
                    });

                    // Инициализация
                    input.value = q;
                    input.focus();
                    input.select();
                    highlightMatches(q);
                },
                args: [query]
            });

            return { success: true };
        } catch (error) {
            console.error('Search error:', error);
            return { success: false, error: error.message };
        }
    }

    static #sanitizeQuery(text) {
        return text
            .replace(/[^\wа-яё\s-]/gi, '')
            .replace(/найди|найти|ищи|покажи/gi, '')
            .trim()
            .slice(0, 100);
    }
}