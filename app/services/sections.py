"""
Section management service for inline editing.
Handles default content and section CRUD operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Section
from app.services.markdown import render_markdown


# Default content for all sections
DEFAULT_SECTIONS = {
    "home": {
        "hero": {
            "title": "Hero Introduction",
            "content": """# Hi, I'm Hemanth 👋

I'm an **AI & MLOps Engineer** with 3+ years of experience shipping production-grade NLP, LLM, and computer vision systems at scale.

Currently building CV and audio intelligence systems at [Arrise Solutions](#), previously at [EonForge (Logos Technologies)](#) and [Zoho Corporation](#)."""
        },
        "what_i_do": {
            "title": "What I Do",
            "content": """## What I do

- Build production LLM systems (vLLM, CTranslate2, LoRA/QLoRA fine-tuning)
- Design RAG pipelines with hybrid search and knowledge graphs
- Build computer vision pipelines for real-time stream analytics (YOLO, OpenCV, PyTorch)
- Optimize inference latency and reduce cloud costs
- Deploy scalable AI microservices on Kubernetes

Try the [PEFT Visualizer](/tools/peft-visualizer), an interactive tool for exploring LoRA/QLoRA adapter mechanics."""
        },
        "cta": {
            "title": "Call to Action",
            "content": """## Get in touch

Looking for an AI/ML engineer? [Send me a message](/contact) or email me at [ihemanth.2001@gmail.com](mailto:ihemanth.2001@gmail.com)."""
        }
    },
    "about": {
        "intro": {
            "title": "Introduction",
            "content": """I'm **Hemanth Irivichetty**, an AI and MLOps Engineer with 3+ years of experience shipping production-grade NLP, LLM, and computer vision systems at scale."""
        },
        "specialization": {
            "title": "What I Specialize In",
            "content": """## What I specialize in

- **LLM Inference Optimization:** vLLM, CTranslate2, PagedAttention, Tensor Parallelism, quantization (Int8/AWQ)
- **RAG Systems:** Hybrid search (Vector + Knowledge Graph), FAISS, ChromaDB, cross-encoder re-ranking, RAGAS evaluation
- **Computer Vision:** PyTorch, OpenCV, YOLO — pose estimation, stream analytics, image analysis pipelines
- **MLOps:** Kubernetes (EKS), Docker, GitHub Actions, MLflow, DVC, Prometheus/Grafana, Weights & Biases
- **Fine-tuning:** LoRA/QLoRA, PEFT techniques for domain adaptation"""
        },
        "experience": {
            "title": "Experience Summary",
            "content": """## Experience

Currently at **Arrise Solutions** as a Machine Learning Engineer, building computer vision and audio intelligence systems for live iGaming stream analytics — pose estimation pipelines and audio monitoring models for sound event detection.

Previously at **EonForge (Logos Technologies LLC)** as an LLM & Vision Infrastructure Engineer (Jul 2025 – Mar 2026), where I designed the complete AI infrastructure for LumenCipher, an enterprise insurance CRM with RAG pipelines, OCR systems, and multi-agent orchestration.

Earlier at **Zoho Corporation** (Jun 2023 – Jun 2025), where I:
- Increased LLM inference throughput from 20 to 80 tokens/sec (4× improvement)
- Reduced P99 latency by 40% and inference costs by 60%
- Built and shipped five customer-facing NLP capabilities on a unified platform
- Led migration from RNN/LSTM to Transformer-based architectures"""
        },
        "education": {
            "title": "Education",
            "content": """## Education

B.Tech in Computer Science & Engineering from Jawaharlal Nehru Technological University Anantapur (JNTUA) · CGPA: 7.72"""
        },
        "looking_for": {
            "title": "Currently Looking For",
            "content": """## Currently

Open to challenging AI/ML engineering roles and interesting freelance projects. If you're working on hard problems in LLM inference, RAG, or computer vision, [let's talk](/contact)."""
        }
    },
    "now": {
        "intro": {
            "title": "Introduction",
            "content": """This is a ["now page"](https://nownownow.com/about) – what I'm currently focused on."""
        },
        "working_on": {
            "title": "Working On",
            "content": """## Working on

- Building CV and audio intelligence systems for live iGaming streams at Arrise Solutions
- Designing pose estimation pipelines for real-time posture tracking using PyTorch, OpenCV, and YOLO
- Developing audio monitoring models for sound event detection and speech analysis
- Exploring multi-agent architectures with CrewAI"""
        },
        "learning": {
            "title": "Learning",
            "content": """## Learning

- Advanced prompt engineering techniques
- Rust for systems programming
- Building in public"""
        },
        "reading": {
            "title": "Reading",
            "content": """## Reading

- *Designing Machine Learning Systems* by Chip Huyen
- LLM research papers (Llama, Qwen series)"""
        },
        "goals": {
            "title": "Goals",
            "content": """## Goals for 2026

- Land a role at a MAANG company
- Write more technical blog posts
- Contribute to open-source LLM projects"""
        }
    },
    "resume": {
        "header": {
            "title": "Header",
            "content": """# Hemanth Irivichetty
**Machine Learning & AI Engineer**

[ihemanth.2001@gmail.com](mailto:ihemanth.2001@gmail.com) · +91 8500363606 · [LinkedIn](https://www.linkedin.com/in/hemanth-irivichetty/) · [GitHub](https://github.com/Hemanth-stack)"""
        },
        "summary": {
            "title": "Professional Summary",
            "content": """## Professional Summary

AI and MLOps Engineer with 3+ years of experience shipping production-grade NLP and LLM systems at scale. At Zoho Corporation, I owned both sides of the AI stack — building customer-facing NLP features (grammar correction, summarization, question answering, sentiment analysis, and NL-to-SQL analytics) and engineering the inference platform that powered them, delivering a 4× throughput increase, 40% latency reduction, and 60% cost savings. I implemented tensor parallelism for multi-GPU inference, built full model CI/CD pipelines with automated retraining, and personally constructed custom CUDA-optimized data pipelines from scratch.

At Arrise Solutions, I am building computer vision and audio intelligence systems for live game stream support — designing pose estimation pipelines for real-time posture tracking and developing audio monitoring models for continuous sound event detection and speech analysis across simultaneous live iGaming feeds."""
        },
        "skills": {
            "title": "Technical Skills",
            "content": """## Technical Skills

- **Core Languages:** Python (AsyncIO) · Bash · SQL · CUDA
- **ML Frameworks:** PyTorch · TensorFlow · Hugging Face Transformers · PEFT · scikit-learn · NumPy · Pandas
- **NLP Tasks:** Grammar Correction · Text Summarization · Question Answering · Sentiment Analysis · NL-to-SQL / NLA · Sequence Labeling
- **LLM & Fine-Tuning:** LLaMA 3.1 · Qwen 2.5 · FLAN-T5 · GPT-4 · Mistral · LoRA · QLoRA · Prompt Engineering · RLHF (exposure)
- **LLM Inference:** vLLM · PagedAttention · Continuous Batching · CTranslate2 · Int8 / AWQ Quantization · Tensor Parallelism · Triton
- **RAG & Agents:** LangChain · FAISS · ChromaDB · Hybrid Search · Cross-Encoder Re-ranking · RAGAS · CrewAI · Multi-Agent Systems
- **MLOps & CI/CD:** Kubernetes (EKS) · Docker · GitHub Actions · MLflow · Prometheus · Grafana · Weights & Biases · DVC
- **Cloud & Infra:** AWS (EC2, S3) · Azure (Open AI) · GCP (Vertex AI) · Distributed Systems · Microservices
- **Backend & Security:** FastAPI · Celery · SQLAlchemy (Async) · REST APIs · JWT / OAuth2 · Hybrid Encryption (RSA + Fernet)"""
        },
        "exp_arrise": {
            "title": "Arrise Solutions Experience",
            "content": """## Arrise Solutions (India) Pvt Ltd
**Machine Learning Engineer** · India · Remote · Apr 2026 – Present

- **Domain:** Building and deploying ML/CV models for Gaming and iGaming analytics, automating data-intensive processes previously performed manually
- **Computer Vision:** Designing and experimenting with posture tracking and image analysis pipelines using PyTorch, OpenCV, and YOLO to extract actionable intelligence from gaming streams and visual data
- **MLOps Infrastructure:** Establishing model lifecycle management with MLflow and DVC; containerizing workloads with Docker and Kubernetes for reproducible, scalable experiment and deployment workflows"""
        },
        "exp_eonforge": {
            "title": "EonForge Experience",
            "content": """## Logos Technologies LLC (EonForge)
**LLM & Vision Infrastructure Engineer** · Dubai, UAE · Remote · Jul 2025 – Mar 2026

- **System Architecture:** Designed the complete AI infrastructure for LumenCipher, an enterprise insurance CRM spanning RAG pipelines, OCR/vision systems, and multi-agent orchestration, all secured with JWT/OAuth2 authentication
- **Hybrid RAG Pipeline:** Built a production RAG system combining FAISS vector search with Knowledge Graph traversal for multi-hop reasoning; added Cross-Encoder re-ranking (BGE) to boost retrieval precision, with end-to-end evaluation via BLEU and ROUGE metrics
- **Document Intelligence:** Engineered an OCR and vision pipeline using Tesseract with custom layout analysis and YOLO-based object detection, enabling automated structured data extraction from complex insurance claim forms at hundreds of documents per day
- **Agent Orchestration:** Architected the multi-agent workflow layer that automates claims processing end-to-end, integrating AI agents with the CRM database via SQLAlchemy Async, significantly reducing manual intervention in the claims lifecycle"""
        },
        "exp_zoho_mts": {
            "title": "Zoho MTS Experience",
            "content": """## Zoho Corporation
**Member of Technical Staff (NLP & AI)** · Chennai, India · On-site · Jun 2023 – Jun 2025

- **NLP Feature Ownership:** Built and shipped five customer-facing NLP capabilities: grammar correction, abstractive text summarization, extractive question answering, sentiment analysis, and NL-to-SQL using fine-tuned FLAN-T5, LLaMA 3.1, and custom models via LoRA/QLoRA; evaluated with BLEU/ROUGE scores and human review cycles
- **NL-to-SQL / NLA Workflows:** Developed natural language query interfaces over Zoho's internal databases and BI dashboards, enabling business users to query structured data in plain English with schema-aware SQL generation and intent parsing
- **4× Throughput Optimization:** Migrated the shared inference platform from a custom FastAPI queue to vLLM with Continuous Batching and PagedAttention, scaling throughput from 20 to 80 tokens/sec across all workloads simultaneously
- **Distributed Inference:** Implemented tensor parallelism and model sharding for multi-GPU inference, allowing larger models to be served reliably under sustained high-concurrency production traffic
- **Model CI/CD Pipeline:** Designed and owned the full model CI/CD pipeline with automated retraining triggers, evaluation gates, and deployment to Kubernetes (EKS) with HPA on GPU metrics ensuring zero-downtime rollouts
- **Observability:** Set up centralized monitoring with Prometheus and Grafana covering GPU utilization, memory consumption, and per-feature request latency; configured MLflow and Weights & Biases for team-wide experiment tracking
- **Security:** Secured on-premise to cloud model communication using Hybrid Encryption (RSA + Fernet symmetric keys), ensuring data integrity across the inference boundary"""
        },
        "exp_zoho_trainee": {
            "title": "Zoho Trainee Experience",
            "content": """## Zoho Corporation
**Project Trainee (AI/ML)** · Chennai, India · On-site · Oct 2022 – May 2023

- **Architecture Migration:** Led the migration of core NLP workflows from RNN/LSTM architectures to Transformer-based pipelines, significantly improving sequence labeling accuracy across production datasets
- **Data Engineering:** Built annotation interfaces and data migration pipelines using Zoho Catalyst, streamlining preprocessing of large-scale text corpora for model training jobs
- **Engineering Standards:** Introduced Poetry for dependency management and Pytest-based unit and integration testing across the AI pipeline, raising the team's code quality baseline"""
        },
        "projects": {
            "title": "Notable Projects",
            "content": """## Notable Projects

### GEC – Grammar Error Correction System
End-to-end grammar correction pipeline fine-tuned on FLAN-T5 using LoRA on domain-specific text corpora. Includes a custom preprocessing pipeline, BLEU-based evaluation harness, and a FastAPI inference server. Demonstrates low-resource fine-tuning and production-ready NLP serving.

### OLLM – Optimized LLM Inference Server
A lightweight, production-oriented LLM inference server built on top of vLLM with custom batching strategies, Int8 quantization support, and a Prometheus metrics endpoint. Designed to benchmark throughput and latency trade-offs across different quantization and batching configurations."""
        },
        "education": {
            "title": "Education",
            "content": """## Education

**B.Tech in Computer Science & Engineering**
Jawaharlal Nehru Technological University Anantapur (JNTUA) · Aug 2019 – Jul 2023 · CGPA: 7.72"""
        }
    },
    "contact": {
        "intro": {
            "title": "Introduction",
            "content": """Have a project in mind? Looking for an AI/ML engineer? Or just want to say hello?

You can reach me at [ihemanth.2001@gmail.com](mailto:ihemanth.2001@gmail.com) or use the form below."""
        },
        "other_ways": {
            "title": "Other Ways to Connect",
            "content": """## Other ways to connect

- **Email:** [ihemanth.2001@gmail.com](mailto:ihemanth.2001@gmail.com)
- **LinkedIn:** [linkedin.com/in/hemanth-irivichetty](https://www.linkedin.com/in/hemanth-irivichetty/)
- **GitHub:** [github.com/Hemanth-stack](https://github.com/Hemanth-stack)
- **Phone:** +91 8500363606"""
        }
    }
}


async def get_section(db: AsyncSession, page: str, section_key: str) -> Section | None:
    """Get a section by page and key."""
    result = await db.execute(
        select(Section).where(Section.page == page, Section.section_key == section_key)
    )
    return result.scalar_one_or_none()


async def get_or_create_section(db: AsyncSession, page: str, section_key: str) -> Section:
    """Get a section or create it with default content."""
    section = await get_section(db, page, section_key)
    
    if not section:
        # Get default content
        default = DEFAULT_SECTIONS.get(page, {}).get(section_key, {})
        section = Section(
            page=page,
            section_key=section_key,
            title=default.get("title", section_key.replace("_", " ").title()),
            content=default.get("content", ""),
            order=0,
            visible=True
        )
        db.add(section)
        await db.commit()
        await db.refresh(section)
    
    return section


async def get_page_sections(db: AsyncSession, page: str) -> dict[str, Section]:
    """Get all sections for a page as a dict keyed by section_key."""
    result = await db.execute(
        select(Section).where(Section.page == page).order_by(Section.order)
    )
    sections = result.scalars().all()
    return {s.section_key: s for s in sections}


async def init_page_sections(db: AsyncSession, page: str) -> dict[str, Section]:
    """Initialize all default sections for a page and return them."""
    sections = {}
    default_sections = DEFAULT_SECTIONS.get(page, {})
    
    for order, (key, data) in enumerate(default_sections.items()):
        section = await get_section(db, page, key)
        if not section:
            section = Section(
                page=page,
                section_key=key,
                title=data.get("title", key.replace("_", " ").title()),
                content=data.get("content", ""),
                order=order,
                visible=True
            )
            db.add(section)
        sections[key] = section
    
    await db.commit()
    return sections


async def update_section(db: AsyncSession, page: str, section_key: str, content: str, title: str = None) -> Section:
    """Update a section's content."""
    section = await get_or_create_section(db, page, section_key)
    section.content = content
    if title is not None:
        section.title = title
    await db.commit()
    await db.refresh(section)
    return section


async def create_section(db: AsyncSession, page: str, section_key: str, title: str, content: str, order: int = 0) -> Section:
    """Create a new section."""
    section = Section(
        page=page,
        section_key=section_key,
        title=title,
        content=content,
        order=order,
        visible=True
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


async def delete_section(db: AsyncSession, section_id: int) -> bool:
    """Delete a section by ID."""
    result = await db.execute(select(Section).where(Section.id == section_id))
    section = result.scalar_one_or_none()
    if section:
        await db.delete(section)
        await db.commit()
        return True
    return False


def render_section(section: Section) -> str:
    """Render a section's content as HTML."""
    return render_markdown(section.content) if section and section.content else ""
