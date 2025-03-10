import {
  FieldHelperProps,
  FieldInputProps,
  FieldMetaProps,
  useField,
} from "formik";
import * as React from "react";
import { Select as SuperdeskSelect } from "superdesk-ui-framework/react";
import { RecursiveKeyOf } from "../formik-utilties";

type SelectProps<T> = Omit<
  React.InputHTMLAttributes<HTMLSelectElement>,
  "onChange"
> & {
  label: string;
  field?: FieldInputProps<T>;
  meta?: FieldMetaProps<T>;
  helpers?: FieldHelperProps<T>;
  value?: string;
  onChange?: (newValue: string) => void;
  [key: string]: any;
};

export const Select = <T,>({
  children,
  label,
  field,
  meta,
  helpers,
  value,
  onChange,
  ...props
}: SelectProps<T>) => {
  return (
    <SuperdeskSelect
      {...field}
      {...props}
      label={label}
      value={(field?.value as string) || (value as string)}
      onChange={(newValue) => {
        if (onChange) onChange(newValue);
        else if (helpers) helpers.setValue(newValue as T);
      }}
      error={meta?.error ? meta.error : undefined}
    >
      {children}
    </SuperdeskSelect>
  );
};

type FormSelectProps<T> = Omit<SelectProps<T>, "name"> & {
  name: RecursiveKeyOf<T> & string;
};

export const FormSelect = <T,>({
  name,
  label,
  children,
  ...props
}: FormSelectProps<T>) => {
  const [field, meta, helpers] = useField(name);

  return (
    <Select
      {...props}
      label={label}
      field={field}
      meta={meta}
      helpers={helpers}
    >
      {children}
    </Select>
  );
};
