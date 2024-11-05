import * as React from "react";
import { ButtonGroup } from "superdesk-ui-framework/react";
import { Button } from "../../components";
import { superdesk } from "../../superdesk";
import { capitalize } from "../../utilities";

type FooterProps = { closeDialog: () => void };

export const Footer = ({ closeDialog }: FooterProps) => {
  const { gettext } = superdesk.localization;

  return (
    <ButtonGroup align="end">
      <Button
        label={capitalize(gettext("cancel"))}
        aria-label={capitalize(gettext("cancel"))}
        superdeskButtonProps={{
          style: "hollow",
        }}
        onClick={closeDialog}
      />
      <Button
        type="submit"
        label={`${capitalize(gettext("apply"))} ${capitalize(
          gettext("translation")
        )}`}
        aria-label={`${capitalize(gettext("apply"))} ${capitalize(
          gettext("translation")
        )}`}
        superdeskButtonProps={{
          type: "primary",
          style: "hollow",
        }}
      />
    </ButtonGroup>
  );
};
