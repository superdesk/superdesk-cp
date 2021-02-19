import {startApp} from 'superdesk-core/scripts/index';

setTimeout(() => {
    startApp(
        [
            {
                id: 'planning-extension',
                load: () => import('superdesk-planning/client/planning-extension/dist/extension').then((res) => res.default),
            },
            {
                id: 'orangelogic-extension',
                load: () => import('./extensions/orangelogic-extension/dist/extension').then((res) => res.default),
            },
            {
                id: 'upload-iptc',
                load: () => import('./extensions/upload-iptc').then((res) => res.default),
            },
        ],
        {},
    );
});

export default angular.module('main.superdesk', []);
