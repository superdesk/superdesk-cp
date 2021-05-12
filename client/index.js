import {startApp} from 'superdesk-core/scripts/index';

setTimeout(() => {
    startApp(
        [
            {
                id: 'planning-extension',
                load: () => import('superdesk-planning/client/planning-extension'),
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
                id: 'usage-metrics',
                load: () => import('superdesk-core/scripts/extensions/usageMetrics'),
            },
        ],
        {},
    );
});

export default angular.module('main.superdesk', []);
