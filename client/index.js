import {startApp} from 'superdesk-core/scripts/index';
import planningExtension from 'superdesk-planning/client/planning-extension/dist/extension';
import orangelogicExtension from './extensions/orangelogic-extension/dist/extension';
import uploadIptc from './extensions/upload-iptc';
import markForUserExtension from 'superdesk-core/scripts/extensions/markForUser';

setTimeout(() => {
    startApp(
        [
            planningExtension,
            orangelogicExtension,
            uploadIptc,
            markForUserExtension,
        ],
        {},
    );
});

export default angular.module('main.superdesk', []);
