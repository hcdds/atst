import { buildUploader } from '../lib/upload'

export default {
  name: 'uploadinput',

  props: {
    name: String,
    filename: {
      type: String,
    },
    objectName: {
      type: String,
    },
    initialErrors: {
      type: Boolean,
      default: false,
    },
    portfolioId: {
      type: String,
    },
  },

  data: function() {
    return {
      hasInitialData: !!this.filename,
      attachment: this.filename || null,
      changed: false,
      uploadError: false,
      sizeError: false,
      downloadLink: '',
    }
  },

  created: async function() {
    if (this.hasInitialData) {
      this.downloadLink = await this.getDownloadLink(
        this.filename,
        this.objectName
      )
    }
  },

  methods: {
    addAttachment: async function(e) {
      this.clearErrors()

      const file = e.target.files[0]
      if (file.size > 64000000) {
        this.sizeError = true
        return
      }

      const uploader = await this.getUploader()
      const response = await uploader.upload(file)
      if (response.ok) {
        this.attachment = e.target.value
        this.$refs.attachmentFilename.value = file.name
        this.$refs.attachmentObjectName.value = response.objectName
        this.$refs.attachmentInput.disabled = true

        this.downloadLink = await this.getDownloadLink(
          file.name,
          response.objectName
        )
      } else {
        this.uploadError = true
      }

      this.changed = true

      this.$parent.$emit('field-change')
    },
    removeAttachment: function(e) {
      e.preventDefault()
      this.attachment = null
      if (this.$refs.attachmentInput) {
        this.$refs.attachmentInput.value = null
        this.$refs.attachmentInput.disabled = false
      }
      this.clearErrors()
      this.changed = true

      this.$parent.$emit('field-change')
    },
    clearErrors: function() {
      this.uploadError = false
      this.sizeError = false
    },
    getUploader: async function() {
      return fetch(`/task_orders/${this.portfolioId}/upload_token`, {
        credentials: 'include',
      })
        .then(response => response.json())
        .then(({ token, objectName }) => buildUploader(token, objectName))
    },
    getDownloadLink: async function(filename, objectName) {
      const { downloadLink } = await fetch(
        `/task_orders/${
          this.portfolioId
        }/download_link?filename=${filename}&objectName=${objectName}`,
        { credentials: 'include' }
      ).then(r => r.json())
      return downloadLink
    },
  },

  computed: {
    baseName: function() {
      if (this.attachment) {
        return this.attachment.split(/[\\/]/).pop()
      }
    },
    hideInput: function() {
      return this.hasInitialData && !this.changed
    },
    showErrors: function() {
      return (
        (!this.changed && this.initialErrors) ||
        this.uploadError ||
        this.sizeError
      )
    },
    valid: function() {
      return !!this.attachment
    },
  },
}
