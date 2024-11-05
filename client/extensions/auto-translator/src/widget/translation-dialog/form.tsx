import { useFormikContext } from "formik";
import * as React from "react";
import { IArticle } from "superdesk-api";
import {
  Container,
  ContentDivider,
  GridItem,
  GridItemContent,
  GridItemMedia,
  GridList,
  ResizablePanels,
} from "superdesk-ui-framework/react";
import {
  Button,
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
import { superdesk } from "../../superdesk";
import {
  TranslationFields,
  TranslationImageField,
  TranslationPayload,
  TranslationResponse,
  TranslationType,
} from "../../typings/translation";
import {
  capitalize,
  getObjectEntries,
  getObjectKeys,
  isArticle,
  isNotEmptyObject,
} from "../../utilities";

const { httpRequestJsonLocal } = superdesk;

type FormInputProps = Record<TranslationFields, string> & {
  images: Record<TranslationImageField, { description: string; href: string }>;
};

type TranslationEntry = Record<
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
  workingArticle: IArticle,
  images: ReturnType<typeof getImagesFormValues>
): TranslationEntry => ({
  original: {
    headline: workingArticle.headline ?? "",
    headline_extended: workingArticle?.extra?.headline_extended ?? "",
    body_html: workingArticle.body_html ?? "",
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
  workingArticle: IArticle,
  articleVersions: IArticle[]
): TranslationDialogFormProps => {
  const translations = articleVersions
    // version 0 is the initial object (contains no metadata)
    .filter((article) => article._current_version !== 0)
    .reduce<TranslationDialogFormProps["translations"]>(
      (translations, article) => {
        const images = getImagesFormValues(article);
        const translationEntry = getTranslationEntryFormValues(article, images);

        Object.assign(translations, {
          [`${article._current_version}`]: translationEntry,
        });

        return translations;
      },
      {}
    );

  const translateTo =
    TRANSLATION_LANGUAGES_CODES_MAP?.[
      workingArticle.language?.toLowerCase?.() as keyof typeof TRANSLATION_LANGUAGES_CODES_MAP
    ];
  const translateFrom =
    translateTo === TRANSLATION_LANGUAGES_CODES_MAP.en
      ? TRANSLATION_LANGUAGES_CODES_MAP.fr
      : TRANSLATION_LANGUAGES_CODES_MAP.en;

  return {
    writethru: Object.keys(translations)[0],
    translationType: "basic",
    translateFrom,
    translateTo,
    translations,
  };
};

const TranslationFormEntry = ({
  initialVersion,
}: {
  initialVersion: keyof TranslationEntry;
}) => {
  const { gettext } = superdesk.localization;
  const [version, setVersion] =
    React.useState<keyof TranslationEntry>(initialVersion);
  const { values } = useFormikContext<TranslationDialogFormProps>();
  const images = getObjectEntries(
    values.translations[values.writethru][version].images
  );

  return (
    <>
      <Select
        value={version}
        label={capitalize(gettext("version"))}
        onChange={(event) => {
          // @ts-ignore
          setVersion(event.currentTarget.value);
        }}
      >
        {getObjectEntries(TRANSLATION_VERSIONS).map(([value, label]) => (
          <option value={value} key={value}>
            {capitalize(gettext(label))}
          </option>
        ))}
      </Select>
      <FormTextInput
        name={`translations.${values.writethru}.${version}.headline`}
        label={capitalize(gettext("headline"))}
        readOnly={version !== "manualTranslation"}
      />
      <FormTextInput
        name={`translations.${values.writethru}.${version}.headline_extended`}
        label={capitalize(gettext("extended headline"))}
        readOnly={version !== "manualTranslation"}
      />
      <FormTextEditorInput
        name={`translations.${values.writethru}.${version}.body_html`}
        label={capitalize(gettext("body HTML"))}
        readOnly={version !== "manualTranslation"}
      />
      {images.length > 0 && (
        <>
          <ContentDivider align="left" margin="none">
            {capitalize(gettext("photos"))}
          </ContentDivider>
          <GridList margin="1">
            {images.map(([key, image]) => {
              return (
                <GridItem key={key} itemtype="photo">
                  <GridItemMedia>
                    <img src={image.href} alt={image.description} />
                  </GridItemMedia>
                  <GridItemContent>
                    <FormTextInput
                      name={`translations.${values.writethru}.${version}.images.${key}.description`}
                      label={capitalize(gettext("caption"))}
                      readOnly={version !== "manualTranslation"}
                    />
                  </GridItemContent>
                </GridItem>
              );
            })}
          </GridList>
        </>
      )}
    </>
  );
};

export const TranslationForm = ({
  currentVersion,
}: {
  currentVersion: IArticle["_current_version"];
}) => {
  const { gettext } = superdesk.localization;
  const [isLoading, setIsLoading] = React.useState(false);
  const { values, setFieldValue } =
    useFormikContext<TranslationDialogFormProps>();

  const getTranslation = (payload: TranslationPayload) =>
    httpRequestJsonLocal<TranslationResponse>({
      method: "POST",
      path: "/ai",
      payload: { service: "translate", item: payload },
    });

  const translateArticle = () => {
    console.log({ values });

    const images = getObjectEntries(
      values.translations[values.writethru].original.images
    ).reduce<Record<TranslationImageField, string>>((images, [key, image]) => {
      Object.assign(images, { [key]: image.description });
      return images;
    }, {});

    const payload = {
      body_html: "",
      payload: {
        headline: values.translations[values.writethru].original.headline,
        headline_extended:
          values.translations[values.writethru].original.headline_extended,
        body_html: values.translations[values.writethru].original.body_html,
        ...(isNotEmptyObject(images) && { images }),
      },
      target_language: values.translateTo,
      source_language: values.translateFrom,
      translation_type: values.translationType,
    } as const;

    setIsLoading(true);

    getTranslation(payload)
      .then((res) => {
        console.log({ res });

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

          if (
            isNotEmptyObject(
              values.translations[values.writethru].original.images
            ) &&
            isNotEmptyObject(res.analysis.translated_payload?.images)
          ) {
            for (const key of getObjectKeys(
              values.translations[values.writethru].original.images
            ))
              setFieldValue(
                `translations.${values.writethru}.${version}.images.${key}.description`,
                res.analysis.translated_payload.images[key]
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
      <GridList margin="0">
        <FormSelect
          name="writethru"
          label={`${capitalize(gettext("writethru"))}/${capitalize(
            gettext("version")
          )}`}
        >
          {getObjectKeys(values.translations).map((versionId) => (
            <option value={versionId} key={`version${versionId}`}>
              {`${currentVersion}` === versionId
                ? `${capitalize(versionId)} (${capitalize(gettext("current"))})`
                : capitalize(versionId)}
            </option>
          ))}
        </FormSelect>
        <FormSelect
          name="translationType"
          label={`${capitalize(gettext("translation"))} ${capitalize(
            gettext("type")
          )}`}
        >
          {getObjectEntries(TRANSLATION_TYPES).map(([value, label]) => (
            <option value={value} key={value}>
              {label}
            </option>
          ))}
        </FormSelect>
        <FormSelect
          name="translateFrom"
          label={`${capitalize(gettext("translate"))} ${capitalize(
            gettext("from")
          )}`}
        >
          {getObjectEntries(TRANSLATION_LANGUAGES).map(([value, label]) => (
            <option value={value} key={value}>
              {capitalize(gettext(label))}
            </option>
          ))}
        </FormSelect>
        <FormSelect
          name="translateTo"
          label={`${capitalize(gettext("translate"))} ${capitalize(
            gettext("to")
          )}`}
        >
          {getObjectEntries(TRANSLATION_LANGUAGES).map(([value, label]) => (
            <option value={value} key={value}>
              {capitalize(gettext(label))}
            </option>
          ))}
        </FormSelect>
        <Button
          label={capitalize(gettext("translate"))}
          aria-label={capitalize(gettext("translate"))}
          className="self-end"
          superdeskButtonProps={{
            type: "primary",
            disabled: isLoading,
            isLoading,
          }}
          // @ts-ignore
          onClick={(event) => {
            translateArticle();
          }}
        />
      </GridList>
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
