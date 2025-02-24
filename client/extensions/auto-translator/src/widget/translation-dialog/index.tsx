import { Formik, FormikConfig } from "formik";
import * as React from "react";
import { IArticle } from "superdesk-api";
import { Loader, Modal } from "superdesk-ui-framework/react";
import { superdesk } from "../../superdesk";
import { Footer } from "./footer";
import {
  getTranslationDialogFormInitialValues,
  getTranslationDialogFormValues,
  TranslationForm,
} from "./form";
import { TranslationDialogFormProps } from "./helpers";

const { httpRequestJsonLocal } = superdesk;
const { prepareSuperdeskQuery } = superdesk.helpers;
const { applyFieldChangesToEditor } = superdesk.ui.article;

type TranslationDialogProps = {
  currentArticle: IArticle;
  closeDialog: () => void;
};

const getWritethrus = (event_id: IArticle["event_id"]) => {
  const query = prepareSuperdeskQuery("/search", {
    filter: {
      $and: [
        { state: { $ne: "spiked" } },
        { event_id: { $eq: event_id } },
        { type: { $ne: "composite" } },
      ],
    },
    sort: [{ versioncreated: "asc" }],
    page: 1,
    max_results: 50,
  });
  return httpRequestJsonLocal<{ _items: IArticle[] }>({
    ...query,
    urlParams: { ...query?.urlParams, repo: "archive,published" },
  });
};

export const TranslationDialog = ({
  currentArticle,
  closeDialog,
}: TranslationDialogProps) => {
  const { gettext } = superdesk.localization;
  const { _id: articleId, event_id } = currentArticle;

  const onSubmit: FormikConfig<TranslationDialogFormProps>["onSubmit"] = (
    values,
    _formikHelpers
  ) => {
    if (!articleId) return;

    applyFieldChangesToEditor(articleId, {
      key: "headline",
      value: values.translations[values.writethru].manualTranslation.headline,
    });
    applyFieldChangesToEditor(articleId, {
      key: "extra",
      value: {
        ...currentArticle?.extra,
        headline_extended:
          values.translations[values.writethru].manualTranslation
            .headline_extended,
      },
    });
    applyFieldChangesToEditor(articleId, {
      key: "body_html",
      value: values.translations[values.writethru].manualTranslation.body_html,
    });

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
          getWritethrus(event_id)
            .then(({ _items }) => {
              setValues(getTranslationDialogFormValues(currentArticle, _items));
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
              headerTemplate={gettext("Translation")}
              className="d-flex flex-auto flex-col self-stretch"
              visible
              size="x-large"
              onHide={closeDialog}
              footerTemplate={
                <Footer isLoading={isLoading} closeDialog={closeDialog} />
              }
            >
              {isLoading ? <Loader /> : <TranslationForm />}
            </Modal>
          </form>
        );
      }}
    </Formik>
  );
};
