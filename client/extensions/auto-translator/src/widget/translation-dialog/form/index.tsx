import { useFormikContext } from "formik";
import * as React from "react";
import { IArticle } from "superdesk-api";
import { Spacer } from "superdesk-ui-framework/react";
import { ErrorDialog } from "../../../components";
import { FORM_ID, SUBMITTER_ID } from "../../../constants";
import { superdesk } from "../../../superdesk";
import { getTranslationFormValues, getWritethrus } from "../helpers";
import { TranslationSettings } from "../settings";
import { ToolTabs } from "../tool-tabs";
import { TranslationPanels } from "./panels";

export const TranslationForm = React.forwardRef<
  HTMLFormElement,
  { article: IArticle }
>(({ article }, ref) => {
  const { showModal } = superdesk.ui;
  const { gettext } = superdesk.localization;
  const { resetForm, handleSubmit, status, setStatus } = useFormikContext();

  React.useEffect(() => {
    getWritethrus(article)
      .then(({ _items }) => {
        resetForm({
          values: getTranslationFormValues(article, _items),
        });
      })
      .catch(() => {
        showModal(({ closeModal }) => (
          <ErrorDialog
            message={gettext("Failed to load writethrus.")}
            closeModal={closeModal}
          />
        ));
      })
      .finally(() => {
        setStatus({ ...status, isLoading: false });
      });
  }, []);

  return (
    <form
      id={FORM_ID}
      ref={ref}
      style={{ height: "100%" }}
      onSubmit={(event) => {
        event.preventDefault();
        event.stopPropagation();

        const nativeEvent = event.nativeEvent;
        if (!(nativeEvent instanceof SubmitEvent)) return;

        const submitter = nativeEvent.submitter;
        if (!submitter || submitter.id !== SUBMITTER_ID) return;

        handleSubmit(event);
      }}
    >
      <Spacer v gap="16" noWrap>
        <TranslationSettings />
        <ToolTabs />
        <TranslationPanels />
      </Spacer>
    </form>
  );
});
