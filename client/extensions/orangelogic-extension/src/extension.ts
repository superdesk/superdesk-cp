import {ISuperdesk, IExtension, IExtensionActivationResult} from 'superdesk-api';
import {searchPanelWidgetFactory} from './search-panel-widget';

const extension: IExtension = {
    activate: (superdesk: ISuperdesk) => {
        const result: IExtensionActivationResult = {
            contributions: {
                searchPanelWidgets: [
                    searchPanelWidgetFactory(superdesk.localization.gettext),
                ],
            }
        };

        return Promise.resolve(result);
    },
};

export default extension;
