const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('api', {
  saveConfig: (data) => ipcRenderer.invoke('save-config', data),
  getConfig: () => ipcRenderer.invoke('get-config', data)
})
