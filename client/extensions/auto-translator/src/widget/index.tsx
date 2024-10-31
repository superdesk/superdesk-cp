import * as React from "react";
import { createPortal } from "react-dom";
import { IArticleSideWidgetComponentType } from "superdesk-api";
import {
  IllustrationButton,
  SvgIconIllustration,
} from "superdesk-ui-framework/react";
import { superdesk } from "../superdesk";
import { WIDGET_ID } from "../utilities";
import { TranslationDialog } from "./translation-dialog";

type AutoTranslatorWidgetProps = { isTranslationOpen: boolean };

export class AutoTranslatorWidget extends React.Component<
  IArticleSideWidgetComponentType,
  AutoTranslatorWidgetProps
> {
  state = { isTranslationOpen: false };

  render() {
    const { AuthoringWidgetLayout, AuthoringWidgetHeading, Spacer } =
      superdesk.components;

    const closeTranslationDialog = () => {
      this.setState({ isTranslationOpen: false });
    };

    return (
      <>
        <AuthoringWidgetLayout
          header={
            <Spacer v gap="0" alignItems="center">
              <AuthoringWidgetHeading
                widgetId={WIDGET_ID}
                // TODO: add localization
                widgetName={"Auto Translate"}
                editMode={false}
              />
              <></>
            </Spacer>
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
              workingArticle={this.props.article}
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
  return (
    <div className="sd-grid-list sd-grid-list--xx-small sd-grid-list--gap-s sd-grid-list--no-margin">
      <IllustrationButton text="Translate" onClick={openTranslationDialog}>
        <SvgIconIllustration illustration="translate" />
      </IllustrationButton>
    </div>
  );
};
