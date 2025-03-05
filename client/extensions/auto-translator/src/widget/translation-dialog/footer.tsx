import * as React from "react";
import { ButtonGroup, Button } from "superdesk-ui-framework/react";
import { superdesk } from "../../superdesk";

type FooterProps = {
  isLoading: boolean;
  closeDialog: () => void;
};

export const Footer = ({ isLoading, closeDialog }: FooterProps) => {
  const { gettext } = superdesk.localization;

  return (
    <ButtonGroup align="end">
      <Button
        text={gettext("Cancel")}
        style="hollow"
        onClick={(event) => {
          event.preventDefault();
          closeDialog();
        }}
      />
      <Button
        text={gettext("Apply Translation")}
        type="primary"
        style="hollow"
        disabled={isLoading}
        onClick={(event) => {
          event.stopPropagation();
        }}
      />
    </ButtonGroup>
  );
};
