import {
  IArticle,
  IExtension,
  IExtensionActivationResult,
} from "superdesk-api";
import { WIDGET_ID } from "./constants";
import { getAutoTranslatorWidget } from "./widget";

const extension: IExtension = {
  activate: (superdesk) => {
    const { gettext } = superdesk.localization;

    const result: IExtensionActivationResult = {
      contributions: {
        authoringSideWidgets: [
          {
            _id: WIDGET_ID,
            label: gettext("Auto Translate"),
            icon: "multiedit",
            order: 1,
            component: getAutoTranslatorWidget(),
            isAllowed: (item: IArticle) => item.type === "text",
          },
        ],
      },
    };

    return Promise.resolve(result);
  },
};

export default extension;
