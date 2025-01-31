import { IArticle, IRelatedArticle } from "superdesk-api";

const isArticle = (
  article: IArticle | IRelatedArticle
  // @ts-ignore superdesk type can't be narrowed from IRelatedArticle
): article is IArticle => Boolean(article?.guid);

const isNotEmptyObject = (value: any): value is Record<string, any> =>
  typeof value === "object" && value !== null && Object.keys(value).length > 0;

const getObjectKeys = <T extends object>(obj: T): (keyof T)[] => {
  return Object.keys(obj) as (keyof T)[];
};

const getObjectValues = <T extends object>(obj: T): T[keyof T][] => {
  return Object.values(obj) as T[keyof T][];
};

const getObjectEntries = <T extends object>(
  obj: T
): [keyof T, T[keyof T]][] => {
  return Object.entries(obj) as [keyof T, T[keyof T]][];
};

const capitalize = (str: string) => {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export {
  isArticle,
  isNotEmptyObject,
  getObjectKeys,
  getObjectValues,
  getObjectEntries,
  capitalize,
};
