import clsx from 'clsx'

export default function Input({
  label,
  error,
  helperText,
  className = '',
  ...props
}) {
  return (
    <div className={className}>
      {label && (
        <label
          htmlFor={props.id || props.name}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      <input
        className={clsx(
          'input-field',
          error && 'border-red-500 focus:ring-red-500'
        )}
        {...props}
      />

      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  )
}
