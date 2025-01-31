import { useField } from "formik";
import * as React from "react";

type SelectProps = React.InputHTMLAttributes<HTMLSelectElement> & {
  label: string;
  field?: any;
  meta?: any;
  [key: string]: any;
};

export const Select = ({
  children,
  label,
  field,
  meta,
  ...props
}: SelectProps) => {
  return (
    <div className="sd-input sd-input--medium">
      <label className="sd-input__label" htmlFor={label} id={`${label}label`}>
        {label}
      </label>
      <div className="sd-input__input-container">
        <span className="sd-input__select-caret-wrapper">
          <select
            {...field}
            {...props}
            aria-describedby={`${label}label`}
            className="sd-input__select"
            id={label}
          >
            {children}
          </select>
        </span>
      </div>
      {meta?.error && <div className="sd-input__message-box">{meta.error}</div>}
    </div>
  );
};

type FormSelectProps = SelectProps & { name: string };

export const FormSelect = ({
  name,
  label,
  children,
  ...props
}: FormSelectProps) => {
  const [field, meta] = useField(name);

  return (
    <Select label={label} field={field} meta={meta} {...props}>
      {children}
    </Select>
  );
};
