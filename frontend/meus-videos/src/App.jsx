import { BrowserRouter } from "react-router-dom";
import MainRoutes from "./MainRouter";
import Header from "./components/Header";
import Footer from "./components/Footer";

const App = () => {
  return (
    <BrowserRouter>
      <div className="d-flex flex-column min-vh-100">
        <Header />
        <MainRoutes />
        <Footer />
      </div>
    </BrowserRouter>
  );
};

export default App;
