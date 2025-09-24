import * as React from "react";
import {
  Button,
  ButtonGroup,
  Modal as SuperdeskModal,
} from "superdesk-ui-framework/react";
import { superdesk } from "../superdesk";

type ConfirmProps = {
  header?: string | JSX.Element;
  body: React.ReactNode;
  footer?: (
    handleConfirm: () => void,
    handleCancel: () => void
  ) => string | JSX.Element;
  footerProps?: {
    confirm?: { buttonProps?: Partial<React.ComponentProps<typeof Button>> };
    cancel?: { buttonProps?: Partial<React.ComponentProps<typeof Button>> };
  };
};

type ConfirmContextType = {
  confirm: (props: ConfirmProps) => Promise<boolean>;
};

const ConfirmContext = React.createContext<ConfirmContextType | undefined>(
  undefined
);

export const useConfirm = () => {
  const context = React.useContext(ConfirmContext);
  if (!context)
    throw new Error("useConfirm must be used within a ConfirmProvider");
  return context;
};

type ConfirmModalProps = ConfirmProps & {
  resolve: (value: boolean) => void;
  closeModal: () => void;
};

const ConfirmModal = ({
  header,
  footer,
  footerProps,
  body,
  resolve,
  closeModal,
}: ConfirmModalProps) => {
  const { gettext } = superdesk.localization;

  const handleConfirm = () => {
    closeModal();
    resolve(true);
  };

  const handleCancel = () => {
    closeModal();
    resolve(false);
  };

  return (
    <SuperdeskModal
      headerTemplate={header ? header : gettext("Confirm")}
      visible
      onHide={handleCancel}
      footerTemplate={
        <ButtonGroup align="end">
          {footer ? (
            footer(handleConfirm, handleCancel)
          ) : (
            <>
              <Button
                text={gettext("Cancel")}
                style="hollow"
                onClick={handleCancel}
                {...footerProps?.cancel?.buttonProps}
              />
              <Button
                text={gettext("Confirm")}
                type="primary"
                style="hollow"
                onClick={handleConfirm}
                {...footerProps?.confirm?.buttonProps}
              />
            </>
          )}
        </ButtonGroup>
      }
    >
      {body}
    </SuperdeskModal>
  );
};

export const ConfirmProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const { showModal } = superdesk.ui;

  const confirm = React.useCallback(
    (confirmProps: ConfirmProps): Promise<boolean> =>
      new Promise((resolve) => {
        showModal(({ closeModal }) => (
          <ConfirmModal {...{ ...confirmProps, resolve, closeModal }} />
        ));
      }),
    []
  );

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
    </ConfirmContext.Provider>
  );
};
