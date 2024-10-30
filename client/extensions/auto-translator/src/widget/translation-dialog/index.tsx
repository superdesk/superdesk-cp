import { Formik, FormikHelpers, FormikProps, useFormikContext } from "formik";
import * as React from "react";
import { IArticle } from "superdesk-api";
import {
  Container,
  ContentDivider,
  GridItem,
  GridItemContent,
  GridItemMedia,
  GridList,
  Modal,
  ResizablePanels,
} from "superdesk-ui-framework/react";
import {
  Button,
  FormSelect,
  FormTextEditorInput,
  FormTextInput,
  Select,
} from "../../components";
import { superdesk } from "../../superdesk";
import {
  TranslationFields,
  TranslationImageField,
  TranslationPayload,
  TranslationResponse,
  TranslationType,
} from "../../typings/translation";
import {
  getObjectEntries,
  getObjectKeys,
  isArticle,
  isNotEmptyObject,
  TRANSLATION_LANGUAGES,
  TRANSLATION_TYPES,
} from "../../utilities";
import { Footer } from "./footer";

const { applyFieldChangesToEditor } = superdesk.ui.article;
const { httpRequestJsonLocal } = superdesk;

type TranslationDialogProps = {
  workingArticle: IArticle;
  closeDialog: () => void;
};

type FormInputProps = Record<TranslationFields, string> & {
  images: Record<TranslationImageField, { description: string; href: string }>;
};

type TranslationDialogFormProps = {
  writethru: string;
  translationType: TranslationType;
  translateFrom: keyof typeof TRANSLATION_LANGUAGES;
  translateTo: keyof typeof TRANSLATION_LANGUAGES;
  translations: {
    [key: string]: {
      original: FormInputProps;
      aiTranslation: FormInputProps;
      manualTranslation: FormInputProps;
    };
  };
};

const getTranslationDialogFormInitialValues = (
  workingArticle: IArticle
): TranslationDialogFormProps => {
  const images = getObjectEntries(workingArticle?.associations || {}).reduce<
    Record<
      keyof TranslationDialogFormProps["translations"][string],
      FormInputProps["images"]
    >
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

  return {
    writethru: "original" as const,
    translationType: "basic",
    translateFrom: workingArticle?.language ?? "en",
    translateTo: "fr",
    translations: {
      original: {
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
          images: isNotEmptyObject(images.aiTranslation)
            ? images.aiTranslation
            : {},
        },
        manualTranslation: {
          headline: "",
          headline_extended: "",
          body_html: "",
          images: isNotEmptyObject(images.manualTranslation)
            ? images.manualTranslation
            : {},
        },
      },
    },
  };
};

const TranslationForm = ({
  initialVersion,
}: {
  initialVersion: "original" | "aiTranslation";
}) => {
  const { values } = useFormikContext<TranslationDialogFormProps>();
  const [version, setVersion] =
    React.useState<keyof TranslationDialogFormProps["translations"][string]>(
      initialVersion
    );

  const images = getObjectEntries(
    values.translations[values.writethru][version].images
  );

  return (
    <>
      <Select
        value={version}
        label="Version"
        onChange={(event) => {
          // @ts-ignore
          setVersion(event.currentTarget.value);
        }}
      >
        <option value="original">Original</option>
        <option value="aiTranslation">AI Translated</option>
        <option value="manualTranslation">Manual Translation</option>
      </Select>
      <FormTextInput
        name={`translations.${values.writethru}.${version}.headline`}
        label="Headline"
        disabled={version === "aiTranslation"}
      />
      <FormTextInput
        name={`translations.${values.writethru}.${version}.headline_extended`}
        label="Extended Headline"
        disabled={version === "aiTranslation"}
      />
      <FormTextEditorInput
        name={`translations.${values.writethru}.${version}.body_html`}
        label="Body HTML"
        readOnly={version === "aiTranslation"}
      />
      {images.length > 0 && (
        <>
          <ContentDivider align="left" margin="none">
            Photos
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
                      label="Caption"
                      disabled={version === "aiTranslation"}
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

export const TranslationDialog = ({
  workingArticle,
  closeDialog,
}: TranslationDialogProps) => {
  const { _id: articleId } = workingArticle;

  console.log({ workingArticle });

  const onSubmit = (
    values: TranslationDialogFormProps,
    // @ts-ignore
    formikHelpers: FormikHelpers<TranslationDialogFormProps>
  ) => {
    if (!articleId) return;

    applyFieldChangesToEditor(articleId, {
      key: "headline",
      value: values.translations[values.writethru].manualTranslation.headline,
    });
    applyFieldChangesToEditor(articleId, {
      key: "extra",
      value: {
        ...workingArticle?.extra,
        headline_extended:
          values.translations[values.writethru].manualTranslation
            .headline_extended,
      },
    });
    applyFieldChangesToEditor(articleId, {
      key: "body_html",
      value: values.translations[values.writethru].manualTranslation.body_html,
    });

    for (const [key, image] of getObjectEntries(
      values.translations[values.writethru].manualTranslation.images
    )) {
      const prevImage = workingArticle?.associations?.[key];

      if (!prevImage) continue;

      applyFieldChangesToEditor(articleId, {
        key: "associations",
        value: {
          ...workingArticle.associations,
          [key]: { ...prevImage, description_text: image.description },
        },
      });
    }

    closeDialog();
  };

  const getTranslation = (payload: TranslationPayload) => {
    return httpRequestJsonLocal<TranslationResponse>({
      method: "POST",
      path: "/ai",
      payload: { service: "translate", item: payload },
    });
  };

  const translateArticle = ({
    values,
    setFieldValue,
  }: FormikProps<TranslationDialogFormProps>) => {
    console.log({ values });

    const payload = {
      body_html: "",
      payload: {
        headline: values.translations[values.writethru].original.headline,
        headline_extended:
          values.translations[values.writethru].original.headline_extended,
        body_html: values.translations[values.writethru].original.body_html,
        images: getObjectEntries(
          values.translations[values.writethru].original.images
        ).reduce<Record<TranslationImageField, string>>(
          (images, [key, image]) => {
            Object.assign(images, { [key]: image.description });
            return images;
          },
          {}
        ),
      },
      target_language: values.translateTo,
      source_language: values.translateFrom,
      translation_type: values.translationType,
    } as const;

    getTranslation(payload)
      .then((res) => {
        console.log({ res });

        for (const version of ["aiTranslation", "manualTranslation"] as const) {
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
              values.translations[values.writethru].original?.images
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
        console.log({ err });
      });
  };

  return (
    <Formik
      // TODO: Generate inital values with writethrus
      initialValues={getTranslationDialogFormInitialValues(workingArticle)}
      onSubmit={onSubmit}
    >
      {(formikProps: FormikProps<TranslationDialogFormProps>) => (
        <form onSubmit={formikProps.handleSubmit}>
          <Modal
            headerTemplate="Translate"
            className="d-flex flex-auto flex-col self-stretch"
            visible
            size="x-large"
            onHide={closeDialog}
            footerTemplate={<Footer closeDialog={closeDialog} />}
          >
            <GridList margin="0">
              <FormSelect name="writethru" label="Writethru/Version">
                {/* TODO: Fetch writethrus from api */}
                <option value="original">Original</option>
              </FormSelect>
              <FormSelect name="translationType" label="Translation Type">
                {getObjectEntries(TRANSLATION_TYPES).map(([value, label]) => (
                  <option value={value} key={value}>
                    {label}
                  </option>
                ))}
              </FormSelect>
              <FormSelect name="translateFrom" label="Translate From">
                {getObjectEntries(TRANSLATION_LANGUAGES).map(
                  ([value, label]) => (
                    <option value={value} key={value}>
                      {label}
                    </option>
                  )
                )}
              </FormSelect>
              <FormSelect name="translateTo" label="Translate To">
                {getObjectEntries(TRANSLATION_LANGUAGES).map(
                  ([value, label]) => (
                    <option value={value} key={value}>
                      {label}
                    </option>
                  )
                )}
              </FormSelect>
              <Container className="items-end">
                <Button
                  label="Translate"
                  aria-label="Translate"
                  superdeskButtonProps={{ type: "primary" }}
                  // @ts-ignore
                  onClick={(event) => {
                    translateArticle(formikProps);
                  }}
                />
              </Container>
            </GridList>
            <ContentDivider margin="small" />
            <Container>
              <ResizablePanels
                direction="horizontal"
                primarySize={{ min: 33, default: 50 }}
                secondarySize={{ min: 33, default: 50 }}
              >
                <Container gap="large" direction="column" className="mx-2">
                  <TranslationForm initialVersion="original" />
                </Container>
                <Container gap="large" direction="column" className="mx-2">
                  <TranslationForm initialVersion="aiTranslation" />
                </Container>
              </ResizablePanels>
            </Container>
          </Modal>
        </form>
      )}
    </Formik>
  );
};
