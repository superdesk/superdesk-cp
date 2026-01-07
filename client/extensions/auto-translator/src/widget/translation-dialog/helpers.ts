import { FormikConfig, FormikContextType, FormikErrors } from "formik";
import { IArticle, ISuperdesk } from "superdesk-api";
import {
  TRANSLATION_LANGUAGES_CODES_MAP,
  TRANSLATION_VERSIONS,
} from "../../constants";
import { RecursiveKeyOf } from "../../formik-utilties";
import {
  TranslationFields,
  TranslationImageField,
  TranslationType,
} from "../../typings/translation";
import { ValueOf } from "../../typings/utilities";
import {
  getObjectEntries,
  getObjectKeys,
  isArticle,
  isNotEmptyObject,
  stripLinkTags,
} from "../../utilities";
import { superdesk } from "../../superdesk";

const { gettext } = superdesk.localization;
const { GenericFormFieldType } = superdesk.forms;

type FormInputProps = Record<TranslationFields, string> & {
  images: Record<TranslationImageField, { description: string; href: string }>;
};

type TranslationEntry = Record<
  keyof typeof TRANSLATION_VERSIONS,
  FormInputProps
>;

type TranslationForm = {
  writethru: string;
  translationType: TranslationType;
  translateFrom: ValueOf<typeof TRANSLATION_LANGUAGES_CODES_MAP>;
  translateTo: ValueOf<typeof TRANSLATION_LANGUAGES_CODES_MAP>;
  translations: Record<string, TranslationEntry & { label: string }>;
  glossary?: string;
  style?: string;
};

type TranslationFormStatus = {
  isLoading: boolean;
  isPristine: boolean;
};

type ExtraTranslationForm = {
  status?: TranslationFormStatus;
  initialStatus?: TranslationFormStatus;
};

const FORM_FIELDS: Record<
  TranslationFields,
  {
    type: ValueOf<ISuperdesk["forms"]["GenericFormFieldType"]>;
    getName: (
      writethru: string,
      version: string
    ) => RecursiveKeyOf<TranslationForm>;
    label: string;
    getFormValue: (article: IArticle) => string;
    setEditorValue: (
      values: TranslationForm,
      props?: { article: IArticle }
    ) => {
      key: string;
      value: any;
    };
    initialValue: any;
    validate?: (
      value: string,
      { schema }: { schema: { maxlength: number } }
    ) => string | undefined;
    setFormValue?: (value: string) => string;
    mapApiValue?: (value: string) => string;
  }
> = {
  headline: {
    type: GenericFormFieldType.plainText,
    getName: (writethru, version) =>
      `translations.${writethru}.${version}.headline`,
    label: gettext("Headline"),
    getFormValue: (article) => article.headline ?? "",
    setEditorValue: (values) => ({
      key: "headline",
      value: values.translations[values.writethru].manualTranslation.headline,
    }),
    initialValue: "",
    validate: (value, { schema }) => {
      if (value.length > schema.maxlength)
        return gettext(
          "Headline may have a maximum character length of {{length}}",
          { length: schema.maxlength }
        );
      return;
    },
  },
  headline_extended: {
    type: GenericFormFieldType.plainText,
    getName: (writethru, version) =>
      `translations.${writethru}.${version}.headline_extended`,
    label: gettext("Extended Headline"),
    getFormValue: (article) => article?.extra?.headline_extended ?? "",
    setEditorValue: (values, props) => ({
      key: "extra",
      value: {
        ...props?.article?.extra,
        headline_extended:
          values.translations[values.writethru].manualTranslation
            .headline_extended,
      },
    }),
    initialValue: "",
    validate: (value, { schema }) => {
      if (value.length > schema.maxlength)
        return gettext(
          "Extended Headline may have a maximum character length of {{length}}",
          { length: schema.maxlength }
        );
      return;
    },
  },
  body_html: {
    type: GenericFormFieldType.textEditor3,
    getName: (writethru, version) =>
      `translations.${writethru}.${version}.body_html`,
    label: gettext("body HTML"),
    getFormValue: (article) => article.body_html ?? "",
    setEditorValue: (values) => ({
      key: "body_html",
      value: values.translations[values.writethru].manualTranslation.body_html,
    }),
    initialValue: "",
    setFormValue: (value) => stripLinkTags(value),
    mapApiValue: (value) => stripLinkTags(value),
  },
};

const FORM_FIELDS_INITIAL_VALUES = getObjectEntries(FORM_FIELDS).reduce(
  (initialValues, [key, value]) => {
    Object.assign(initialValues, { [key]: value.initialValue });
    return initialValues;
  },
  {} as Omit<FormInputProps, "images">
);

const isTranslationVersion = (value: string): value is keyof TranslationEntry =>
  Object.keys(TRANSLATION_VERSIONS).includes(value);

const isLanguageCode = (
  value: string
): value is keyof typeof TRANSLATION_LANGUAGES_CODES_MAP =>
  value in TRANSLATION_LANGUAGES_CODES_MAP;

type formatWritethruLabelProps = Partial<IArticle> & {
  isCurrentStory?: boolean;
};

const formatWritethruLabel = ({
  isCurrentStory,
  anpa_take_key,
  correction_sequence,
  language,
}: formatWritethruLabelProps) => {
  let label = "";
  if (
    anpa_take_key !== null &&
    typeof anpa_take_key === "string" &&
    anpa_take_key.length > 0
  )
    label += isCurrentStory ? `(${anpa_take_key})` : anpa_take_key;
  if (typeof correction_sequence === "number" && !isNaN(correction_sequence))
    label += ` #${correction_sequence} (${gettext("Corrected")})`;
  if (language !== null && typeof language === "string" && language.length > 0)
    label += ` (${language})`;
  return label;
};

type isManualTranslationDirtyProps = Pick<
  FormikContextType<TranslationForm>,
  "values" | "getFieldMeta"
>;

const isManualTranslationDirty = ({
  values,
  getFieldMeta,
}: isManualTranslationDirtyProps) => {
  const { getContentStateFromHtml } = superdesk.helpers;

  return getObjectEntries(FORM_FIELDS).some(([key, value]) => {
    const field = getFieldMeta<string>(
      `translations.${values.writethru}.manualTranslation.${key}`
    );
    if (value.type === GenericFormFieldType.textEditor3) {
      const contentState = getContentStateFromHtml(field.value);
      const text = contentState.getPlainText();
      const initialContentState = getContentStateFromHtml(
        field.initialValue ?? ""
      );
      const initialText = initialContentState.getPlainText();

      return initialText !== text;
    }
    return field.initialValue !== field.value;
  });
};

const getWritethrus = (article: IArticle) => {
  const { prepareSuperdeskQuery } = superdesk.helpers;
  const { httpRequestJsonLocal } = superdesk;

  const query = prepareSuperdeskQuery("/search", {
    filter: { family_id: { $eq: article.family_id } },
    sort: [{ versioncreated: "asc" }],
    page: 1,
    max_results: 50,
  });

  return httpRequestJsonLocal<{ _items: IArticle[] }>(query);
};

const getImagesFormValues = (article: IArticle) =>
  getObjectEntries(article?.associations || {}).reduce<
    Record<keyof TranslationEntry, FormInputProps["images"]>
  >(
    (images, [key, article]) => {
      if (!isArticle(article)) return images;

      const description = article?.description_text;
      const thumbnailHref = article?.renditions?.thumbnail?.href;

      if (!thumbnailHref) return images;

      for (const version of getObjectKeys(TRANSLATION_VERSIONS)) {
        Object.assign(images[version], {
          [key]: { description: description ?? "", href: thumbnailHref },
        });
      }

      return images;
    },
    { original: {}, aiTranslation: {}, manualTranslation: {} }
  );

const getTranslationEntryFormValues = ({
  article,
  images,
}: {
  article: IArticle;
  images: ReturnType<typeof getImagesFormValues>;
}) =>
  getObjectKeys(TRANSLATION_VERSIONS).reduce<
    TranslationForm["translations"][string]
  >(
    (formValues, version) => {
      if (version === TRANSLATION_VERSIONS.original.value) {
        formValues[version] = {
          ...getObjectEntries(FORM_FIELDS).reduce<
            Omit<FormInputProps, "images">
          >(
            (formValues, [key, value]) => {
              formValues[key] = value.getFormValue(article);
              return formValues;
            },
            { ...FORM_FIELDS_INITIAL_VALUES }
          ),
          images: {},
        };
      }
      formValues[version]["images"] = isNotEmptyObject(images[version])
        ? images[version]
        : {};

      return formValues;
    },
    {
      original: {
        ...FORM_FIELDS_INITIAL_VALUES,
        images: {},
      },
      aiTranslation: {
        ...FORM_FIELDS_INITIAL_VALUES,
        images: {},
      },
      manualTranslation: {
        ...FORM_FIELDS_INITIAL_VALUES,
        images: {},
      },
      label: formatWritethruLabel(article),
    }
  );

const getTranslationFormInitialValues = () =>
  ({
    writethru: "current",
    translationType: "deepl",
    translateFrom: TRANSLATION_LANGUAGES_CODES_MAP.en,
    translateTo: TRANSLATION_LANGUAGES_CODES_MAP.fr,
    translations: {
      current: {
        original: {
          ...FORM_FIELDS_INITIAL_VALUES,
          images: {},
        },
        aiTranslation: {
          ...FORM_FIELDS_INITIAL_VALUES,
          images: {},
        },
        manualTranslation: {
          ...FORM_FIELDS_INITIAL_VALUES,
          images: {},
        },
        label: gettext("Current Story"),
      },
    },
    glossary: "",
    style: "",
  } as const);

const getTranslationFormValues = (
  article: IArticle,
  articleVersions: IArticle[]
): TranslationForm => {
  const { gettext } = superdesk.localization;
  const { writethrus, originals } = articleVersions.reduce<{
      writethrus: typeof articleVersions;
      originals: Partial<
        Record<
          ValueOf<typeof TRANSLATION_LANGUAGES_CODES_MAP>,
          (typeof articleVersions)[number]
        >
      >;
    }>(
      (acc, article) => {
        if (
          article.anpa_take_key !== null &&
          typeof article.anpa_take_key === "string" &&
          article.anpa_take_key.length > 0
        ) {
          acc.writethrus.push(article);
          return acc;
        }

        const lang = article.language?.toLowerCase();
        if (!isLanguageCode(lang)) return acc;

        acc.originals[TRANSLATION_LANGUAGES_CODES_MAP[lang]] = article;
        return acc;
      },
      { writethrus: [], originals: {} }
    ),
    current = {
      ...getTranslationEntryFormValues({
        article,
        images: getImagesFormValues(article),
      }),
      label: gettext("Current Story {{writethru}}", {
        writethru: formatWritethruLabel({
          ...article,
          isCurrentStory: true,
        }),
      }),
    },
    translations = {
      current,
      ...(originals.en && {
        [`${originals.en._id}`]: {
          ...getTranslationEntryFormValues({
            article: originals.en,
            images: getImagesFormValues(originals.en),
          }),
          label: `${
            originals.en.translated_from
              ? gettext("Translation")
              : gettext("Original")
          } (${originals.en.language})`,
        },
      }),
      ...(originals.fr && {
        [`${originals.fr._id}`]: {
          ...getTranslationEntryFormValues({
            article: originals.fr,
            images: getImagesFormValues(originals.fr),
          }),
          label: `${
            originals.fr.translated_from
              ? gettext("Translation")
              : gettext("Original")
          } (${originals.fr.language})`,
        },
      }),
      ...(writethrus.length &&
        writethrus.reduce<TranslationForm["translations"]>(
          (translations, article) => {
            const images = getImagesFormValues(article);
            const translationEntry = getTranslationEntryFormValues({
              article,
              images,
            });
            translations[`${article._id}`] = translationEntry;
            return translations;
          },
          {}
        )),
    },
    articleLanguage =
      typeof article.language === "string"
        ? article.language.toLowerCase()
        : undefined,
    translateTo =
      articleLanguage && isLanguageCode(articleLanguage)
        ? TRANSLATION_LANGUAGES_CODES_MAP[articleLanguage]
        : TRANSLATION_LANGUAGES_CODES_MAP.en,
    translateFrom =
      translateTo === TRANSLATION_LANGUAGES_CODES_MAP.en
        ? TRANSLATION_LANGUAGES_CODES_MAP.fr
        : TRANSLATION_LANGUAGES_CODES_MAP.en;

  return {
    writethru: getObjectKeys(translations)[0],
    translationType: "deepl",
    translateFrom,
    translateTo,
    translations,
    glossary: "",
    style: "",
  };
};

const validateTranslationForm: FormikConfig<TranslationForm>["validate"] = (
  values
) => {
  const errors: FormikErrors<TranslationForm> = {};

  for (const [key, value] of getObjectEntries(FORM_FIELDS)) {
    const error = value?.validate?.(
      values.translations[values.writethru].manualTranslation[key],
      { schema: superdesk.instance.config.schema?.["Story"]?.[key] }
    );

    if (!error) continue;

    Object.assign(errors, {
      translations: {
        [values.writethru]: {
          [TRANSLATION_VERSIONS.manualTranslation.value]: {
            ...errors?.translations?.[values.writethru]?.manualTranslation,
            [key]: error,
          },
        },
      },
    });
  }

  return errors;
};

export {
  ExtraTranslationForm,
  FORM_FIELDS,
  FORM_FIELDS_INITIAL_VALUES,
  formatWritethruLabel,
  FormInputProps,
  getTranslationFormInitialValues,
  getTranslationFormValues,
  getWritethrus,
  isLanguageCode,
  isManualTranslationDirty,
  isTranslationVersion,
  TranslationEntry,
  TranslationForm,
  validateTranslationForm,
};
