import { IArticle, IRelatedArticle } from "superdesk-api";

export const WIDGET_ID = "auto-translator-widget" as const;

export const TRANSLATION_TYPES = {
  basic: "Google Basic",
  advanced_nmt: "Google NMT",
  advanced_llm: "Google LLM",
  deepl: "DeepL",
} as const;

export const TRANSLATION_LANGUAGES = {
  en: "English",
  fr: "French",
};

export const isArticle = (
  article: IArticle | IRelatedArticle
  // @ts-ignore superdesk type can't be narrowed from IRelatedArticle
): article is IArticle => Boolean(article?.guid);

export const isNotEmptyObject = (value: any): value is Record<string, any> =>
  typeof value === "object" && value !== null && Object.keys(value).length > 0;

export const getObjectKeys = <T extends object>(obj: T): (keyof T)[] => {
  return Object.keys(obj) as (keyof T)[];
};

export const getObjectValues = <T extends object>(obj: T): T[keyof T][] => {
  return Object.values(obj) as T[keyof T][];
};

export const getObjectEntries = <T extends object>(
  obj: T
): [keyof T, T[keyof T]][] => {
  return Object.entries(obj) as [keyof T, T[keyof T]][];
};
