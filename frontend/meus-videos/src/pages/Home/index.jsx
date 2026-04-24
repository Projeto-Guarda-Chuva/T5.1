import { Link } from "react-router-dom";
import { ROUTES } from "../../utils/routes";

const Home = () => {
  return (
    <div>
      <h1>Página Inicial</h1>
      <Link to={ROUTES.LOGIN}>Ir para Login</Link>
    </div>
  );
};

export default Home;
