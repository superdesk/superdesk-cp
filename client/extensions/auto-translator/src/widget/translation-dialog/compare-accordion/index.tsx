import DiffMatchPatch from "diff-match-patch";
import { useFormikContext } from "formik";
import * as React from "react";
import {
  Container,
  Label,
  Option,
  Spacer,
  ToggleBox,
} from "superdesk-ui-framework/react";
import { Select } from "../../../components";
import { superdesk } from "../../../superdesk";
import {
  capitalize,
  getObjectEntries,
  getObjectKeys,
} from "../../../utilities";
import {
  FORM_FIELDS,
  FormInputProps,
  TranslationDialogFormProps,
} from "../helpers";
import { getPrettyDiffHtml, sanitizeHtml } from "./helpers";

const COMPARE_VERSIONS = ["ls", "rs", "diff"] as const;

const getCompareContentValues = (
  ls: TranslationDialogFormProps["translations"][string],
  rs: TranslationDialogFormProps["translations"][string],
  version: (typeof COMPARE_VERSIONS)[number]
) => {
  const { gettext } = superdesk.localization;
  const dmp = new DiffMatchPatch();

  const result = getObjectKeys(FORM_FIELDS).reduce<
    Omit<FormInputProps, "images">
  >(
    (result, field) => {
      result[field] = "";
      return result;
    },
    { headline: "", headline_extended: "", body_html: "" }
  );

  switch (version) {
    case "ls":
      for (const key of getObjectKeys(FORM_FIELDS)) {
        result[key] = sanitizeHtml(ls.original[key]);
      }
      break;
    case "rs":
      for (const key of getObjectKeys(FORM_FIELDS)) {
        result[key] = sanitizeHtml(rs.original[key]);
      }
      break;
    case "diff":
      for (const key of getObjectKeys(FORM_FIELDS)) {
        const diffs = dmp.diff_main(
          sanitizeHtml(ls.original[key]),
          sanitizeHtml(rs.original[key])
        );
        result[key] = getPrettyDiffHtml({ diffs, gettext });
      }
  }

  return result;
};

const CompareContent = (props: Omit<FormInputProps, "images">) => (
  <>
    {getObjectEntries(FORM_FIELDS).map(([key, value]) => (
      <Spacer
        key={`compare-${key}`}
        gap="4"
        style={{ flexDirection: "column" }}
      >
        <Label text={value.label} style="hollow" />
        <p dangerouslySetInnerHTML={{ __html: props[key] }}></p>
      </Spacer>
    ))}
  </>
);

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
        <Container gap="large" direction="column">
          <div className="auto-translator__compare-accordion-settings-container">
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
              className="auto-translator__compare-accordion-content-container"
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
                    <p className="auto-translator__compare-accordion-content-header">
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
