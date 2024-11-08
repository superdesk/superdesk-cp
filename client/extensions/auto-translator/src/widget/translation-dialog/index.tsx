import { Formik, FormikConfig } from "formik";
import * as React from "react";
import { IArticle } from "superdesk-api";
import { Loader, Modal } from "superdesk-ui-framework/react";
import { superdesk } from "../../superdesk";
import { capitalize } from "../../utilities";
import { Footer } from "./footer";
import {
  getTranslationDialogFormInitialValues,
  getTranslationDialogFormValues,
  TranslationForm,
} from "./form";
import { TranslationDialogFormProps } from "./helpers";

const { httpRequestJsonLocal } = superdesk;
const { applyFieldChangesToEditor } = superdesk.ui.article;

type TranslationDialogProps = {
  currentArticle: IArticle;
  closeDialog: () => void;
};

export const TranslationDialog = ({
  currentArticle,
  closeDialog,
}: TranslationDialogProps) => {
  const { gettext } = superdesk.localization;
  const { _id: articleId, event_id } = currentArticle;

  console.log({ currentArticle });

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
          const getWritethrus = () =>
            httpRequestJsonLocal<{ _items: IArticle[] }>({
              method: "GET",
              path: "/search",
              urlParams: {
                repo: "archive,published",
                source: {
                  query: {
                    filtered: {
                      filter: {
                        and: [
                          { not: { term: { state: "spiked" } } },
                          {
                            term: {
                              event_id,
                            },
                          },
                          { not: { term: { type: "composite" } } },
                        ],
                      },
                    },
                  },
                  size: 200,
                  from: 0,
                  sort: { versioncreated: "asc" },
                },
              },
            });

          getWritethrus()
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
              headerTemplate={capitalize(gettext("translation"))}
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
