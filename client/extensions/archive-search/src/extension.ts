import {
  IExtension,
  IExtensionActivationResult,
  ISearchPanelWidgetProps,
} from "superdesk-api";
import { SearchPanelWidget } from "./widget";

const extension: IExtension = {
  activate: () => {
    const result: IExtensionActivationResult = {
      contributions: {
        searchPanelWidgets: [
          SearchPanelWidget as React.ComponentType<
            ISearchPanelWidgetProps<unknown>
          >,
        ],
      },
    };

    return Promise.resolve(result);
  },
};

export default extension;
