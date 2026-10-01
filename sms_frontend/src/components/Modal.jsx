import { useCallback, useEffect } from 'react'

/**
 * A dialog with macOS-style window controls.
 *
 * The three dots carry the dialog's actions, so the footer no longer needs to
 * repeat Cancel and Save:
 *   red    closes the dialog
 *   yellow cancels the same way as red, but is the cancel affordance
 *   green  saves, by submitting the form the dialog contains
 *
 * Pass extra footer actions through `footer` for anything else, such as Delete.
 */
export default function Modal({
  title,
  children,
  onClose,
  onCancel,
  onSave,
  formId,
  saving = false,
  saveDisabled = false,
  footer,
}) {
  // onClose may be omitted by a caller; never let Escape throw.
  const close = typeof onClose === 'function' ? onClose : () => {}
  const cancel = typeof onCancel === 'function' ? onCancel : close

  const save = useCallback(() => {
    if (typeof onSave === 'function') {
      onSave()
      return
    }
    // No handler: submit the dialog's own form so HTML5 validation still applies.
    const form = formId ? document.getElementById(formId) : null
    if (form) {
      form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit'))
    }
  }, [onSave, formId])

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.stopPropagation()
        cancel()
        return
      }
      // Ctrl/Cmd + Enter saves, so it never depends on hitting a small dot.
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault()
        event.stopPropagation()
        if (!saving && !saveDisabled) save()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [cancel, save, saving, saveDisabled])

  return (
    <div className="modal-overlay" onClick={close}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === 'string' ? title : undefined}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div className="modal-lights" role="group" aria-label="Dialog actions">
            <button
              type="button"
              className="modal-light modal-light-close"
              onClick={close}
              aria-label="Close dialog"
              title="Close"
            />
            <button
              type="button"
              className="modal-light modal-light-min"
              onClick={cancel}
              aria-label="Cancel"
              title="Cancel"
            />
            <button
              type="button"
              className="modal-light modal-light-max"
              onClick={save}
              disabled={saving || saveDisabled}
              aria-label="Save"
              title={saveDisabled ? 'Nothing to save yet' : 'Save'}
            />
          </div>
          <h3 className="modal-title">{title}</h3>
          <span className="modal-header-spacer" aria-hidden="true" />
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
        <div className="modal-hint">
          <span className="modal-hint-item">red closes</span>
          <span className="modal-hint-item">yellow cancels</span>
          <span className="modal-hint-item">green saves</span>
          <span className="modal-hint-item">
            Esc cancels &middot; Ctrl/&#8984; + Enter saves
          </span>
        </div>
      </div>
    </div>
  )
}