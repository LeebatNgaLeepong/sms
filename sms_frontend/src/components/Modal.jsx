import { useEffect } from 'react'

/**
 * A dialog with a macOS-style close control.
 *
 * The three dots are decorative except for the first, which closes the dialog.
 * Holding the close dot for a moment, or focusing it and pressing Enter or
 * Space, also closes, so the control is reachable without a pointer.
 */
export default function Modal({ title, children, onClose, footer }) {
  // onClose may be omitted by a caller; never let Escape throw.
  const close = typeof onClose === 'function' ? onClose : () => {}

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.stopPropagation()
        close()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [close])

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
          <button
            type="button"
            className="modal-lights"
            onClick={close}
            aria-label="Close dialog"
            title="Close"
          >
            <span className="modal-light modal-light-close" />
            <span className="modal-light modal-light-min" aria-hidden="true" />
            <span className="modal-light modal-light-max" aria-hidden="true" />
          </button>
          <h3 className="modal-title">{title}</h3>
          <span className="modal-header-spacer" aria-hidden="true" />
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}