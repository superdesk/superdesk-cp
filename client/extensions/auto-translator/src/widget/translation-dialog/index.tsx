import { Formik, FormikConfig } from "formik";
import * as React from "react";
import { IArticle } from "superdesk-api";
import { Modal } from "superdesk-ui-framework/react";
import { superdesk } from "../../superdesk";
import { getObjectValues } from "../../utilities";
import { Footer } from "./footer";
import { TranslationForm } from "./form";
import {
  ExtraTranslationForm,
  FORM_FIELDS,
  getTranslationFormInitialValues,
  TranslationForm as TranslationFormType,
  validateTranslationForm,
} from "./helpers";

export const TranslationDialog = ({
  article,
  closeDialog,
}: {
  article: IArticle;
  closeDialog: () => void;
}) => {
  const { gettext } = superdesk.localization;
  const { applyFieldChangesToEditor } = superdesk.ui.article;
  const { _id: articleId } = article;
  const formRef = React.useRef<HTMLFormElement>(null);

  const onSubmit: FormikConfig<TranslationFormType>["onSubmit"] = (
    values,
    _formikHelpers
  ) => {
    if (!articleId) return;

    for (const value of getObjectValues(FORM_FIELDS))
      applyFieldChangesToEditor(
        articleId,
        value.setEditorValue(values, { article })
      );

    closeDialog();
  };

  return (
    <Formik<TranslationFormType, ExtraTranslationForm>
      enableReinitialize
      initialValues={getTranslationFormInitialValues()}
      onSubmit={onSubmit}
      validate={validateTranslationForm}
      initialStatus={{ isLoading: true, isPristine: true }}
    >
      <Modal
        headerTemplate={gettext("Translation Widget")}
        visible
        size="x-large"
        onHide={closeDialog}
        footerTemplate={<Footer closeDialog={closeDialog} formRef={formRef} />}
      >
        <TranslationForm article={article} ref={formRef} />
      </Modal>
    </Formik>
  );
};
