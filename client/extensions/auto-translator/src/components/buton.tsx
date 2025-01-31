import * as React from "react";
import {
  Spinner,
  Button as SuperdeskButton,
} from "superdesk-ui-framework/react";

type SuperdeskButtonProps = React.ComponentProps<typeof SuperdeskButton>;

type SuperdeskButtonStyles =
  | Exclude<
      SuperdeskButtonProps[keyof Pick<
        SuperdeskButtonProps,
        "size" | "type" | "style" | "theme"
      >],
      undefined | "light"
    >
  | "expand"
  | "disabled"
  | "iconOnly"
  | "iconOnlyCircle";

const superdeskButtonClasses: Record<SuperdeskButtonStyles, string> = {
  expand: "btn--expanded",
  small: "btn--small",
  normal: "btn--normal",
  large: "btn--large",
  default: "btn--default",
  primary: "btn--primary",
  success: "btn--success",
  warning: "btn--warning",
  alert: "btn--alert",
  highlight: "btn--highlight",
  "sd-green": "btn--sd-green",
  filled: "btn--filled",
  hollow: "btn--hollow",
  "text-only": "btn--text-only",
  disabled: "btn--disabled",
  iconOnly: "btn--icon-only",
  dark: "btn--ui-dark",
  iconOnlyCircle: "btn--icon-only-circle",
};

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  label: React.ReactNode;
  superdeskButtonProps?: Partial<SuperdeskButtonProps>;
};

export const Button = ({
  label,
  superdeskButtonProps,
  className,
  ...props
}: ButtonProps) => {
  const classes = ["btn"];

  if (superdeskButtonProps?.expand) classes.push(superdeskButtonClasses.expand);
  if (superdeskButtonProps?.size)
    classes.push(superdeskButtonClasses[superdeskButtonProps.size]);
  if (superdeskButtonProps?.type)
    classes.push(superdeskButtonClasses[superdeskButtonProps.type]);
  if (superdeskButtonProps?.style)
    classes.push(superdeskButtonClasses[superdeskButtonProps.style]);
  if (superdeskButtonProps?.disabled)
    classes.push(superdeskButtonClasses.disabled);
  if (superdeskButtonProps?.iconOnly)
    classes.push(superdeskButtonClasses.iconOnly);
  if (superdeskButtonProps?.theme === "dark")
    classes.push(superdeskButtonClasses.dark);
  if (superdeskButtonProps?.shape === "round" && superdeskButtonProps.iconOnly)
    classes.push(superdeskButtonClasses.iconOnlyCircle);

  if (className) classes.push(className);

  return (
    <button
      type="button"
      className={classes.join(" ")}
      disabled={
        superdeskButtonProps?.disabled || superdeskButtonProps?.isLoading
      }
      {...props}
    >
      {superdeskButtonProps?.isLoading ? <Spinner size="mini" /> : label}
    </button>
  );
};
