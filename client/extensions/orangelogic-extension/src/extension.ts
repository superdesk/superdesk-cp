import {ISuperdesk, IExtension, IExtensionActivationResult, ISearchPanelWidgetProps} from 'superdesk-api';
import {searchPanelWidgetFactory} from './search-panel-widget';

const extension: IExtension = {
    activate: (superdesk: ISuperdesk) => {
        const result: IExtensionActivationResult = {
            contributions: {
                searchPanelWidgets: [
                    // casting is required because of limitations on use of generics in superdesk-api
                    searchPanelWidgetFactory(superdesk.localization.gettext) as React.ComponentType<ISearchPanelWidgetProps<unknown>>,
                ],
            }
        };

        return Promise.resolve(result);
    },
};

export default extension;
