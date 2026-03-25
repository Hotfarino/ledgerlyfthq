const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("ledgerlift", {
  appName: "LedgerLift"
});
