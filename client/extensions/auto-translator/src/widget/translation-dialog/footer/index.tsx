import { useFormikContext } from "formik";
import * as React from "react";
import { Button, ButtonGroup } from "superdesk-ui-framework/react";
import { FORM_ID, SUBMITTER_ID } from "../../../constants";
import { useSuperdesk } from "../../../context";
import { isManualTranslationDirty, TranslationForm } from "../helpers";

const SubmitButton = ({
  formRef,
}: {
  formRef: React.RefObject<HTMLFormElement>;
}) => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization,
    { isValid, status, values, getFieldMeta } =
      useFormikContext<TranslationForm>();

  const handleOnSubmitClick = () => {
    if (!formRef.current) return;

    const button = document.createElement("button");
    button.type = "submit";
    button.style.display = "none";
    button.id = SUBMITTER_ID;
    button.setAttribute("form", FORM_ID);

    formRef.current.addEventListener(
      "submit",
      () => {
        button.remove();
      },
      { once: true }
    );

    document.body.appendChild(button);
    button.click();
  };

  return (
    <Button
      text={gettext("Apply Translation")}
      type="primary"
      disabled={
        !isValid ||
        status.isLoading ||
        (status.isPristine &&
          !isManualTranslationDirty({ values, getFieldMeta }, superdesk))
      }
      onClick={handleOnSubmitClick}
    />
  );
};

export const Footer = ({
  closeDialog,
  formRef,
}: {
  closeDialog: () => void;
  formRef: React.RefObject<HTMLFormElement>;
}) => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization;

  return (
    <ButtonGroup align="end">
      <Button text={gettext("Cancel")} style="hollow" onClick={closeDialog} />
      <SubmitButton formRef={formRef} />
    </ButtonGroup>
  );
};
