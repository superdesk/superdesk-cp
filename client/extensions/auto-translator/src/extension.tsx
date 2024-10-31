import {
  IArticle,
  IExtension,
  IExtensionActivationResult,
} from "superdesk-api";
import { WIDGET_ID } from "./utilities";
import { AutoTranslatorWidget } from "./widget";

// TODO: add localization
const extension: IExtension = {
  activate: () => {
    // const { gettext } = superdesk.localization;
    const result: IExtensionActivationResult = {
      contributions: {
        authoringSideWidgets: [
          {
            _id: WIDGET_ID,
            label: "Auto Translate",
            icon: "multiedit",
            order: 1,
            component: AutoTranslatorWidget,
            isAllowed: (item: IArticle) => item.type === "text",
          },
        ],
      },
    };

    return Promise.resolve(result);
  },
};

export default extension;
