import {
  IExtension,
  IExtensionActivationResult,
  ISearchPanelWidgetProps,
} from "superdesk-api";
import { widgetFactory } from "./widget";

const extension: IExtension = {
  activate: () => {
    const result: IExtensionActivationResult = {
      contributions: {
        searchPanelWidgets: [
          widgetFactory() as React.ComponentType<
            ISearchPanelWidgetProps<unknown>
          >,
        ],
      },
    };

    return Promise.resolve(result);
  },
};

export default extension;
