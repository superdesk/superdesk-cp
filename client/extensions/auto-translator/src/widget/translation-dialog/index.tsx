import { Formik, FormikConfig } from "formik";
import * as React from "react";
import { IArticle } from "superdesk-api";
import { Modal } from "superdesk-ui-framework/react";
import { useSuperdesk } from "../../context";
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
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization,
    { applyFieldChangesToEditor } = superdesk.ui.article,
    { _id: articleId } = article,
    formRef = React.useRef<HTMLFormElement>(null);

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
      initialValues={getTranslationFormInitialValues(superdesk)}
      onSubmit={onSubmit}
      validate={validateTranslationForm(superdesk)}
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
