import * as React from "react";
import { IArticleSideWidgetComponentType } from "superdesk-api";
import {
  GridList,
  IllustrationButton,
  SvgIconIllustration,
} from "superdesk-ui-framework/react";
import { WIDGET_ID } from "../constants";
import { ConfirmProvider } from "../context";
import { superdesk } from "../superdesk";
import { TranslationDialog } from "./translation-dialog";

const { gettext } = superdesk.localization;

const Menu = ({ openWidget }: { openWidget: () => void }) => (
  <GridList size="x-small" gap="small" margin="0">
    <IllustrationButton text={gettext("Translate")} onClick={openWidget}>
      <SvgIconIllustration illustration="translate" />
    </IllustrationButton>
  </GridList>
);

const Widget = ({
  article,
}: {
  article: IArticleSideWidgetComponentType["article"];
}) => {
  const { AuthoringWidgetLayout, AuthoringWidgetHeading } =
    superdesk.components;
  const { showModal } = superdesk.ui;

  return (
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
            showModal(({ closeModal }) => (
              <ConfirmProvider>
                <TranslationDialog
                  article={article}
                  closeDialog={() => {
                    closeModal();
                  }}
                />
              </ConfirmProvider>
            ));
          }}
        />
      }
    />
  );
};

export const getAutoTranslatorWidget = () =>
  class AutoTranslatorWidget extends React.Component<IArticleSideWidgetComponentType> {
    render() {
      return <Widget article={this.props.article} />;
    }
  };
