import * as React from "react";
import { createPortal } from "react-dom";
import { IArticleSideWidgetComponentType, ISuperdesk } from "superdesk-api";
import {
  GridList,
  IllustrationButton,
  SvgIconIllustration,
} from "superdesk-ui-framework/react";
import { WIDGET_ID } from "../constants";
import { ConfirmProvider, SuperdeskProvider, useSuperdesk } from "../context";
import { TranslationDialog } from "./translation-dialog";

const Menu = ({ openWidget }: { openWidget: () => void }) => (
  <GridList size="x-small" gap="small" margin="0">
    <IllustrationButton
      text={useSuperdesk().localization.gettext("Translate")}
      onClick={openWidget}
    >
      <SvgIconIllustration illustration="translate" />
    </IllustrationButton>
  </GridList>
);

const Widget = ({
  article,
}: {
  article: IArticleSideWidgetComponentType["article"];
}) => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization,
    { AuthoringWidgetLayout, AuthoringWidgetHeading } = superdesk.components,
    [isOpen, setIsOpen] = React.useState(false);

  return (
    <>
      <AuthoringWidgetLayout
        header={
          <AuthoringWidgetHeading
            widgetId={WIDGET_ID}
            widgetName={gettext("Auto Translate")}
            editMode={false}
          />
        }
        body={
          <Menu
            openWidget={() => {
              setIsOpen(true);
            }}
          />
        }
      />
      {isOpen &&
        createPortal(
          <TranslationDialog
            article={article}
            closeDialog={() => {
              setIsOpen(false);
            }}
          />,
          document.body
        )}
    </>
  );
};

export const getAutoTranslatorWidget = (superdesk: ISuperdesk) =>
  class AutoTranslatorWidget extends React.Component<IArticleSideWidgetComponentType> {
    render() {
      return (
        <SuperdeskProvider superdesk={superdesk}>
          <ConfirmProvider>
            <Widget article={this.props.article} />
          </ConfirmProvider>
        </SuperdeskProvider>
      );
    }
  };
