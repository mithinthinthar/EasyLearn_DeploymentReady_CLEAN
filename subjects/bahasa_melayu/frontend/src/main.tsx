import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "./app/App";
import "./styles/global.css";
import { AuthProvider } from "./context/AuthContext";
import { installBmActivityTracker } from "./services/platformActivity";

installBmActivityTracker();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <HashRouter>
    <AuthProvider>
      <App />
    </AuthProvider>
  </HashRouter>
);
