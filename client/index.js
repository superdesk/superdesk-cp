import {startApp} from 'superdesk-core/scripts/index';
import planningExtension from 'superdesk-planning/client/planning-extension/dist/extension';
import orangelogicExtension from './extensions/orangelogic-extension/dist/extension';
import uploadIptcExtension from './extensions/upload-iptc';

setTimeout(() => {
    startApp(
        [
            planningExtension,
            orangelogicExtension,
            uploadIptcExtension,
        ],
        {},
    );
});

export default angular.module('main.superdesk', []);
