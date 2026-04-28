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
                  Tecnologia pensada para aproximar pessoas, facilitar a rotina
                  e transformar mobilidade em uma experiência mais inteligente.
                </p>
              </div>

              <div className="mb-5">
                <h3 className="fw-bold mb-3">Nossa proposta</h3>
                <p className="text-muted">
                  O Projeto Guarda-Chuva nasceu com a missão de criar soluções
                  inovadoras que unem praticidade, segurança e interação. Mais
                  do que um sistema tecnológico, ele representa uma nova forma
                  de conectar mobilidade e assistência no dia a dia.
                </p>
                <p className="text-muted mb-0">
                  Nosso foco está em oferecer uma experiência intuitiva para o
                  usuário, com recursos que tornam a utilização simples,
                  acessível e eficiente.
                </p>
              </div>

              <div className="row g-4 mb-5">
                <div className="col-12 col-md-4">
                  <div className="p-4 rounded-4 bg-light h-100">
                    <h5 className="fw-semibold">Facilidade</h5>
                    <p className="text-muted small mb-0">
                      Interfaces simples e acessíveis para que qualquer pessoa
                      possa utilizar a plataforma sem dificuldades.
                    </p>
                  </div>
                </div>

                <div className="col-12 col-md-4">
                  <div className="p-4 rounded-4 bg-light h-100">
                    <h5 className="fw-semibold">Conexão</h5>
                    <p className="text-muted small mb-0">
                      Recursos pensados para aproximar tecnologia e pessoas,
                      promovendo interações mais humanas e naturais.
                    </p>
                  </div>
                </div>

                <div className="col-12 col-md-4">
                  <div className="p-4 rounded-4 bg-light h-100">
                    <h5 className="fw-semibold">Inovação</h5>
                    <p className="text-muted small mb-0">
                      Evolução constante para entregar soluções modernas e
                      alinhadas às necessidades reais dos usuários.
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
                  Colocar o usuário no centro de cada decisão. Cada
                  funcionalidade foi planejada para gerar valor real, trazendo
                  praticidade, confiança e uma experiência agradável em todos os
                  momentos.
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
