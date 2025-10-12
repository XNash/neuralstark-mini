import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Wait for DOM to be fully ready
function initApp() {
  const rootElement = document.getElementById("root");
  
  if (!rootElement) {
    console.error("CRITICAL: Root element #root not found in DOM!");
    return;
  }
  
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

// Ensure DOM is ready before initializing
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initApp);
} else {
  // DOM is already ready, but wait a tick to ensure all scripts have loaded
  setTimeout(initApp, 0);
}
