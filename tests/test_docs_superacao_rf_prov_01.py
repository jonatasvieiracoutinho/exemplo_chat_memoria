"""Confirma que os artefatos que declaravam a mensagem de erro genérica
como requisito trazem a nota de superação por RF-PROV-01, sem apagar o
texto original."""

FEATURE_DIR = "adicionar-tela-streamlit-659323ea"
PRD_PATH = "docs/prds/PRD-2026-09-18-adicionar-front-end-em-streamlit-com-scripts-de-inicializacao-automatica.md"


def _ler(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def test_spec_da_feature_streamlit_traz_nota_de_superacao():
    conteudo = _ler(f".specs/features/{FEATURE_DIR}/spec.md")
    assert "RF-PROV-01" in conteudo
    assert "erro amigável sem expor chave, stack trace ou detalhes internos" in conteudo


def test_design_da_feature_streamlit_traz_nota_de_superacao():
    conteudo = _ler(f".specs/features/{FEATURE_DIR}/design.md")
    assert "RF-PROV-01" in conteudo
    assert "mensagem amigável fixa, sem chave/stack/detalhes" in conteudo


def test_validation_da_feature_streamlit_traz_nota_de_superacao():
    conteudo = _ler(f".specs/features/{FEATURE_DIR}/validation.md")
    assert "RF-PROV-01" in conteudo
    assert "MENSAGEM_ERRO_AMIGAVEL" in conteudo


def test_prd_streamlit_traz_nota_de_superacao_no_ca07():
    conteudo = _ler(PRD_PATH)
    assert "RF-PROV-01" in conteudo
    assert "CA-07" in conteudo
    assert "Erros da API são exibidos de forma amigável, sem vazar chave nem detalhes" in conteudo


def test_env_example_documenta_bloco_de_perfis():
    conteudo = _ler("env.example")
    assert "PERFIS=Groq,Ollama local" in conteudo
    assert "PERFIL_GROQ_BASE_URL" in conteudo
    assert "PERFIL_GROQ_API_KEY" in conteudo
    assert "PERFIL_GROQ_MODEL" in conteudo
    assert "obrigatória em todo Perfil" in conteudo
