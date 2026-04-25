import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AuthProvider } from "./app/AuthContext";
import { ThemeProvider } from "./app/ThemeContext";
import { ToastProvider } from "./components/ui";
import { AppRouter } from "./app/router";
import "./styles/global.css";

const rootEl = document.getElementById("root");
if (!rootEl) throw new Error("#root element not found");

createRoot(rootEl).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <AppRouter />
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
);
