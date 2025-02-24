import DiffMatchPatch from "diff-match-patch";
import { useFormikContext } from "formik";
import * as React from "react";
import {
  Container,
  Label,
  Option,
  ToggleBox,
} from "superdesk-ui-framework/react";
import { Select } from "../../../components";
import { WIDGET_ID } from "../../../constants";
import { superdesk } from "../../../superdesk";
import { capitalize, getObjectKeys } from "../../../utilities";
import { TranslationDialogFormProps } from "../helpers";
import { getPrettyDiffHtml, sanitizeHtml } from "./helpers";

const COMPARE_VERSIONS = ["ls", "rs", "diff"] as const;

const getCompareContentValues = (
  ls: TranslationDialogFormProps["translations"][string],
  rs: TranslationDialogFormProps["translations"][string],
  version: (typeof COMPARE_VERSIONS)[number]
) => {
  const { gettext } = superdesk.localization;
  const dmp = new DiffMatchPatch();
  let headline: string, headline_extended: string, body_html: string;

  switch (version) {
    case "ls":
      headline = sanitizeHtml(ls.original.headline);
      headline_extended = sanitizeHtml(ls.original.headline_extended);
      body_html = sanitizeHtml(ls.original.body_html);
      break;
    case "rs":
      headline = sanitizeHtml(rs.original.headline);
      headline_extended = sanitizeHtml(rs.original.headline_extended);
      body_html = sanitizeHtml(rs.original.body_html);
      break;
    case "diff":
      const diffHeadline = dmp.diff_main(
        sanitizeHtml(ls.original.headline),
        sanitizeHtml(rs.original.headline)
      );
      const diffHeadline_extended = dmp.diff_main(
        sanitizeHtml(ls.original.headline_extended),
        sanitizeHtml(rs.original.headline_extended)
      );
      const diffBody_html = dmp.diff_main(
        sanitizeHtml(ls.original.body_html),
        sanitizeHtml(rs.original.body_html)
      );
      headline = getPrettyDiffHtml({ diffs: diffHeadline, gettext });
      headline_extended = getPrettyDiffHtml({
        diffs: diffHeadline_extended,
        gettext,
      });
      body_html = getPrettyDiffHtml({ diffs: diffBody_html, gettext });
  }

  return { headline, headline_extended, body_html };
};

const CompareContent = ({
  headline,
  headline_extended,
  body_html,
}: Pick<
  TranslationDialogFormProps["translations"][string]["original"],
  "headline" | "headline_extended" | "body_html"
>) => {
  const { gettext } = superdesk.localization;

  return (
    <div className="d-flex flex-col items-stretch content-stretch gap-2">
      <div className="d-flex flex-wrap items-stretch content-stretch gap-1">
        <Label text={gettext("Headline")} style="hollow" />
        <p
          className="m-0"
          style={{ width: "100%" }}
          dangerouslySetInnerHTML={{ __html: headline }}
        ></p>
      </div>
      <div className="d-flex flex-wrap items-stretch content-stretch gap-1">
        <Label text={gettext("Extended Headline")} style="hollow" />
        <p
          className="m-0"
          style={{ width: "100%" }}
          dangerouslySetInnerHTML={{ __html: headline_extended }}
        ></p>
      </div>
      <div className="d-flex flex-wrap items-stretch content-stretch gap-1">
        <Label text={gettext("body HTML")} style="hollow" />
        <p
          className="m-0"
          style={{ width: "100%" }}
          dangerouslySetInnerHTML={{ __html: body_html }}
        ></p>
      </div>
    </div>
  );
};

export const CompareAccordion = () => {
  const { gettext } = superdesk.localization;
  const { values } = useFormikContext<TranslationDialogFormProps>();

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
      title={gettext("Compare")}
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
          <div
            className={`${WIDGET_ID}__compare-accordion-settings-container d-grid gap-2`}
          >
            <Select
              value={compareLeft}
              onChange={(newValue) => {
                setCompareLeft(newValue);
              }}
              label={gettext("Writethru 1")}
            >
              {getObjectKeys(values.translations).map((writethru) => (
                <Option value={writethru} key={`left-writethru-${writethru}`}>
                  {capitalize(writethru)}
                </Option>
              ))}
            </Select>
            <Select
              value={compareRight}
              onChange={(newValue) => {
                setCompareRight(newValue);
              }}
              label={gettext("Writethru 2")}
            >
              {getObjectKeys(values.translations).map((writethru) => (
                <Option value={writethru} key={`right-writethru-${writethru}`}>
                  {capitalize(writethru)}
                </Option>
              ))}
            </Select>
          </div>
          {compareLeft && compareRight && (
            <article
              className={`${WIDGET_ID}__compare-accordion-content-container d-grid gap-2`}
              tabIndex={0}
              aria-label={gettext("Compare Writethru Diff")}
            >
              {COMPARE_VERSIONS.map((version, index) => {
                const header =
                  version === "diff"
                    ? gettext("Diff")
                    : `${gettext("Writethru")} ${index + 1}`;

                return (
                  <Container key={version} gap="large" direction="column">
                    <p className="text-md font-medium self-center m-0">
                      {header}
                    </p>
                    <CompareContent
                      {...getCompareContentValues(
                        values.translations[compareLeft],
                        values.translations[compareRight],
                        version
                      )}
                    />
                  </Container>
                );
              })}
            </article>
          )}
        </Container>
      )}
    </ToggleBox>
  );
};
