// extending superdesk-api

declare module 'superdesk-api' {
    interface ISuperdeskGlobalConfig {
        semaphoreFields: {
            entities: {
                [key: string]: {
                    name: string;
                    order: number;
                };
            },
            others: {
                [key: string]: {
                    name: string;
                    order: number;
                };
            }
        };
    }

    interface ISubject {
        creator: string;
        relevance: number;
    }
}
