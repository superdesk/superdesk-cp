import { useFormikContext } from "formik";
import * as React from "react";
import { IArticle } from "superdesk-api";
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
  getObjectValues,
  isArticle,
  isNotEmptyObject,
} from "../../utilities";
import { CompareAccordion } from "./compare-accordion";
import {
  FORM_FIELDS,
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

      for (const version of getObjectKeys(TRANSLATION_VERSIONS)) {
        Object.assign(images[version], {
          [key]: { description: description ?? "", href: thumbnailHref },
        });
      }

      return images;
    },
    { original: {}, aiTranslation: {}, manualTranslation: {} }
  );

const getTranslationEntryFormValues = (
  article: IArticle,
  images: ReturnType<typeof getImagesFormValues>
) =>
  getObjectKeys(TRANSLATION_VERSIONS).reduce<TranslationEntry>(
    (formValues, version) => {
      if (version === "original") {
        formValues[version] = {
          ...getObjectEntries(FORM_FIELDS).reduce<
            Omit<FormInputProps, "images">
          >(
            (formValues, [key, value]) => {
              formValues[key] = value.getFormValue(article);
              return formValues;
            },
            { headline: "", headline_extended: "", body_html: "" }
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
    }
  );

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

  const translateFrom =
    currentArticleLanguage && isLanguageCode(currentArticleLanguage)
      ? TRANSLATION_LANGUAGES_CODES_MAP[currentArticleLanguage]
      : TRANSLATION_LANGUAGES_CODES_MAP.en;
  const translateTo =
    translateFrom === TRANSLATION_LANGUAGES_CODES_MAP.en
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
            {value.label}
          </Option>
        ))}
      </Select>
      {getObjectValues(FORM_FIELDS).map((value) => {
        const name = value.getName(values.writethru, version);

        switch (value.type) {
          case "textEditor":
            return (
              <FormTextEditorInput<TranslationDialogFormProps>
                key={name}
                name={name}
                label={value.label}
                readOnly={version !== "manualTranslation"}
              />
            );
          default:
            return (
              <FormTextInput<TranslationDialogFormProps>
                key={name}
                name={name}
                label={value.label}
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
      payload: getObjectKeys(FORM_FIELDS).reduce<
        Omit<FormInputProps, "images">
      >(
        (payload, field) => {
          payload[field] =
            values.translations[values.writethru].original[field];
          return payload;
        },
        { headline: "", headline_extended: "", body_html: "" }
      ),
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
          for (const key of getObjectKeys(FORM_FIELDS)) {
            setFieldValue(
              `translations.${values.writethru}.${version}.${key}`,
              res.analysis.translated_payload[key]
            );
          }
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
      <div className="auto-translator__translation-form-settings-container">
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
              {value.label}
            </Option>
          ))}
        </FormSelect>
        <FormSelect<TranslationDialogFormProps>
          name="translateTo"
          label={gettext("Translate To")}
        >
          {getObjectEntries(TRANSLATION_LANGUAGES).map(([key, value]) => (
            <Option value={value.value} key={`translateTo-${key}`}>
              {value.label}
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
      <Container>
        <ResizablePanels
          direction="horizontal"
          primarySize={{ min: 33, default: 50 }}
          secondarySize={{ min: 33, default: 50 }}
        >
          <Container
            gap="large"
            direction="column"
            className="auto-translator__translation-form-panel-container"
          >
            <TranslationFormEntry initialVersion="original" />
          </Container>
          <Container
            gap="large"
            direction="column"
            className="auto-translator__translation-form-panel-container"
          >
            <TranslationFormEntry initialVersion="aiTranslation" />
          </Container>
        </ResizablePanels>
      </Container>
    </>
  );
};
