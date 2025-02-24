import { useField } from "formik";
import * as React from "react";
import { InputWrapper } from "superdesk-ui-framework/react";
import { RecursiveKeyOf } from "../formik-utilties";
import { superdesk } from "../superdesk";

type TextEditorInputProps = {
  label: string;
  value: string;
  readOnly: boolean;
  onChange: (value: string) => void;
};

export const TextEditorInput = ({
  label,
  value,
  readOnly,
  onChange,
  ...props
}: TextEditorInputProps) => {
  const { Editor3Html } = superdesk.components;

  return (
    <InputWrapper label={label} fullWidth boxedStyle boxedLable>
      <Editor3Html
        readOnly={readOnly}
        value={value}
        onChange={onChange}
        {...props}
      />
    </InputWrapper>
  );
};

type FormTextEditorInputProps<T> = Omit<
  TextEditorInputProps,
  "value" | "onChange"
> & { name: RecursiveKeyOf<T> & string };

export const FormTextEditorInput = <T,>({
  label,
  name,
  ...props
}: FormTextEditorInputProps<T>) => {
  const [field, _meta, helpers] = useField(name);
  const { setValue } = helpers;

  return (
    <TextEditorInput
      label={label}
      value={field.value}
      onChange={(value) => {
        setValue(value);
      }}
      {...props}
    />
  );
};
