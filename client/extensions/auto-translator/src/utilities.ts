import { IArticle, IRelatedArticle } from "superdesk-api";

const isArticle = (
  article: IArticle | IRelatedArticle
  // @ts-ignore superdesk type can't be narrowed from IRelatedArticle
): article is IArticle => Boolean(article?.guid);

const isNotEmptyObject = (value: any): value is Record<string, any> =>
  typeof value === "object" && value !== null && Object.keys(value).length > 0;

const getObjectKeys = <T extends object>(obj: T): (keyof T)[] =>
  Object.keys(obj) as (keyof T)[];

const getObjectValues = <T extends object>(obj: T): T[keyof T][] =>
  Object.values(obj) as T[keyof T][];

const getObjectEntries = <T extends object>(obj: T): [keyof T, T[keyof T]][] =>
  Object.entries(obj) as [keyof T, T[keyof T]][];

const stripLinkTags = (html: string) => {
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");
  const links = doc.querySelectorAll("a");

  links.forEach((link) => {
    if (link.textContent) {
      const textNode = document.createTextNode(link.textContent);
      const parentNode = link.parentNode;
      if (parentNode) {
        parentNode.replaceChild(textNode, link);
      }
    }
  });

  return doc.body.innerHTML;
};

export {
  getObjectEntries,
  getObjectKeys,
  getObjectValues,
  isArticle,
  isNotEmptyObject,
  stripLinkTags,
};
