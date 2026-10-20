import io
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from .models import Diagnostic


def build_pdf(d: Diagnostic) -> bytes:  # RF08, RF23
    ss = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"Relatório AgroCare #{d.id}",
                            leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    P = lambda t, s="BodyText": Paragraph(escape(t), ss[s])
    dis = d.disease
    story = [P("AgroCare · Relatório resumido do diagnóstico", "Title"),
             P(f"Cultura: {d.crop}"),
             P(f"Data da análise: {d.created_at:%d/%m/%Y %H:%M}"),
             P(f"Doença identificada: {dis.name if dis else 'Nenhuma (folha saudável)'}"),
             P(f"Agente causal: {dis.scientific_name}") if dis else Spacer(1, 1),
             P(f"Severidade: {d.severity or '—'}"),
             P(f"Confiabilidade: {d.confidence * 100:.0f}%"
               + ("  (abaixo de 70%: confirmar com agrônomo)" if d.needs_review else "")),
             Spacer(1, 10)]
    for p in d.photos[:2]:
        try:
            story += [RLImage(p.path, width=7 * cm, height=7 * cm * p.height / p.width), Spacer(1, 6)]
        except Exception:
            pass
    if dis:
        for title, txt in (("Causas prováveis", dis.causes), ("Cuidados recomendados", dis.care),
                           ("Observações", dis.notes)):
            if txt:
                story += [P(title, "Heading3"), P(txt)]
    story += [Spacer(1, 14), P("Diagnóstico preliminar obtido a partir do padrão visual da folha. O AgroCare "
                               "não prescreve agrotóxicos nem tratamentos e não substitui a avaliação de um "
                               "engenheiro agrônomo habilitado.", "Italic")]
    doc.build(story)
    return buf.getvalue()
