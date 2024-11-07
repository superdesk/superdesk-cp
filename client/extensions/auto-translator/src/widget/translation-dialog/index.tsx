import { Formik, FormikConfig } from "formik";
import * as React from "react";
import { IArticle } from "superdesk-api";
import { Loader, Modal } from "superdesk-ui-framework/react";
import { superdesk } from "../../superdesk";
import { capitalize, getObjectEntries } from "../../utilities";
import { Footer } from "./footer";
import {
  getTranslationDialogFormInitialValues,
  getTranslationDialogFormValues,
  TranslationDialogFormProps,
  TranslationForm,
} from "./form";

const { httpRequestJsonLocal } = superdesk;
const { applyFieldChangesToEditor } = superdesk.ui.article;

type TranslationDialogProps = {
  workingArticle: IArticle;
  closeDialog: () => void;
};

export const TranslationDialog = ({
  workingArticle,
  closeDialog,
}: TranslationDialogProps) => {
  const { gettext } = superdesk.localization;
  const { _id: articleId, anpa_take_key: writethru } = workingArticle;

  console.log({ workingArticle });

  const onSubmit: FormikConfig<TranslationDialogFormProps>["onSubmit"] = (
    values,
    // @ts-ignore
    formikHelpers
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

  return (
    <Formik<TranslationDialogFormProps>
      enableReinitialize
      initialValues={getTranslationDialogFormInitialValues()}
      onSubmit={onSubmit}
    >
      {({ setValues, handleSubmit }) => {
        const [isLoading, setIsLoading] = React.useState(true);

        React.useEffect(() => {
          const getVersions = () =>
            httpRequestJsonLocal<{ _items: IArticle[] }>({
              method: "GET",
              path: `/archive/${articleId}`,
              urlParams: {
                embedded: { user: 1 },
                max_results: 200,
                version: "all",
              },
            });

          getVersions()
            .then(({ _items }) => {
              setValues(getTranslationDialogFormValues(workingArticle, _items));
            })
            .catch((err) => {
              console.error({ err });
            })
            .finally(() => {
              setIsLoading(false);
            });
        }, []);

        return (
          <form onSubmit={handleSubmit}>
            <Modal
              headerTemplate={capitalize(gettext("translation"))}
              className="d-flex flex-auto flex-col self-stretch"
              visible
              size="x-large"
              onHide={closeDialog}
              footerTemplate={
                <Footer isLoading={isLoading} closeDialog={closeDialog} />
              }
            >
              {isLoading ? (
                <Loader />
              ) : (
                <TranslationForm currentWritethru={writethru} />
              )}
            </Modal>
          </form>
        );
      }}
    </Formik>
  );
};
