export const emitFieldChange = (el, data) => {
  el.$root.$emit('field-change', {
    ...data,
    parent_uid: el.$parent && el.$parent._uid,
  })
}

export const emitFieldMount = (el, data) => {
  el.$root.$emit('field-mount', {
    ...data,
    parent_uid: el.$parent && el.$parent._uid,
  })
}
