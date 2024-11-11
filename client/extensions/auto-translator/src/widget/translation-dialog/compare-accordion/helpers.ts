import diff_match_patch, {
  DIFF_DELETE,
  DIFF_EQUAL,
  DIFF_INSERT,
} from "diff-match-patch";
import DOMPurify from "dompurify";

export const sanitizeHtml = (html: string | Node) => {
  const clean = DOMPurify.sanitize(html);

  return clean;
};

export const getPrettyDiffHtml = (diffs: diff_match_patch.Diff[]) => {
  let html = [];
  const pattern_para = /\n/g;
  const tempDiv = document.createElement("div");

  const getFormattedElements = (text: string, type: "ins" | "del") => {
    let elements = "";
    const fragment = document.createRange().createContextualFragment(text);

    fragment.childNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        const element = node as Element;
        const tag = element.nodeName.toLowerCase();
        console.log({ innerHTML: element.innerHTML });
        if (element.innerHTML)
          elements += `<${tag}>${
            type === "ins"
              ? `<ins style="background:#e6ffe6;">${element.innerHTML}</ins>`
              : `<del style="background:#ffe6e6;">${element.innerHTML}</del>`
          }</${tag}>`;
      } else if (node.nodeType === Node.TEXT_NODE) {
        const element = node as Text;
        console.log({ text: element.textContent });
        if (element.textContent)
          elements +=
            type === "ins"
              ? `<ins style="background:#e6ffe6;">${element.textContent}</ins>`
              : `<del style="background:#ffe6e6;">${element.textContent}</del>`;
      }
    });

    return elements;
  };

  for (let x = 0; x < diffs.length; x++) {
    let op = diffs[x][0];
    let data = diffs[x][1];
    let text = data.replace(pattern_para, "");
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
