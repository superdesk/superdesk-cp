import diff_match_patch, {
  DIFF_DELETE,
  DIFF_EQUAL,
  DIFF_INSERT,
} from "diff-match-patch";
import DOMPurify from "dompurify";
import { superdesk } from "../../../superdesk";

export const sanitizeHtml = (html: string | Node) => DOMPurify.sanitize(html);

export const getPrettyDiffHtml = (diffs: diff_match_patch.Diff[]) => {
  const { gettext } = superdesk.localization;

  let html = [];
  const patternPara = /\n/g;
  const tempDiv = document.createElement("div");

  const getFormattedElements = (text: string, type: "ins" | "del") => {
    let elements = "";
    const fragment = document.createRange().createContextualFragment(text);

    fragment.childNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        const element = node as Element;
        const tag = element.nodeName.toLowerCase();

        if (element.innerHTML)
          elements += `<${tag}>${
            type === "ins"
              ? `<ins style="background:#e6ffe6;" aria-label=${gettext(
                  "Inserted"
                )}>${element.innerHTML}</ins>`
              : `<del style="background:#ffe6e6;" aria-label=${gettext(
                  "Deleted"
                )}>${element.innerHTML}</del>`
          }</${tag}>`;
      } else if (node.nodeType === Node.TEXT_NODE) {
        const element = node as Text;

        if (element.textContent)
          elements +=
            type === "ins"
              ? `<ins style="background:#e6ffe6;" aria-label=${gettext(
                  "Inserted"
                )}>${element.textContent}</ins>`
              : `<del style="background:#ffe6e6;" aria-label=${gettext(
                  "Deleted"
                )}>${element.textContent}</del>`;
      }
    });

    return elements;
  };

  for (let x = 0; x < diffs.length; x++) {
    let op = diffs[x][0];
    let data = diffs[x][1];
    const text = data.replace(patternPara, "");
    tempDiv.innerHTML = text;

    switch (op) {
      case DIFF_INSERT:
        html[x] = tempDiv.hasChildNodes()
          ? getFormattedElements(text, "ins")
          : `<ins style="background:#e6ffe6;">${text}</ins>`;
        break;
      case DIFF_DELETE:
        html[x] = tempDiv.hasChildNodes()
          ? getFormattedElements(text, "del")
          : `<del style="background:#ffe6e6;">${text}</del>`;
        break;
      case DIFF_EQUAL:
        html[x] = text;
        break;
    }
  }

  return html.join("");
};
