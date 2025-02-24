import {
  FieldHelperProps,
  FieldInputProps,
  FieldMetaProps,
  useField,
} from "formik";
import * as React from "react";
import { Input } from "superdesk-ui-framework/react";
import { RecursiveKeyOf } from "../formik-utilties";

type TextInputProps<T> = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  field: FieldInputProps<T>;
  meta: FieldMetaProps<T>;
  helpers: FieldHelperProps<T>;
  [key: string]: any;
};

export const TextInput = <T,>({
  label,
  field,
  meta,
  helpers,
  ...props
}: TextInputProps<T>) => {
  return (
    <Input
      {...field}
      {...props}
      type="text"
      label={label}
      boxedLable={true}
      boxedStyle={true}
      size="medium"
      value={field?.value as string}
      onChange={(newValue) => {
        helpers.setValue(newValue as T);
      }}
      error={meta?.error ? meta.error : undefined}
    />
  );
};

type FormTextInputProps<T> = Omit<TextInputProps<T>, "name"> & {
  name: RecursiveKeyOf<T> & string;
};

export const FormTextInput = <T,>({
  name,
  label,
  ...props
}: FormTextInputProps<T>) => {
  const [field, meta, helpers] = useField<T>(name);

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
