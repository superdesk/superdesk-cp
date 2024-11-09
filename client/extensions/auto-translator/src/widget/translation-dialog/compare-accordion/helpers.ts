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

  for (var x = 0; x < diffs.length; x++) {
    let op = diffs[x][0];
    let data = diffs[x][1];
    let text = data;
    switch (op) {
      case DIFF_INSERT:
        html[x] = '<ins style="background:#e6ffe6;">' + text + "</ins>";
        break;
      case DIFF_DELETE:
        html[x] = '<del style="background:#ffe6e6;">' + text + "</del>";
        break;
      case DIFF_EQUAL:
        html[x] = text;
        break;
    }
  }

  return html.join("");
};
