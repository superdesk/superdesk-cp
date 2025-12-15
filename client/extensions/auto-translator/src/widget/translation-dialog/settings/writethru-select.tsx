import { useFormikContext } from "formik";
import * as React from "react";
import { Option } from "superdesk-ui-framework/react";
import { FormSelect } from "../../../components";
import { superdesk } from "../../../superdesk";
import { getObjectEntries } from "../../../utilities";
import { TranslationForm } from "../helpers";

export const WritethruSelect = () => {
  const { gettext } = superdesk.localization;
  const { values } = useFormikContext<TranslationForm>();

  return (
    <FormSelect<TranslationForm> name="writethru" label={gettext("Writethru")}>
      <Option value="current">{values.translations.current.label}</Option>
      {getObjectEntries(values.translations)
        .filter(([k]) => k !== "current")
        .map(([k, v]) => (
          <Option value={k} key={`writethru-${k}`}>
            {v.label}
          </Option>
        ))}
    </FormSelect>
  );
};
