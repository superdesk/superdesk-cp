import { useFormikContext } from "formik";
import * as React from "react";
import { IArticle, ISuperdesk } from "superdesk-api";
import {
  Button,
  Container,
  ContentDivider,
  Option,
  ResizablePanels,
} from "superdesk-ui-framework/react";
import {
  FormSelect,
  FormTextEditorInput,
  FormTextInput,
  Select,
} from "../../components";
import {
  TRANSLATION_LANGUAGES,
  TRANSLATION_LANGUAGES_CODES_MAP,
  TRANSLATION_TYPES,
  TRANSLATION_VERSIONS,
  WIDGET_ID,
} from "../../constants";
import { typedSetFieldValue } from "../../formik-utilties";
import { superdesk } from "../../superdesk";
import {
  TranslationPayload,
  TranslationResponse,
} from "../../typings/translation";
import {
  capitalize,
  getObjectEntries,
  getObjectKeys,
  isArticle,
  isNotEmptyObject,
} from "../../utilities";
import { CompareAccordion } from "./compare-accordion";
import {
  FormInputProps,
  isLanguageCode,
  isTranslationVersion,
  TranslationDialogFormProps,
  TranslationEntry,
} from "./helpers";

const { httpRequestJsonLocal } = superdesk;

const getImagesFormValues = (workingArticle: IArticle) =>
  getObjectEntries(workingArticle?.associations || {}).reduce<
    Record<keyof TranslationEntry, FormInputProps["images"]>
  >(
    (images, [key, article]) => {
      if (!isArticle(article)) return images;

      const description = article?.description_text;
      const thumbnailHref = article?.renditions?.thumbnail?.href;

      if (!thumbnailHref) return images;

      Object.assign(images.original, {
        [key]: { description: description ?? "", href: thumbnailHref },
      });
      Object.assign(images.aiTranslation, {
        [key]: { description: "", href: thumbnailHref },
      });
      Object.assign(images.manualTranslation, {
        [key]: { description: "", href: thumbnailHref },
      });

      return images;
    },
    { original: {}, aiTranslation: {}, manualTranslation: {} }
  );

const getTranslationEntryFormValues = (
  article: IArticle,
  images: ReturnType<typeof getImagesFormValues>
): TranslationEntry => ({
  original: {
    headline: article.headline ?? "",
    headline_extended: article?.extra?.headline_extended ?? "",
    body_html: article.body_html ?? "",
    images: isNotEmptyObject(images.original) ? images.original : {},
  },
  aiTranslation: {
    headline: "",
    headline_extended: "",
    body_html: "",
    images: isNotEmptyObject(images.aiTranslation) ? images.aiTranslation : {},
  },
  manualTranslation: {
    headline: "",
    headline_extended: "",
    body_html: "",
    images: isNotEmptyObject(images.manualTranslation)
      ? images.manualTranslation
      : {},
  },
});

export const getTranslationDialogFormInitialValues = () =>
  ({
    writethru: "current",
    translationType: "basic",
    translateFrom: TRANSLATION_LANGUAGES_CODES_MAP.en,
    translateTo: TRANSLATION_LANGUAGES_CODES_MAP.fr,
    translations: {
      current: {
        original: {
          headline: "",
          headline_extended: "",
          body_html: "",
          images: {},
        },
        aiTranslation: {
          headline: "",
          headline_extended: "",
          body_html: "",
          images: {},
        },
        manualTranslation: {
          headline: "",
          headline_extended: "",
          body_html: "",
          images: {},
        },
      },
    },
  } as const);

export const getTranslationDialogFormValues = (
  currentArticle: IArticle,
  articleVersions: IArticle[]
): TranslationDialogFormProps => {
  const writethrus = articleVersions.filter((article) => article.anpa_take_key);

  const translations = writethrus.length
    ? writethrus.reduce<TranslationDialogFormProps["translations"]>(
        (translations, article) => {
          const images = getImagesFormValues(article);
          const translationEntry = getTranslationEntryFormValues(
            article,
            images
          );

          Object.assign(translations, {
            [`${article.anpa_take_key}`]: translationEntry,
          });

          return translations;
        },
        {
          current: getTranslationEntryFormValues(
            currentArticle,
            getImagesFormValues(currentArticle)
          ),
        }
      )
    : {
        current: getTranslationEntryFormValues(
          currentArticle,
          getImagesFormValues(currentArticle)
        ),
      };

  const currentArticleLanguage =
    typeof currentArticle.language === "string"
      ? currentArticle.language.toLowerCase()
      : undefined;

  const translateTo =
    currentArticleLanguage && isLanguageCode(currentArticleLanguage)
      ? TRANSLATION_LANGUAGES_CODES_MAP[currentArticleLanguage]
      : TRANSLATION_LANGUAGES_CODES_MAP.en;
  const translateFrom =
    translateTo === TRANSLATION_LANGUAGES_CODES_MAP.en
      ? TRANSLATION_LANGUAGES_CODES_MAP.fr
      : TRANSLATION_LANGUAGES_CODES_MAP.en;

  return {
    writethru: getObjectKeys(translations)[0],
    translationType: "basic",
    translateFrom,
    translateTo,
    translations,
  };
};

const getTranslation = (payload: TranslationPayload) =>
  httpRequestJsonLocal<TranslationResponse>({
    method: "POST",
    path: "/ai",
    payload: { service: "translate", item: payload },
  });

const getFormFields = (
  writethru: TranslationDialogFormProps["writethru"],
  version: keyof TranslationEntry,
  gettext: ISuperdesk["localization"]["gettext"]
) =>
  [
    {
      type: "text",
      name: `translations.${writethru}.${version}.headline`,
      label: gettext("Headline"),
    },
    {
      type: "text",
      name: `translations.${writethru}.${version}.headline_extended`,
      label: gettext("Extended Headline"),
    },
    {
      type: "textEditor",
      name: `translations.${writethru}.${version}.body_html`,
      label: gettext("body HTML"),
    },
  ] as const;

const TranslationFormEntry = ({
  initialVersion,
}: {
  initialVersion: keyof TranslationEntry;
}) => {
  const { gettext } = superdesk.localization;
  const [version, setVersion] =
    React.useState<keyof TranslationEntry>(initialVersion);
  const { values } = useFormikContext<TranslationDialogFormProps>();

  return (
    <>
      <Select
        value={version}
        label={gettext("Version")}
        onChange={(newValue) => {
          if (isTranslationVersion(newValue)) setVersion(newValue);
        }}
      >
        {getObjectEntries(TRANSLATION_VERSIONS).map(([key, value]) => (
          <Option value={value.value} key={`version-${key}`}>
            {value.getLabel(gettext)}
          </Option>
        ))}
      </Select>
      {getFormFields(values.writethru, version, gettext).map((field) => {
        switch (field.type) {
          case "textEditor":
            return (
              <FormTextEditorInput<TranslationDialogFormProps>
                key={field.name}
                name={field.name}
                label={field.label}
                readOnly={version !== "manualTranslation"}
              />
            );
          default:
            return (
              <FormTextInput<TranslationDialogFormProps>
                key={field.name}
                name={field.name}
                label={field.label}
                readonly={version !== "manualTranslation"}
              />
            );
        }
      })}
    </>
  );
};

export const TranslationForm = () => {
  const { gettext } = superdesk.localization;
  const [isLoading, setIsLoading] = React.useState(false);
  const { values, setFieldValue: formikSetFieldValue } =
    useFormikContext<TranslationDialogFormProps>();
  const setFieldValue =
    typedSetFieldValue<TranslationDialogFormProps>(formikSetFieldValue);

  const translateArticle = () => {
    const payload = {
      body_html: "",
      payload: {
        headline: values.translations[values.writethru].original.headline,
        headline_extended:
          values.translations[values.writethru].original.headline_extended,
        body_html: values.translations[values.writethru].original.body_html,
      },
      target_language: values.translateTo,
      source_language: values.translateFrom,
      translation_type: values.translationType,
    } as const;

    setIsLoading(true);

    getTranslation(payload)
      .then((res) => {
        if ("error" in res.analysis) {
          console.error(res.analysis.error);
          return;
        }

        const versions = ["aiTranslation", "manualTranslation"] as const;

        for (const version of versions) {
          setFieldValue(
            `translations.${values.writethru}.${version}.headline`,
            res.analysis.translated_payload.headline
          );
          setFieldValue(
            `translations.${values.writethru}.${version}.headline_extended`,
            res.analysis.translated_payload.headline_extended
          );
          setFieldValue(
            `translations.${values.writethru}.${version}.body_html`,
            res.analysis.translated_payload.body_html
          );
        }
      })
      .catch((err) => {
        console.error({ err });
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  return (
    <>
      <div
        className={`${WIDGET_ID}__translation-form-settings-container d-grid gap-2 items-end`}
      >
        <FormSelect<TranslationDialogFormProps>
          name="writethru"
          label={gettext("Writethru")}
        >
          {getObjectKeys(values.translations).map((writethru) => (
            <Option value={writethru} key={`writethru-${writethru}`}>
              {capitalize(writethru)}
            </Option>
          ))}
        </FormSelect>
        <FormSelect<TranslationDialogFormProps>
          name="translationType"
          label={gettext("Translation Type")}
        >
          {getObjectEntries(TRANSLATION_TYPES).map(([value, label]) => (
            <Option value={value} key={`translationType-${value}`}>
              {label}
            </Option>
          ))}
        </FormSelect>
        <FormSelect<TranslationDialogFormProps>
          name="translateFrom"
          label={gettext("Translate From")}
        >
          {getObjectEntries(TRANSLATION_LANGUAGES).map(([key, value]) => (
            <Option value={value.value} key={`translateFrom-${key}`}>
              {value.getLabel(gettext)}
            </Option>
          ))}
        </FormSelect>
        <FormSelect<TranslationDialogFormProps>
          name="translateTo"
          label={gettext("Translate To")}
        >
          {getObjectEntries(TRANSLATION_LANGUAGES).map(([key, value]) => (
            <Option value={value.value} key={`translateTo-${key}`}>
              {value.getLabel(gettext)}
            </Option>
          ))}
        </FormSelect>
        <Button
          text={gettext("Translate")}
          type="primary"
          isLoading={isLoading}
          onClick={(event) => {
            event.preventDefault();
            translateArticle();
          }}
        />
      </div>
      <ContentDivider margin="small" />
      <CompareAccordion />
      <ContentDivider margin="small" />
      <Container className="flex-grow">
        <ResizablePanels
          direction="horizontal"
          primarySize={{ min: 33, default: 50 }}
          secondarySize={{ min: 33, default: 50 }}
        >
          <Container gap="large" direction="column" className="mx-2">
            <TranslationFormEntry initialVersion="original" />
          </Container>
          <Container gap="large" direction="column" className="mx-2">
            <TranslationFormEntry initialVersion="aiTranslation" />
          </Container>
        </ResizablePanels>
      </Container>
    </>
  );
};
