// Preload script for Electron security
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
    onProgressUpdate: (callback) => {
        ipcRenderer.on('export-progress', (event, data) => callback(data));
    }
});
