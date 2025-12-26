#!/usr/bin/env python3
"""
Generate resume PDF from your profile data.
Usage: python scripts/generate_resume.py
"""

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from datetime import datetime
except ImportError:
    print("❌ reportlab not installed. Installing...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'reportlab'])
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors


def generate_resume():
    # Create PDF
    pdf_path = "static/resume.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#111111'),
        spaceAfter=6,
        alignment=0
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#111111'),
        spaceAfter=6,
        spaceBefore=12,
        borderBottomColor=colors.HexColor('#ddd'),
        borderBottomWidth=1,
        borderPadding=3
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )
    
    # Build document
    story = []
    
    # Header
    story.append(Paragraph("Hemanth Irivichetty", title_style))
    story.append(Paragraph("AI & MLOps Engineer", styles['Normal']))
    story.append(Paragraph(
        "ihemanth.2001@gmail.com | +91 8500363606 | "
        '<a href="https://www.linkedin.com/in/hemanth-irivichetty/">LinkedIn</a> | '
        '<a href="https://github.com/Hemanth-stack">GitHub</a>',
        normal_style
    ))
    story.append(Spacer(1, 12))
    
    # Professional Summary
    story.append(Paragraph("Professional Summary", heading_style))
    story.append(Paragraph(
        "Product-focused AI Engineer with 2+ years of experience architecting high-performance LLM "
        "inference engines and distributed RAG pipelines. Expert in reducing production latency by 40% "
        "and inference costs by 60% through advanced quantization and memory optimization. Proven track record "
        "of migrating legacy NLP systems to Transformer-based architectures and deploying scalable, secure AI "
        "microservices on Kubernetes (EKS).",
        normal_style
    ))
    story.append(Spacer(1, 12))
    
    # Technical Skills
    story.append(Paragraph("Technical Skills", heading_style))
    skills = [
        ("GenAI & LLM Inference", "vLLM, CTranslate2, PagedAttention, Dynamic Batching, Quantization (Int8/AWQ), LoRA/QLoRA Fine-tuning"),
        ("RAG & Retrieval", "Hybrid Search (Vector + Knowledge Graph), FAISS, Cross-Encoders (BGE/Cohere), RAGAS Evaluation"),
        ("Models", "LLaMA 3.1, Qwen 2.5, FLAN-T5, LSTM, RNN"),
        ("MLOps & Cloud", "Kubernetes (EKS), Docker, AWS (EC2, S3), CI/CD (GitHub Actions), Prometheus, Grafana"),
        ("Backend Engineering", "Python (AsyncIO), FastAPI, Celery, SQLAlchemy (Async), Hybrid Encryption, JWT/OAuth2"),
        ("Vision & OCR", "Tesseract OCR, Document Layout Analysis, Object Detection (YOLO)"),
    ]
    
    for skill, details in skills:
        story.append(Paragraph(f"<b>{skill}:</b> {details}", normal_style))
    story.append(Spacer(1, 12))
    
    # Professional Experience
    story.append(Paragraph("Professional Experience", heading_style))
    
    # EonForge
    story.append(Paragraph(
        "<b>LLM & Vision Infrastructure Engineer</b><br/>"
        "EonForge (Logos Technologies LLC) · Dubai, UAE / Remote · July 2025 – Present",
        normal_style
    ))
    story.append(Paragraph(
        "• Designed Hybrid RAG system combining FAISS vector search with Knowledge Graph traversal<br/>"
        "• Built end-to-end document processing pipeline using Tesseract OCR with custom layout analysis<br/>"
        "• Architected orchestration layer for 'LumenCipher' Insurance CRM with JWT/OAuth2 security<br/>"
        "• Developed intelligent agents for automated claims processing using SQLAlchemy (Async)",
        normal_style
    ))
    story.append(Spacer(1, 10))
    
    # Zoho - MTS
    story.append(Paragraph(
        "<b>Member Technical Staff (NLP & AI)</b><br/>"
        "Zoho Corporation · Chennai, TN · June 2023 – June 2025",
        normal_style
    ))
    story.append(Paragraph(
        "• <b>4x Throughput:</b> Migrated to vLLM, increasing throughput from 20 to 80 tokens/sec<br/>"
        "• <b>40% Latency Reduction:</b> Implemented Int8 Quantization using CTranslate2, reducing P99 from 5s to 3s<br/>"
        "• <b>60% Cost Reduction:</b> Achieved through CPU offloading and optimized GEMM kernels<br/>"
        "• Fine-tuned FLAN-T5 and LLaMA 3.1 using LoRA/QLoRA for specialized tasks<br/>"
        "• Deployed on Kubernetes (EKS) with HPA based on GPU metrics and Prometheus/Grafana monitoring",
        normal_style
    ))
    story.append(Spacer(1, 10))
    
    # Zoho - Trainee
    story.append(Paragraph(
        "<b>Project Trainee (AI/ML)</b><br/>"
        "Zoho Corporation · Chennai, TN · Oct 2022 – May 2023",
        normal_style
    ))
    story.append(Paragraph(
        "• Led migration from RNN/LSTM to Transformer-based pipelines<br/>"
        "• Built data migration pipelines using Zoho Catalyst<br/>"
        "• Enforced code quality with Poetry and Pytest",
        normal_style
    ))
    story.append(Spacer(1, 12))
    
    # Education
    story.append(Paragraph("Education", heading_style))
    story.append(Paragraph(
        "<b>B.Tech in Computer Science & Engineering</b><br/>"
        "Sri Venkateswara College of Engineering · CGPA: 7.72",
        normal_style
    ))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Resume generated: {pdf_path}")


if __name__ == "__main__":
    generate_resume()
