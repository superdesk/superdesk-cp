import { useField } from "formik";
import * as React from "react";
import { InputWrapper } from "superdesk-ui-framework/react";
import { superdesk } from "../superdesk";

type TextEditorInputProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  [key: string]: any;
};

export const TextEditorInput = ({
  label,
  value,
  onChange,
  ...props
}: TextEditorInputProps) => {
  const { Editor3Html } = superdesk.components;

  return (
    <InputWrapper label={label} fullWidth boxedStyle boxedLable>
      <Editor3Html
        key={label}
        readOnly={false}
        value={value}
        onChange={onChange}
        {...props}
      />
    </InputWrapper>
  );
};

type FormTextEditorInputProps = Omit<
  TextEditorInputProps,
  "value" | "onChange"
> & { name: string };

export const FormTextEditorInput = ({
  label,
  name,
  ...props
}: FormTextEditorInputProps) => {
  // @ts-ignore
  const [field, meta, helpers] = useField(name);
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
