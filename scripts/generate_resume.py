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
    story.append(Paragraph("Machine Learning & AI Engineer", styles['Normal']))
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
        "AI and MLOps Engineer with 3+ years of experience shipping production-grade NLP and LLM systems at scale. "
        "At Zoho Corporation, I owned both sides of the AI stack — building customer-facing NLP features (grammar "
        "correction, summarization, question answering, sentiment analysis, and NL-to-SQL analytics) and engineering "
        "the inference platform that powered them, delivering a 4× throughput increase, 40% latency reduction, and "
        "60% cost savings. I implemented tensor parallelism for multi-GPU inference, built full model CI/CD pipelines "
        "with automated retraining, and personally constructed custom CUDA-optimized data pipelines from scratch.",
        normal_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "At Arrise Solutions, I am building computer vision and audio intelligence systems for live game stream "
        "support — designing pose estimation pipelines for real-time posture tracking and developing audio monitoring "
        "models for continuous sound event detection and speech analysis across simultaneous live iGaming feeds.",
        normal_style
    ))
    story.append(Spacer(1, 12))

    # Technical Skills
    story.append(Paragraph("Technical Skills", heading_style))
    skills = [
        ("Core Languages", "Python (AsyncIO) · Bash · SQL · CUDA"),
        ("ML Frameworks", "PyTorch · TensorFlow · Hugging Face Transformers · PEFT · scikit-learn · NumPy · Pandas"),
        ("NLP Tasks", "Grammar Correction · Text Summarization · Question Answering · Sentiment Analysis · NL-to-SQL / NLA · Sequence Labeling"),
        ("LLM & Fine-Tuning", "LLaMA 3.1 · Qwen 2.5 · FLAN-T5 · GPT-4 · Mistral · LoRA · QLoRA · Prompt Engineering · RLHF (exposure)"),
        ("LLM Inference", "vLLM · PagedAttention · Continuous Batching · CTranslate2 · Int8 / AWQ Quantization · Tensor Parallelism · Triton"),
        ("RAG & Agents", "LangChain · FAISS · ChromaDB · Hybrid Search · Cross-Encoder Re-ranking · RAGAS · CrewAI · Multi-Agent Systems"),
        ("MLOps & CI/CD", "Kubernetes (EKS) · Docker · GitHub Actions · MLflow · Prometheus · Grafana · Weights & Biases · DVC"),
        ("Cloud & Infra", "AWS (EC2, S3) · Azure (Open AI) · GCP (Vertex AI) · Distributed Systems · Microservices"),
        ("Backend & Security", "FastAPI · Celery · SQLAlchemy (Async) · REST APIs · JWT / OAuth2 · Hybrid Encryption (RSA + Fernet)"),
    ]

    for skill, details in skills:
        story.append(Paragraph(f"<b>{skill}:</b> {details}", normal_style))
    story.append(Spacer(1, 12))

    # Professional Experience
    story.append(Paragraph("Professional Experience", heading_style))

    # Arrise Solutions (current)
    story.append(Paragraph(
        "<b>Machine Learning Engineer</b><br/>"
        "Arrise Solutions (India) Pvt Ltd · India · Remote · Apr 2026 – Present",
        normal_style
    ))
    story.append(Paragraph(
        "• <b>Domain:</b> Building and deploying ML/CV models for Gaming and iGaming analytics, automating data-intensive processes previously performed manually<br/>"
        "• <b>Computer Vision:</b> Designing and experimenting with posture tracking and image analysis pipelines using PyTorch, OpenCV, and YOLO to extract actionable intelligence from gaming streams and visual data<br/>"
        "• <b>MLOps Infrastructure:</b> Establishing model lifecycle management with MLflow and DVC; containerizing workloads with Docker and Kubernetes for reproducible, scalable experiment and deployment workflows",
        normal_style
    ))
    story.append(Spacer(1, 10))

    # EonForge
    story.append(Paragraph(
        "<b>LLM & Vision Infrastructure Engineer</b><br/>"
        "Logos Technologies LLC (EonForge) · Dubai, UAE · Remote · Jul 2025 – Mar 2026",
        normal_style
    ))
    story.append(Paragraph(
        "• <b>System Architecture:</b> Designed the complete AI infrastructure for LumenCipher, an enterprise insurance CRM spanning RAG pipelines, OCR/vision systems, and multi-agent orchestration, all secured with JWT/OAuth2 authentication<br/>"
        "• <b>Hybrid RAG Pipeline:</b> Built a production RAG system combining FAISS vector search with Knowledge Graph traversal for multi-hop reasoning; added Cross-Encoder re-ranking (BGE) to boost retrieval precision, with end-to-end evaluation via BLEU and ROUGE metrics<br/>"
        "• <b>Document Intelligence:</b> Engineered an OCR and vision pipeline using Tesseract with custom layout analysis and YOLO-based object detection, enabling automated structured data extraction from complex insurance claim forms at hundreds of documents per day<br/>"
        "• <b>Agent Orchestration:</b> Architected the multi-agent workflow layer that automates claims processing end-to-end, integrating AI agents with the CRM database via SQLAlchemy Async, significantly reducing manual intervention in the claims lifecycle",
        normal_style
    ))
    story.append(Spacer(1, 10))

    # Zoho - MTS
    story.append(Paragraph(
        "<b>Member of Technical Staff (NLP & AI)</b><br/>"
        "Zoho Corporation · Chennai, India · On-site · Jun 2023 – Jun 2025",
        normal_style
    ))
    story.append(Paragraph(
        "• <b>NLP Feature Ownership:</b> Built and shipped five customer-facing NLP capabilities: grammar correction, abstractive text summarization, extractive question answering, sentiment analysis, and NL-to-SQL using fine-tuned FLAN-T5, LLaMA 3.1, and custom models via LoRA/QLoRA<br/>"
        "• <b>NL-to-SQL / NLA Workflows:</b> Developed natural language query interfaces over Zoho's internal databases and BI dashboards with schema-aware SQL generation and intent parsing<br/>"
        "• <b>4× Throughput Optimization:</b> Migrated the shared inference platform from a custom FastAPI queue to vLLM with Continuous Batching and PagedAttention, scaling throughput from 20 to 80 tokens/sec<br/>"
        "• <b>Distributed Inference:</b> Implemented tensor parallelism and model sharding for multi-GPU inference under sustained high-concurrency production traffic<br/>"
        "• <b>Model CI/CD Pipeline:</b> Designed and owned the full model CI/CD pipeline with automated retraining triggers, evaluation gates, and deployment to Kubernetes (EKS) with HPA on GPU metrics ensuring zero-downtime rollouts<br/>"
        "• <b>Observability:</b> Set up centralized monitoring with Prometheus and Grafana; configured MLflow and Weights & Biases for team-wide experiment tracking<br/>"
        "• <b>Security:</b> Secured on-premise to cloud model communication using Hybrid Encryption (RSA + Fernet symmetric keys)",
        normal_style
    ))
    story.append(Spacer(1, 10))

    # Zoho - Trainee
    story.append(Paragraph(
        "<b>Project Trainee (AI/ML)</b><br/>"
        "Zoho Corporation · Chennai, India · On-site · Oct 2022 – May 2023",
        normal_style
    ))
    story.append(Paragraph(
        "• <b>Architecture Migration:</b> Led the migration of core NLP workflows from RNN/LSTM to Transformer-based pipelines, significantly improving sequence labeling accuracy<br/>"
        "• <b>Data Engineering:</b> Built annotation interfaces and data migration pipelines using Zoho Catalyst, streamlining preprocessing of large-scale text corpora<br/>"
        "• <b>Engineering Standards:</b> Introduced Poetry for dependency management and Pytest-based unit and integration testing across the AI pipeline",
        normal_style
    ))
    story.append(Spacer(1, 12))

    # Notable Projects
    story.append(Paragraph("Notable Projects", heading_style))
    story.append(Paragraph("<b>GEC – Grammar Error Correction System</b>", normal_style))
    story.append(Paragraph(
        "End-to-end grammar correction pipeline fine-tuned on FLAN-T5 using LoRA on domain-specific text corpora. "
        "Includes a custom preprocessing pipeline, BLEU-based evaluation harness, and a FastAPI inference server. "
        "Demonstrates low-resource fine-tuning and production-ready NLP serving.",
        normal_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>OLLM – Optimized LLM Inference Server</b>", normal_style))
    story.append(Paragraph(
        "A lightweight, production-oriented LLM inference server built on top of vLLM with custom batching strategies, "
        "Int8 quantization support, and a Prometheus metrics endpoint. Designed to benchmark throughput and latency "
        "trade-offs across different quantization and batching configurations.",
        normal_style
    ))
    story.append(Spacer(1, 12))

    # Education
    story.append(Paragraph("Education", heading_style))
    story.append(Paragraph(
        "<b>B.Tech in Computer Science & Engineering</b><br/>"
        "Jawaharlal Nehru Technological University Anantapur (JNTUA) · Aug 2019 – Jul 2023 · CGPA: 7.72",
        normal_style
    ))

    # Build PDF
    doc.build(story)
    print(f"✅ Resume generated: {pdf_path}")


if __name__ == "__main__":
    generate_resume()
