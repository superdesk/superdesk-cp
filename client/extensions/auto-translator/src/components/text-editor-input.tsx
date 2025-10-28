import { FieldHelperProps, FieldInputProps } from "formik";
import * as React from "react";
import { InputWrapper } from "superdesk-ui-framework/react";
import { RecursiveKeyOf, useFastField } from "../formik-utilties";
import { superdesk } from "../superdesk";

type TextEditorInputProps<T> = {
  label: string;
  field?: FieldInputProps<T>;
  helpers?: FieldHelperProps<T>;
  value?: string;
  wrapperValue?: string;
  readOnly?: boolean;
  onChange?: (newValue: string) => void;
  maxLength?: number;
};

export const TextEditorInput = <T,>({
  label,
  value,
  wrapperValue,
  readOnly,
  onChange,
  maxLength,
  field,
  helpers,
}: TextEditorInputProps<T>) => {
  const { stripHtmlTags } = superdesk.utilities;
  const { Editor3Html } = superdesk.components;
  const fieldValue = (field?.value as string) ?? value;

  return (
    <InputWrapper
      fullWidth
      boxedStyle
      boxedLable
      label={label}
      value={wrapperValue ?? stripHtmlTags(fieldValue).replace(/\n/g, "")}
      // max length must be provided to show a character count
      maxLength={maxLength}
    >
      <Editor3Html
        readOnly={!!readOnly}
        value={fieldValue}
        onChange={(newValue) => {
          if (onChange) onChange(newValue);
          else if (helpers) helpers.setValue(newValue as T);
        }}
      />
    </InputWrapper>
  );
};

type FormTextEditorInputProps<T> = Omit<
  TextEditorInputProps<T>,
  "value" | "wrapperValue" | "onChange"
> & {
  name: RecursiveKeyOf<T> & string;
  maxLength?: number;
};

export const FormTextEditorInput = <T,>({
  name,
  ...props
}: FormTextEditorInputProps<T>) => {
  const [field, _, helpers] = useFastField<T>({ name });

  return <TextEditorInput field={field} helpers={helpers} {...props} />;
};
