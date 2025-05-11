export class BaseScenario {
    static get name() {
        throw new Error('Not implemented');
    }

    static match(commandText) {
        throw new Error('Not implemented');
    }

    static execute(commandText) {
        throw new Error('Not implemented');
    }
}