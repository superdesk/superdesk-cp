import * as React from "react";
import { createPortal } from "react-dom";
import { IArticleSideWidgetComponentType } from "superdesk-api";
import {
  GridList,
  IllustrationButton,
  SvgIconIllustration,
} from "superdesk-ui-framework/react";
import { WIDGET_ID } from "../constants";
import { superdesk } from "../superdesk";
import { TranslationDialog } from "./translation-dialog";

type AutoTranslatorWidgetProps = { isTranslationOpen: boolean };

export class AutoTranslatorWidget extends React.Component<
  IArticleSideWidgetComponentType,
  AutoTranslatorWidgetProps
> {
  state = { isTranslationOpen: false };

  render() {
    const { gettext } = superdesk.localization;
    const { AuthoringWidgetLayout, AuthoringWidgetHeading } =
      superdesk.components;

    const closeTranslationDialog = () => {
      this.setState({ isTranslationOpen: false });
    };

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
              openTranslationDialog={() => {
                this.setState({ isTranslationOpen: true });
              }}
            />
          }
        />
        {this.state.isTranslationOpen &&
          createPortal(
            <TranslationDialog
              currentArticle={this.props.article}
              closeDialog={closeTranslationDialog}
            />,
            document.body
          )}
      </>
    );
  }
}

type MenuProps = { openTranslationDialog: () => void };

const Menu = ({ openTranslationDialog }: MenuProps) => {
  const { gettext } = superdesk.localization;

  return (
    <GridList size="x-small" gap="small" margin="0">
      <IllustrationButton
        text={gettext("Translate")}
        onClick={openTranslationDialog}
      >
        <SvgIconIllustration illustration="translate" />
      </IllustrationButton>
    </GridList>
  );
};
