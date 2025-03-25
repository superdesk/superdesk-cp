import * as React from "react";
import { createPortal } from "react-dom";
import { Button, ButtonGroup, Modal } from "superdesk-ui-framework/react";
import { useSuperdesk } from "./superdesk-provider";

type ConfirmProps = {
  header?: string | JSX.Element;
  body: React.ReactNode;
  footer?: (
    handleConfirm: () => void,
    handleCancel: () => void
  ) => string | JSX.Element;
  footerProps?: {
    confirm?: Partial<React.ComponentProps<typeof Button>>;
    cancel?: Partial<React.ComponentProps<typeof Button>>;
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

export const ConfirmProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization,
    [confirmState, setConfirmState] = React.useState<
      | (ConfirmProps & {
          resolve?: (value: boolean) => void;
        })
      | null
    >(null);

  const confirm = React.useCallback(
    (props: ConfirmProps): Promise<boolean> =>
      new Promise((resolve) => {
        setConfirmState({ ...props, resolve });
      }),
    []
  );

  const handleConfirm = () => {
    confirmState?.resolve?.(true);
    setConfirmState(null);
  };

  const handleCancel = () => {
    confirmState?.resolve?.(false);
    setConfirmState(null);
  };

  const modal = confirmState
    ? createPortal(
        <Modal
          headerTemplate={
            confirmState.header ? confirmState.header : gettext("Confirm")
          }
          visible
          onHide={handleCancel}
          footerTemplate={
            <ButtonGroup align="end">
              {confirmState.footer ? (
                confirmState.footer(handleConfirm, handleCancel)
              ) : (
                <>
                  <Button
                    text={gettext("Cancel")}
                    style="hollow"
                    onClick={handleCancel}
                    {...confirmState.footerProps?.cancel}
                  />
                  <Button
                    text={gettext("Confirm")}
                    type="primary"
                    style="hollow"
                    onClick={handleConfirm}
                    {...confirmState.footerProps?.confirm}
                  />
                </>
              )}
            </ButtonGroup>
          }
        >
          {confirmState.body}
        </Modal>,
        document.body
      )
    : null;

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      {modal}
    </ConfirmContext.Provider>
  );
};
