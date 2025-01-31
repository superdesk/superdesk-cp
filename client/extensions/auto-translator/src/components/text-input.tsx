import { useField } from "formik";
import * as React from "react";

type TextInputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  field?: any;
  meta?: any;
  [key: string]: any;
};

export const TextInput = ({ label, field, meta, ...props }: TextInputProps) => {
  return (
    <div className="sd-input sd-input--medium sd-input--boxed-style sd-input--boxed-label">
      <label
        className="sd-input__label sd-input__label--boxed"
        htmlFor={label}
        id={`${label}label`}
      >
        {label}
      </label>
      <div className="sd-input__input-container">
        <input
          className="sd-input__input"
          {...field}
          {...props}
          type="text"
          aria-describedby={`${label}label`}
        />
      </div>
      {meta?.error && <div className="sd-input__message-box">{meta.error}</div>}
    </div>
  );
};

type FormTextInputProps = TextInputProps & { name: string };

export const FormTextInput = ({
  name,
  label,
  ...props
}: FormTextInputProps) => {
  const [field, meta] = useField(name);

  return <TextInput label={label} field={field} meta={meta} {...props} />;
};
