const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("ledgerlyfthq", {
  appName: "ledgerlyftHQ"
});
