import DiffMatchPatch from "diff-match-patch";
import { useFormikContext } from "formik";
import * as React from "react";
import { ISuperdesk } from "superdesk-api";
import {
  Label,
  Option,
  Spacer,
  SpacerBlock,
  Text,
} from "superdesk-ui-framework/react";
import { Select } from "../../../components";
import { useSuperdesk } from "../../../context";
import { getObjectEntries, getObjectKeys } from "../../../utilities";
import {
  FORM_FIELDS,
  FORM_FIELDS_INITIAL_VALUES,
  FormInputProps,
  TranslationForm,
} from "../helpers";
import { getPrettyDiffHtml, sanitizeHtml } from "./helpers";

const COMPARE_VERSIONS = ["ls", "rs", "diff"] as const;

const getCompareContentValues = (
  {
    ls,
    rs,
    version,
  }: {
    ls: TranslationForm["translations"][string];
    rs: TranslationForm["translations"][string];
    version: (typeof COMPARE_VERSIONS)[number];
  },
  { localization: { gettext } }: ISuperdesk
) => {
  const dmp = new DiffMatchPatch(),
    result = getObjectKeys(FORM_FIELDS).reduce<Omit<FormInputProps, "images">>(
      (result, field) => {
        result[field] = "";
        return result;
      },
      { ...FORM_FIELDS_INITIAL_VALUES }
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

const CompareContent = (props: Omit<FormInputProps, "images">) => {
  const superdesk = useSuperdesk();

  return (
    <>
      {getObjectEntries(FORM_FIELDS).map(([key, value]) => (
        <Spacer key={`compare-${key}`} v gap="8" noWrap>
          <Label text={value.getLabel(superdesk)} style="hollow" />
          <p dangerouslySetInnerHTML={{ __html: props[key] }}></p>
        </Spacer>
      ))}
    </>
  );
};

export const Compare = () => {
  const superdesk = useSuperdesk(),
    { gettext } = superdesk.localization,
    { values } = useFormikContext<TranslationForm>(),
    [compareLeft, setCompareLeft] = React.useState<
      TranslationForm["writethru"]
    >(getObjectKeys(values.translations)?.[0] ?? ""),
    [compareRight, setCompareRight] = React.useState<
      TranslationForm["writethru"]
    >(getObjectKeys(values.translations)?.[0] ?? "");

  return (
    <>
      <Spacer h gap="16" noWrap style={{ width: "50%" }}>
        {(
          [
            { value: compareLeft, setter: setCompareLeft },
            { value: compareRight, setter: setCompareRight },
          ] as const
        ).map(({ value, setter }, i) => (
          <Select
            key={`compare-select-${i}`}
            value={value}
            onChange={(newValue) => {
              setter(newValue);
            }}
            label={gettext("Writethru {{n}}", { n: i + 1 })}
          >
            <Option value="current">{values.translations.current.label}</Option>
            {getObjectEntries(values.translations)
              .filter(([k]) => k !== "current")
              .map(([k, v]) => (
                <Option value={k} key={`${i}-writethru-${k}`}>
                  {v.label}
                </Option>
              ))}
          </Select>
        ))}
      </Spacer>
      <SpacerBlock v gap="16" />
      {compareLeft && compareRight && (
        <Spacer h gap="16" alignItems="start" noWrap>
          {COMPARE_VERSIONS.map((version, i) => {
            const header =
              version === "diff"
                ? gettext("Difference (Diff)")
                : gettext("Writethru {{n}}", { n: i + 1 });

            return (
              <Spacer key={version} v gap="16" alignItems="center" noWrap>
                <Text weight="medium" size="medium">
                  {header}
                </Text>
                <CompareContent
                  {...getCompareContentValues(
                    {
                      ls: values.translations[compareLeft],
                      rs: values.translations[compareRight],
                      version,
                    },
                    superdesk
                  )}
                />
              </Spacer>
            );
          })}
        </Spacer>
      )}
    </>
  );
};
