"""Confirma que os artefatos que declaravam a mensagem de erro genérica
como requisito trazem a nota de superação por RF-PROV-01, sem apagar o
texto original."""

FEATURE_DIR = "adicionar-tela-streamlit-659323ea"


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
