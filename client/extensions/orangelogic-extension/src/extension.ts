import {ISuperdesk, IExtension} from 'superdesk-api';
import {searchPanelWidgetFactory} from './search-panel-widget';

const extension: IExtension = {
    id: 'orange-logic',
    activate: (superdesk: ISuperdesk) => {
        return Promise.resolve({
            contributions: {
                searchPanelWidgets: [
                    searchPanelWidgetFactory(superdesk.localization.gettext),
                ],
            }
        });
    },
};

export default extension;
