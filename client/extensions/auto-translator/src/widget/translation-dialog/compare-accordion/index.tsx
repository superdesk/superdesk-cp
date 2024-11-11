import DiffMatchPatch from "diff-match-patch";
import { useFormikContext } from "formik";
import * as React from "react";
import { Container, GridList, ToggleBox } from "superdesk-ui-framework/react";
import { Select } from "../../../components";
import { superdesk } from "../../../superdesk";
import { capitalize, getObjectKeys } from "../../../utilities";
import { TranslationDialogFormProps } from "../helpers";
import { getPrettyDiffHtml, sanitizeHtml } from "./helpers";

const COMPARE_VERSIONS = ["ls", "rs", "diff"] as const;

const CompareContent = ({
  headline,
  headline_extended,
  body_html,
  version,
}: Pick<
  TranslationDialogFormProps["translations"][string]["original"],
  "headline" | "headline_extended" | "body_html"
> & { version: (typeof COMPARE_VERSIONS)[number] }) => {
  const { gettext } = superdesk.localization;

  return (
    <>
      <div className="sd-input sd-input--medium sd-input--boxed-style sd-input--boxed-label">
        <span
          className="sd-input__label sd-input__label--boxed"
          id={`compare-headline-${version}-label`}
        >
          {capitalize(gettext("headline"))}
        </span>
        <div className="sd-input__input-container">
          <p
            aria-labelledby={`compare-headline-${version}-label`}
            className="m-0"
            dangerouslySetInnerHTML={{ __html: headline }}
          ></p>
        </div>
      </div>
      <div className="sd-input sd-input--medium sd-input--boxed-style sd-input--boxed-label">
        <span
          className="sd-input__label sd-input__label--boxed"
          id={`compare-extended-headline-${version}-label`}
        >
          {capitalize(gettext("extended headline"))}
        </span>
        <div className="sd-input__input-container">
          <p
            aria-labelledby={`compare-extended-headline-${version}-label`}
            className="m-0"
            dangerouslySetInnerHTML={{ __html: headline_extended }}
          ></p>
        </div>
      </div>
      <div className="sd-input sd-input--medium sd-input--boxed-style sd-input--boxed-label">
        <span
          className="sd-input__label sd-input__label--boxed"
          id={`compare-body-html-${version}-label`}
        >
          {capitalize(gettext("body HTML"))}
        </span>
        <div className="sd-input__input-container">
          <div
            aria-labelledby={`compare-body-html-${version}-label`}
            dangerouslySetInnerHTML={{ __html: body_html }}
          ></div>
        </div>
      </div>
    </>
  );
};

export const CompareAccordion = () => {
  const { gettext } = superdesk.localization;
  const { values } = useFormikContext<TranslationDialogFormProps>();
  const dmp = new DiffMatchPatch();

  const [isOpen, setIsOpen] = React.useState<boolean>(false);
  const [compareLeft, setCompareLeft] = React.useState<
    TranslationDialogFormProps["writethru"]
  >(getObjectKeys(values.translations)?.[0] ?? "");
  const [compareRight, setCompareRight] = React.useState<
    TranslationDialogFormProps["writethru"]
  >(getObjectKeys(values.translations)?.[0] ?? "");

  return (
    <ToggleBox
      variant="simple"
      title={capitalize(gettext("Compare"))}
      margin="none"
      onOpen={() => {
        setIsOpen(true);
      }}
      onClose={() => {
        setIsOpen(false);
      }}
    >
      {isOpen && (
        <Container gap="large" direction="column" className="mx-2">
          <div style={{ width: "100%" }}>
            <GridList margin="0">
              <Select
                value={compareLeft}
                onChange={(e) => {
                  setCompareLeft(e.target.value);
                }}
                label={`${capitalize(gettext("writethru"))} 1`}
              >
                <option value="" hidden></option>
                {getObjectKeys(values.translations).map((writethru) => (
                  <option value={writethru} key={`left-writethru-${writethru}`}>
                    {capitalize(writethru)}
                  </option>
                ))}
              </Select>
              <Select
                value={compareRight}
                onChange={(e) => {
                  setCompareRight(e.target.value);
                }}
                label={`${capitalize(gettext("writethru"))} 2`}
              >
                <option value="" hidden></option>
                {getObjectKeys(values.translations).map((writethru) => (
                  <option
                    value={writethru}
                    key={`right-writethru-${writethru}`}
                  >
                    {capitalize(writethru)}
                  </option>
                ))}
              </Select>
            </GridList>
          </div>
          {compareLeft && compareRight && (
            <div style={{ width: "100%" }}>
              <div
                className="sd-grid-list sd-grid-list--large sd-grid-list--gap-small sd-margin--0"
                style={{ gridTemplateColumns: "repeat(3, 1fr)" }}
              >
                {COMPARE_VERSIONS.map((version, index) => {
                  let header = `${capitalize(gettext("writethru"))} ${
                    index + 1
                  }`;
                  let headline: string,
                    headline_extended: string,
                    body_html: string;

                  switch (version) {
                    case "ls":
                      headline = sanitizeHtml(
                        values.translations[compareLeft].original.headline
                      );
                      headline_extended = sanitizeHtml(
                        values.translations[compareLeft].original
                          .headline_extended
                      );
                      body_html = sanitizeHtml(
                        values.translations[compareLeft].original.body_html
                      );
                      break;
                    case "rs":
                      headline = sanitizeHtml(
                        values.translations[compareRight].original.headline
                      );
                      headline_extended = sanitizeHtml(
                        values.translations[compareRight].original
                          .headline_extended
                      );
                      body_html = sanitizeHtml(
                        values.translations[compareRight].original.body_html
                      );
                      break;
                    case "diff":
                      header = capitalize(gettext("diff"));

                      const diffHeadline = dmp.diff_main(
                        sanitizeHtml(
                          values.translations[compareLeft].original.headline
                        ),
                        sanitizeHtml(
                          values.translations[compareRight].original.headline
                        )
                      );
                      const diffHeadline_extended = dmp.diff_main(
                        sanitizeHtml(
                          values.translations[compareLeft].original
                            .headline_extended
                        ),
                        sanitizeHtml(
                          values.translations[compareRight].original
                            .headline_extended
                        )
                      );
                      const diffBody_html = dmp.diff_main(
                        sanitizeHtml(
                          values.translations[compareLeft].original.body_html
                        ),
                        sanitizeHtml(
                          values.translations[compareRight].original.body_html
                        )
                      );

                      headline = getPrettyDiffHtml(diffHeadline);
                      headline_extended = getPrettyDiffHtml(
                        diffHeadline_extended
                      );
                      body_html = getPrettyDiffHtml(diffBody_html);

                      console.log({
                        diffHeadline,
                        diffHeadline_extended,
                        diffBody_html,
                        headline,
                        headline_extended,
                        body_html,
                      });
                  }

                  return (
                    <Container key={version} gap="large" direction="column">
                      <p className="text-md font-medium self-center m-0">
                        {header}
                      </p>
                      <CompareContent
                        headline={headline}
                        headline_extended={headline_extended}
                        body_html={body_html}
                        version={version}
                      />
                    </Container>
                  );
                })}
              </div>
            </div>
          )}
        </Container>
      )}
    </ToggleBox>
  );
};
