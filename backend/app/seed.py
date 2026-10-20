"""Carga inicial do catálogo (conteúdo de partida, ainda NÃO validado por agrônomo) e admin."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import Disease, User
from .security import hash_password

# (nome, científico, cultura, severidade, descrição, causas, cuidados, observações)
DISEASES = [
 ("Ferrugem-do-cafeeiro", "Hemileia vastatrix", "Café", "alta", "Manchas amarelo-alaranjadas na face superior e pó alaranjado na inferior, com desfolha severa.", "Fungo favorecido por temperaturas amenas, alta umidade e carga pendente elevada.", "Monitorar a lavoura, evitar adensamento, manter nutrição equilibrada e fazer podas de arejamento.", "Principal doença do cafeeiro; a desfolha reduz a produtividade da safra seguinte."),
 ("Cercosporiose do cafeeiro", "Cercospora coffeicola", "Café", "moderada", "Manchas circulares pardo-escuras com centro mais claro e halo amarelado, visíveis nos dois lados da folha.", "Associada a desequilíbrio nutricional, estresse hídrico e insolação excessiva.", "Corrigir a adubação, manter o solo coberto e evitar estresse hídrico.", "Também atinge frutos, provocando maturação precoce."),
 ("Mancha aureolada", "Pseudomonas syringae pv. garcae", "Café", "alta", "Lesões escuras com halo amarelo em folhas e ramos jovens, comuns após ventos e chuvas.", "Vento acompanhado de chuva, granizo, ferimentos por tratos culturais e produção de mudas em viveiro.", "Adoção de quebra-ventos, evitar ferimentos desnecessários, produzir mudas sadias e evitar podas severas em períodos chuvosos com vento.", "Doença bacteriana típica de regiões de altitude com ventos frequentes, como parte do Alto Paranaíba."),
 ("Phoma", "Phoma costarricensis", "Café", "moderada", "Manchas escuras em folhas, ramos e flores novas, associadas a frio, umidade e vento.", "Clima frio e úmido com ventos, principalmente em altitudes elevadas.", "Quebra-ventos, nutrição adequada e monitoramento em períodos frios e úmidos.", "Ataca brotações e pode causar seca de ponteiros."),
 ("Ascochiose", "Ascochyta tarda", "Café", "baixa", "Manchas claras com anéis concêntricos em folhas jovens, em locais frios e úmidos.", "Baixas temperaturas e alta umidade em lavouras de altitude.", "Monitorar a lavoura e favorecer a ventilação entre as plantas.", "Costuma ter baixo impacto quando as condições melhoram."),
 ("Antracnose", "Colletotrichum spp.", "Soja", "moderada", "Lesões escuras e deprimidas nas nervuras, haste e vagens, com escurecimento e morte de tecidos.", "Fungo transmitido por sementes e restos culturais, favorecido por alta umidade.", "Usar sementes sadias, fazer rotação de culturas e manejar a palhada.", "Pode causar morte de plântulas e vagens chochas."),
 ("Ferrugem-asiática", "Phakopsora pachyrhizi", "Soja", "alta", "Pequenas pústulas na face inferior das folhas, com amarelecimento e desfolha precoce.", "Fungo disseminado pelo vento e favorecido por molhamento foliar prolongado.", "Respeitar o vazio sanitário, eliminar plantas voluntárias e monitorar a lavoura com frequência.", "Pode causar perdas expressivas se não for detectada cedo."),
 ("Mancha-alvo", "Corynespora cassiicola", "Soja", "moderada", "Lesões circulares pardas com anéis concêntricos em folhas, hastes e vagens.", "Fungo que sobrevive em restos culturais, favorecido por umidade.", "Rotação de culturas, manejo da palhada e monitoramento.", "Pode causar desfolha em ataques intensos."),
 ("Oídio", "Erysiphe diffusa", "Soja", "baixa", "Pó esbranquiçado sobre folhas e hastes, mais comum em clima ameno e seco.", "Fungo favorecido por temperaturas amenas e baixa umidade do ar.", "Monitorar a lavoura e preferir cultivares menos suscetíveis.", "Geralmente de menor impacto, mas pode reduzir a fotossíntese."),
 ("Cercosporiose do milho", "Cercospora zeae-maydis", "Milho", "moderada", "Lesões retangulares estreitas, com bordas bem definidas e paralelas às nervuras, formando estrias na folha.", "Sobrevive na palhada e é favorecida por alta umidade e plantio direto sobre milho.", "Rotação de culturas, manejo da palhada e escolha de híbridos tolerantes.", "Pode comprometer o enchimento de grãos."),
 ("Mancha-branca", "Pantoea ananatis", "Milho", "moderada", "Pequenas manchas claras e alongadas nas folhas, que podem secar o tecido.", "Favorecida por noites úmidas e temperaturas amenas.", "Híbridos tolerantes, época de plantio adequada e monitoramento.", "Surge primeiro nas folhas mais velhas."),
 ("Ferrugem-polissora", "Puccinia polysora", "Milho", "alta", "Pústulas alaranjadas e pulverulentas dos dois lados da folha, com secamento precoce.", "Fungo disseminado pelo vento, favorecido por calor e alta umidade.", "Híbridos tolerantes, escalonar plantios e monitorar a lavoura.", "Ataques precoces podem causar perdas de produtividade."),
 ("Helmintosporiose", "Exserohilum turcicum", "Milho", "moderada", "Lesões alongadas em forma de charuto, de cor acinzentada a parda.", "Fungo favorecido por umidade e temperaturas moderadas.", "Rotação de culturas, manejo da palhada e híbridos tolerantes.", "Mais severa quando ocorre antes do florescimento."),
 ("Mancha-de-bipolaris", "Bipolaris maydis", "Milho", "baixa", "Manchas ovais pardas, de bordas escuras, que podem se juntar nas folhas.", "Calor e umidade elevados, com inóculo na palhada.", "Rotação de culturas e manejo adequado dos restos culturais.", "Costuma ter baixa incidência em híbridos atuais."),
]


def run(db: Session) -> None:
    if not db.scalar(select(Disease.id).limit(1)):
        for n, s, c, sev, desc, causes, care, notes in DISEASES:
            db.add(Disease(name=n, scientific_name=s, crop=c, severity=sev, description=desc,
                           causes=causes, care=care, notes=notes))
    if not db.scalar(select(User).where(User.email == settings.admin_email.lower())):
        db.add(User(name="Administrador", email=settings.admin_email.lower(),
                    password_hash=hash_password(settings.admin_password), role="admin"))
    db.commit()
