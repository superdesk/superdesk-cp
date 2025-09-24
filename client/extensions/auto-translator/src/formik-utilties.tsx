// formik setFieldValue currently is not type-safe
// type-safe implementation of setFieldValue solution: https://github.com/jaredpalmer/formik/issues/1388
import {
  FieldHelperProps,
  FormikHelpers,
  useField,
  useFormikContext,
} from "formik";
import * as React from "react";

type TerminalType =
  | string
  | number
  | bigint
  | boolean
  | null
  | undefined
  | Set<any>
  | Date;

type IsAny<T> = unknown extends T
  ? [keyof T] extends [never]
    ? false
    : true
  : false;

/**
 * Deep nested keys of an interface with dot syntax
 *
 * @example
 * type t = RecursiveKeyOf<{a: {b: {c: string}}> // => 'a' | 'a.b' | 'a.b.c'
 */
export type RecursiveKeyOf<
  T,
  Prefix extends string = never
> = T extends TerminalType
  ? never
  : IsAny<T> extends true
  ? never
  : T extends any[]
  ? `${Prefix}.${number}` | RecursiveKeyOf<T[number], `${Prefix}.${number}`>
  : {
      [K in keyof T & string]: [Prefix] extends [never]
        ? K | RecursiveKeyOf<T[K], K>
        : `${Prefix}.${K}` | RecursiveKeyOf<T[K], `${Prefix}.${K}`>;
    }[keyof T & string];

type ParseInt<T extends string> = T extends `${infer Int extends number}`
  ? Int
  : never;

/**
 * Get the type of a nested property with dot syntax
 *
 * Basically the inverse of `RecursiveKeyOf`
 *
 * @example
 * type t = DeepPropertyType<{a: {b: {c: string}}}, 'a.b.c'> // => string
 */
export type DeepPropertyType<
  T,
  P extends RecursiveKeyOf<T>,
  TT = Exclude<T, undefined>
> = P extends `${infer Prefix}.${infer Rest}`
  ? Prefix extends keyof TT
    ? Rest extends RecursiveKeyOf<TT[Prefix]>
      ? DeepPropertyType<TT[Prefix], Rest>
      : ParseInt<Rest> extends number
      ? TT[Prefix] extends (infer ArrayType)[]
        ? Rest extends `${number}.${infer DeepRest extends RecursiveKeyOf<ArrayType>}`
          ? DeepPropertyType<ArrayType, DeepRest>
          : ArrayType
        : never
      : never
    : never
  : P extends keyof TT
  ? TT[P]
  : never;

export const typedSetFieldValue =
  <T,>(setFieldValue: FormikHelpers<T>["setFieldValue"]) =>
  <Key extends RecursiveKeyOf<T>>(
    field: Key,
    value: DeepPropertyType<T, Key>,
    shouldValidate?: boolean
  ) =>
    setFieldValue(field, value, shouldValidate);

// formik useField.helpers returns new reference on any form update
// useFormikContext provides helpers but does not return new references https://github.com/jaredpalmer/formik/issues/2268
type HelperArgs<T extends (...args: any) => any> = Parameters<T> extends [
  string,
  ...infer Args
]
  ? Args
  : never;

export const useFastField = <T,>(...args: Parameters<typeof useField<T>>) => {
  const [field, meta] = useField<T>(...args);
  const { setFieldTouched, setFieldValue, setFieldError } =
    useFormikContext<T>();
  const helpers = React.useMemo<FieldHelperProps<T>>(
    () => ({
      setValue: (...args: HelperArgs<typeof setFieldValue>) =>
        setFieldValue(field.name, ...args),
      setTouched: (...args: HelperArgs<typeof setFieldTouched>) =>
        setFieldTouched(field.name, ...args),
      setError: (...args: HelperArgs<typeof setFieldError>) =>
        setFieldError(field.name, ...args),
    }),
    [setFieldTouched, setFieldValue, setFieldError, field.name]
  );

  return [field, meta, helpers] as const;
};
