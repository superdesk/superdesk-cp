import * as React from "react";
import { Button, Modal } from "superdesk-ui-framework/react";
import { superdesk } from "../superdesk";

type ErrorDialogProps = {
  message: string;
  closeModal: () => void;
};

export const ErrorDialog = ({ message, closeModal }: ErrorDialogProps) => {
  const { gettext } = superdesk.localization;

  const closeDialog = () => {
    closeModal();
  };

  return (
    <Modal
      headerTemplate={gettext("Error")}
      visible
      size="medium"
      onHide={closeDialog}
      footerTemplate={
        <Button text={gettext("Ok")} style="hollow" onClick={closeDialog} />
      }
    >
      {message}
    </Modal>
  );
};
