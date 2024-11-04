import {
  IArticle,
  IExtension,
  IExtensionActivationResult,
} from "superdesk-api";
import { WIDGET_ID } from "./constants";
import { superdesk } from "./superdesk";
import { capitalize } from "./utilities";
import { AutoTranslatorWidget } from "./widget";

const extension: IExtension = {
  activate: () => {
    const { gettext } = superdesk.localization;

    const result: IExtensionActivationResult = {
      contributions: {
        authoringSideWidgets: [
          {
            _id: WIDGET_ID,
            label: `${capitalize(gettext("auto"))} ${capitalize(
              gettext("translate")
            )}`,
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
