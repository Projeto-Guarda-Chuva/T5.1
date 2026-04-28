import { useState } from "react";

const StatusGravacao = () => {
  const [status, setStatus] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!status) {
      alert("Por favor, selecione uma opção!");
      return;
    }
    
    console.log("Status selecionado:", status);
    alert(`Opção "${status}" registrada! Em breve redirecionaremos para Meus Vídeos.`);
  };

  return (
    <div className="container mt-5">
      <h2>Informações da Gravação</h2>
      <p>Para localizarmos seu vídeo, precisamos saber do seu status:</p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-check mb-2">
          <input 
            className="form-check-input" 
            type="radio" 
            name="statusGravacao" 
            id="jaParticipei" 
            value="ja_participei"
            onChange={(e) => setStatus(e.target.value)}
          />
          <label className="form-check-label" htmlFor="jaParticipei">
            Já participei da gravação
          </label>
        </div>
        
        <div className="form-check mb-4">
          <input 
            className="form-check-input" 
            type="radio" 
            name="statusGravacao" 
            id="aindaParticiparei" 
            value="ainda_participarei"
            onChange={(e) => setStatus(e.target.value)}
          />
          <label className="form-check-label" htmlFor="aindaParticiparei">
            Ainda participarei da gravação
          </label>
        </div>

        <button type="submit" className="btn btn-primary">
          Confirmar e Acessar Meus Vídeos
        </button>
      </form>
    </div>
  );
};

export default StatusGravacao;