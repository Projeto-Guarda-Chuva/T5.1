import { Link } from "react-router-dom";
import { ROUTES } from "../../utils/routes";

const About = () => {
  return (
    <div className="container py-4 py-md-5">
      <div className="row justify-content-center">
        <div className="col-12 col-lg-9">
          <div
            className="card shadow-sm border-0"
            style={{ borderRadius: "20px" }}
          >
            <div className="card-body p-4 p-md-5">
              <div className="text-center mb-5">
                <h1 className="fw-bold display-6">
                  Sobre o Projeto Guarda-Chuva
                </h1>
                <p className="text-muted mt-3 mb-0">
                  Uma interação mágica e surpreendente entre você e a
                  inteligência artificial.
                </p>
              </div>

              <div className="mb-5">
                <h3 className="fw-bold mb-3">Nossa proposta</h3>
                <p className="text-muted">
                  Imagine um guarda-chuva robótico que se move como uma
                  água-viva. Equipado com uma câmera e IA, ele reconhece sua
                  presença e reage aos seus movimentos, criando uma dança lúdica
                  entre pessoa e máquina. Além da interação, o sistema grava
                  esse momento único para você!
                </p>
              </div>

              <div className="row g-4 mb-5">
                <div className="col-12 col-md-4">
                  <div className="p-4 rounded-4 bg-light h-100">
                    <h5 className="fw-semibold">Interação</h5>
                    <p className="text-muted small mb-0">
                      A tecnologia responde diretamente à sua presença com
                      movimentos guiados por IA.
                    </p>
                  </div>
                </div>

                <div className="col-12 col-md-4">
                  <div className="p-4 rounded-4 bg-light h-100">
                    <h5 className="fw-semibold">Arte e Design</h5>
                    <p className="text-muted small mb-0">
                      Um visual lúdico inspirado em águas-vivas, misturando
                      robótica com formas da natureza.
                    </p>
                  </div>
                </div>

                <div className="col-12 col-md-4">
                  <div className="p-4 rounded-4 bg-light h-100">
                    <h5 className="fw-semibold">Recordação</h5>
                    <p className="text-muted small mb-0">
                      O guarda-chuva interage e captura em vídeo para você rever
                      e compartilhar.
                    </p>
                  </div>
                </div>
              </div>

              <div
                className="rounded-4 p-4 mb-5"
                style={{
                  background:
                    "linear-gradient(135deg, rgba(13,110,253,0.08), rgba(108,117,125,0.08))",
                }}
              >
                <h3 className="fw-bold mb-3">Nosso compromisso</h3>
                <p className="text-muted mb-0">
                  Proporcionar um momento inesquecível de conexão. Queremos
                  mostrar que a tecnologia pode ser divertida, orgânica e
                  surpreendente, transformando o simples ato de parar sob um
                  guarda-chuva em uma experiência memorável.
                </p>
              </div>

              <div className="text-center">
                <Link to={ROUTES.LOGIN} className="btn btn-primary px-4">
                  Começar agora
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;
