import { Link } from "react-router-dom";
import { ROUTES } from "../../utils/routes";

export default function Terms() {
  return (
    <div className="container my-5 flex-grow-1">
      <h1 className="mb-4 text-primary">Termos de Uso</h1>
      <div className="card shadow-sm border-0">
        <div className="card-body p-4">
          <h5 className="card-title fw-bold">1. Aceitação dos Termos</h5>
          <p className="card-text text-muted mb-4">
            Ao acessar e utilizar a aplicação "Meus Vídeos", você concorda em
            cumprir e ficar vinculado a estes Termos de Uso.
          </p>

          <h5 className="card-title fw-bold">2. Uso de Imagens e Mídia</h5>
          <p className="card-text text-muted mb-4">
            Todo o conteúdo de mídia, incluindo imagens, vídeos e logotipos
            inseridos ou gerados pelo serviço, é de responsabilidade do usuário.
            É estritamente proibida a reprodução, distribuição, modificação ou
            uso não autorizado das imagens pertencentes a terceiros sem o devido
            consentimento prévio e por escrito dos detentores dos direitos
            autorais.
          </p>

          <h5 className="card-title fw-bold">3. Propriedade Intelectual</h5>
          <p className="card-text text-muted mb-4">
            Os direitos autorais, marcas registradas e todos os outros direitos
            de propriedade intelectual sobre o software e o design da plataforma
            permanecem sob a titularidade exclusiva de seus respectivos
            criadores.
          </p>

          <h5 className="card-title fw-bold">4. Modificações dos Termos</h5>
          <p className="card-text text-muted mb-4">
            Reservamo-nos o direito de alterar ou substituir estes Termos a
            qualquer momento. Quaisquer alterações entrarão em vigor
            imediatamente após a publicação nesta página.
          </p>

          <div className="mt-4 pt-3 border-top">
            <Link to={ROUTES.LOGIN} className="btn btn-outline-primary">
              Voltar
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
