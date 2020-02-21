import {startApp} from 'superdesk-core/scripts/index';
import planningExtension from 'superdesk-planning-extension';
import orangelogicExtension from './extensions/orangelogic-extension/dist/extension';

setTimeout(() => {
    startApp(
        [
            planningExtension,
            orangelogicExtension,
        ],
        {},
    );
});

export default angular.module('main.superdesk', []);
