import {startApp} from 'superdesk-core/scripts/index';
import orangelogicExtension from 'orangelogic-extension';

setTimeout(() => {
    startApp(
        [orangelogicExtension],
        {},
    );
});

export default angular.module('main.superdesk', []);
