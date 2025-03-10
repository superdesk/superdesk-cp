import { startApp } from 'superdesk-core/scripts/index';

setTimeout(() => {
    startApp(
        [
            {
                id: 'planning-extension',
                load: () => import('superdesk-planning/client/planning-extension'),
                configuration: {
                    assignmentsTopBarWidget: true,
                },
            },
            {
                id: 'orangelogic-extension',
                load: () => import('./extensions/orangelogic-extension'),
            },
            {
                id: 'upload-iptc',
                load: () => import('./extensions/upload-iptc'),
            },
            {
                id: 'auto-tagger',
                load: () => import('./extensions/auto-tagger'),
            },
            {
                id: 'usage-metrics',
                load: () => import('superdesk-core/scripts/extensions/usageMetrics'),
            },
            {
                id: 'auto-translator',
                load: () => import('./extensions/auto-translator')
            },
        ],
        {},
    );
});

export default angular.module('main.superdesk', []);
