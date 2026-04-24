export default function Footer() {
  return (
    <footer className="bg-white text-center py-3 mt-auto border-top">
      <div className="container">
        <span className="text-muted small">
          © {new Date().getFullYear()} Meus Vídeos. Todos os direitos
          reservados.
        </span>
      </div>
    </footer>
  );
}
