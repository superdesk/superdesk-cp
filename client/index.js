import {startApp} from 'superdesk-core/scripts/index';
import planningExtension from 'superdesk-planning/client/planning-extension/dist/extension';
import orangelogicExtension from './extensions/orangelogic-extension/dist/extension';
import uploadIptc from './extensions/upload-iptc';

setTimeout(() => {
    startApp(
        [
            planningExtension,
            orangelogicExtension,
            uploadIptc,
        ],
        {},
    );
});

export default angular.module('main.superdesk', []);
