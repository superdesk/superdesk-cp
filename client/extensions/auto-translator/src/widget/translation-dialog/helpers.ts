import { IArticle } from "superdesk-api";
import {
  TRANSLATION_LANGUAGES_CODES_MAP,
  TRANSLATION_VERSIONS,
} from "../../constants";
import { RecursiveKeyOf } from "../../formik-utilties";
import { superdesk } from "../../superdesk";
import {
  TranslationFields,
  TranslationImageField,
  TranslationType,
} from "../../typings/translation";
import { getObjectEntries } from "../../utilities";

export const FORM_FIELDS: Record<
  TranslationFields,
  {
    type: string;
    getName: (
      writethru: string,
      version: string
    ) => RecursiveKeyOf<TranslationDialogFormProps>;
    label: string;
    getFormValue: (article: IArticle) => string;
    setEditorValue: (
      values: TranslationDialogFormProps,
      props?: { currentArticle: IArticle }
    ) => {
      key: string;
      value: any;
    };
    initialValue: any;
  }
> = {
  headline: {
    type: "text",
    getName: (writethru, version) =>
      `translations.${writethru}.${version}.headline`,
    label: superdesk.localization.gettext("Headline"),
    getFormValue: (article) => article.headline ?? "",
    setEditorValue: (values) => ({
      key: "headline",
      value: values.translations[values.writethru].manualTranslation.headline,
    }),
    initialValue: "",
  },
  headline_extended: {
    type: "text",
    getName: (writethru, version) =>
      `translations.${writethru}.${version}.headline_extended`,
    label: superdesk.localization.gettext("Extended Headline"),
    getFormValue: (article) => article?.extra?.headline_extended ?? "",
    setEditorValue: (values, props) => ({
      key: "extra",
      value: {
        ...props?.currentArticle?.extra,
        headline_extended:
          values.translations[values.writethru].manualTranslation
            .headline_extended,
      },
    }),
    initialValue: "",
  },
  body_html: {
    type: "textEditor",
    getName: (writethru, version) =>
      `translations.${writethru}.${version}.body_html`,
    label: superdesk.localization.gettext("body HTML"),
    getFormValue: (article) => article.body_html ?? "",
    setEditorValue: (values) => ({
      key: "body_html",
      value: values.translations[values.writethru].manualTranslation.body_html,
    }),
    initialValue: "",
  },
};

export const FORM_FIELDS_INITIAL_VALUES = getObjectEntries(FORM_FIELDS).reduce(
  (initialValues, [key, value]) => {
    Object.assign(initialValues, { [key]: value.initialValue });
    return initialValues;
  },
  {} as Omit<FormInputProps, "images">
);

export type FormInputProps = Record<TranslationFields, string> & {
  images: Record<TranslationImageField, { description: string; href: string }>;
};

export type TranslationEntry = Record<
  keyof typeof TRANSLATION_VERSIONS,
  FormInputProps
>;

export type TranslationDialogFormProps = {
  writethru: string;
  translationType: TranslationType;
  translateFrom: (typeof TRANSLATION_LANGUAGES_CODES_MAP)[keyof typeof TRANSLATION_LANGUAGES_CODES_MAP];
  translateTo: (typeof TRANSLATION_LANGUAGES_CODES_MAP)[keyof typeof TRANSLATION_LANGUAGES_CODES_MAP];
  translations: Record<string, TranslationEntry>;
};

export const isTranslationVersion = (
  value: string
): value is keyof TranslationEntry =>
  Object.keys(TRANSLATION_VERSIONS).includes(value);

export const isLanguageCode = (
  value: string
): value is keyof typeof TRANSLATION_LANGUAGES_CODES_MAP =>
  value in TRANSLATION_LANGUAGES_CODES_MAP;
