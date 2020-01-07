import {startApp} from 'superdesk-core/scripts/index';
import orangelogicExtension from './extensions/orangelogic-extension/dist/extension';

setTimeout(() => {
    startApp(
        [orangelogicExtension],
        {},
    );
});

export default angular.module('main.superdesk', []);
