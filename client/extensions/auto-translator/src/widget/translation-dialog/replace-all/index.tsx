import { Formik, FormikConfig, useFormikContext } from "formik";
import * as React from "react";
import { Button, ButtonGroup, Spacer } from "superdesk-ui-framework/react";
import { FormTextInput } from "../../../components";
import { typedSetFieldValue } from "../../../formik-utilties";
import { superdesk } from "../../../superdesk";
import { getObjectKeys } from "../../../utilities";
import { FORM_FIELDS, TranslationForm } from "../helpers";

type TranslationFormRef = {
  values: TranslationForm;
  setFieldValue: ReturnType<typeof typedSetFieldValue<TranslationForm>>;
};

type ReplaceAllFormProps = {
  search: string;
  replace: string;
};

/**
 * The pattern is matching the literal string value string.
 * This can be replaced with string.replaceAll once node is updated to 15+
 */
const getReplaceValue = (value: string, search: string, replace: string) => {
  const escapedSearch = search.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(escapedSearch, "gi");
  return value.replace(regex, replace);
};

const ReplaceAllForm = ({
  translationFormRef,
}: {
  translationFormRef: React.RefObject<TranslationFormRef>;
}) => {
  const { gettext } = superdesk.localization;

  const onSubmit: FormikConfig<ReplaceAllFormProps>["onSubmit"] = (
    values,
    _formikHelpers
  ) => {
    if (!translationFormRef.current || !values.search) return;

    for (const key of getObjectKeys(FORM_FIELDS)) {
      const value =
          translationFormRef.current.values.translations[
            translationFormRef.current.values.writethru
          ].manualTranslation[key],
        replaceValue = getReplaceValue(value, values.search, values.replace);

      translationFormRef.current.setFieldValue(
        `translations.${translationFormRef.current.values.writethru}.manualTranslation.${key}`,
        replaceValue
      );
    }
  };

  return (
    <Formik<ReplaceAllFormProps>
      initialValues={{ search: "", replace: "" }}
      onSubmit={onSubmit}
    >
      {({ submitForm, setFieldValue: formikSetFieldValue }) => {
        const setFieldValue =
          typedSetFieldValue<ReplaceAllFormProps>(formikSetFieldValue);

        const clearReplaceAll = () => {
          setFieldValue("search", "");
          setFieldValue("replace", "");
        };

        return (
          <Spacer h gap="16" alignItems="end" noWrap>
            <FormTextInput<ReplaceAllFormProps>
              name="search"
              label={gettext("Search")}
            />
            <FormTextInput<ReplaceAllFormProps>
              name="replace"
              label={gettext("Replace")}
            />
            <ButtonGroup align="inline">
              <Button
                text={gettext("Replace All")}
                type="primary"
                expand
                onClick={submitForm}
              />
              <Button
                text={gettext("Clear")}
                style="hollow"
                expand
                onClick={clearReplaceAll}
              />
            </ButtonGroup>
          </Spacer>
        );
      }}
    </Formik>
  );
};

export const ReplaceAll = () => {
  const { values, setFieldValue: formikSetFieldValue } =
      useFormikContext<TranslationForm>(),
    setFieldValue = typedSetFieldValue<TranslationForm>(formikSetFieldValue),
    translationFormRef = React.useRef<TranslationFormRef>({
      values,
      setFieldValue,
    });

  React.useEffect(() => {
    translationFormRef.current.values = values;
  }, [values]);

  return <ReplaceAllForm translationFormRef={translationFormRef} />;
};
