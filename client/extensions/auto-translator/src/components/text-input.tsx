import { FieldHelperProps, FieldInputProps, FieldMetaProps } from "formik";
import * as React from "react";
import { Input } from "superdesk-ui-framework/react";
import { RecursiveKeyOf, useFastField } from "../formik-utilties";

type TextInputProps<T> = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  field?: FieldInputProps<T>;
  meta?: FieldMetaProps<T>;
  helpers?: FieldHelperProps<T>;
  readonly?: boolean;
  onChange?: (newValue: string) => void;
};

export const TextInput = <T,>({
  label,
  field,
  meta,
  helpers,
  onChange,
  ...props
}: TextInputProps<T>) => (
  <Input
    {...field}
    {...props}
    type="text"
    label={label}
    boxedLable
    boxedStyle
    size="medium"
    value={field?.value as string}
    onChange={(newValue) => {
      if (onChange) onChange(newValue);
      else if (helpers) helpers.setValue(newValue as T);
    }}
    error={meta?.error ?? undefined}
  />
);

type FormTextInputProps<T> = Omit<TextInputProps<T>, "name"> & {
  name: RecursiveKeyOf<T> & string;
};

export const FormTextInput = <T,>({
  name,
  label,
  ...props
}: FormTextInputProps<T>) => {
  const [field, meta, helpers] = useFastField<T>({ name });

  return (
    <TextInput<T>
      {...props}
      label={label}
      field={field}
      meta={meta}
      helpers={helpers}
    />
  );
};
