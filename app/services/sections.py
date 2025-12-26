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

I'm an **AI & MLOps Engineer** with 2+ years of experience building high-performance LLM inference engines and distributed RAG pipelines.

Currently working on LLM infrastructure at [EonForge](#), previously at [Zoho Corporation](#)."""
        },
        "what_i_do": {
            "title": "What I Do",
            "content": """## What I do

- Build production LLM systems (vLLM, CTranslate2, LoRA fine-tuning)
- Design RAG pipelines with hybrid search and knowledge graphs
- Optimize inference latency and reduce cloud costs
- Deploy scalable AI microservices on Kubernetes"""
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
            "content": """I'm **Hemanth Irivichetty**, a product-focused AI Engineer with 2+ years of experience architecting high-performance LLM inference engines and distributed RAG pipelines."""
        },
        "specialization": {
            "title": "What I Specialize In",
            "content": """## What I specialize in

- **LLM Inference Optimization:** vLLM, CTranslate2, PagedAttention, quantization (Int8/AWQ)
- **RAG Systems:** Hybrid search (Vector + Knowledge Graph), FAISS, cross-encoder re-ranking
- **MLOps:** Kubernetes (EKS), Docker, CI/CD, Prometheus/Grafana monitoring
- **Fine-tuning:** LoRA/QLoRA, PEFT techniques for domain adaptation"""
        },
        "experience": {
            "title": "Experience Summary",
            "content": """## Experience

Currently at **EonForge (Logos Technologies LLC)** as an LLM & Vision Infrastructure Engineer, where I design RAG pipelines and OCR systems for insurance automation.

Previously at **Zoho Corporation** for 2+ years, where I:
- Increased LLM inference throughput from 20 to 80 tokens/sec (4x improvement)
- Reduced P99 latency by 40% and inference costs by 60%
- Led migration from RNN/LSTM to Transformer-based architectures"""
        },
        "education": {
            "title": "Education",
            "content": """## Education

B.Tech in Computer Science & Engineering from Sri Venkateswara College of Engineering (CGPA: 7.72)"""
        },
        "looking_for": {
            "title": "Currently Looking For",
            "content": """## Currently

Looking for opportunities at MAANG companies and interesting freelance projects. If you're working on challenging AI/ML problems, [let's talk](/contact)."""
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

- Building RAG pipelines with hybrid search at EonForge
- OCR and document processing systems for insurance automation
- Exploring multi-agent architectures"""
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
            "content": """## Goals for 2025

- Land a role at a MAANG company
- Write more technical blog posts
- Contribute to open-source LLM projects"""
        }
    },
    "resume": {
        "header": {
            "title": "Header",
            "content": """# Hemanth Irivichetty
**AI & MLOps Engineer**

[ihemanth.2001@gmail.com](mailto:ihemanth.2001@gmail.com) · +91 8500363606 · [LinkedIn](https://www.linkedin.com/in/hemanth-irivichetty/) · [GitHub](https://github.com/Hemanth-stack)"""
        },
        "summary": {
            "title": "Professional Summary",
            "content": """## Professional Summary

Product-focused AI Engineer with 2+ years of experience architecting high-performance LLM inference engines and distributed RAG pipelines. Expert in reducing production latency by 40% and inference costs by 60% through advanced quantization and memory optimization. Proven track record of migrating legacy NLP systems to Transformer-based architectures and deploying scalable, secure AI microservices on Kubernetes (EKS)."""
        },
        "skills": {
            "title": "Technical Skills",
            "content": """## Technical Skills

- **GenAI & LLM Inference:** vLLM, CTranslate2, PagedAttention, Dynamic Batching, Quantization (Int8/AWQ), LoRA/QLoRA Fine-tuning
- **RAG & Retrieval:** Hybrid Search (Vector + Knowledge Graph), FAISS, Cross-Encoders (BGE/Cohere), RAGAS Evaluation
- **Models:** LLaMA 3.1, Qwen 2.5, FLAN-T5, LSTM, RNN
- **MLOps & Cloud:** Kubernetes (EKS), Docker, AWS (EC2, S3), CI/CD (GitHub Actions), Prometheus, Grafana
- **Backend Engineering:** Python (AsyncIO), FastAPI, Celery, SQLAlchemy (Async), Hybrid Encryption (RSA + Fernet), JWT/OAuth2
- **Vision & OCR:** Tesseract OCR, Document Layout Analysis, Object Detection (YOLO)"""
        },
        "exp_eonforge": {
            "title": "EonForge Experience",
            "content": """## EonForge (Logos Technologies LLC)
**LLM & Vision Infrastructure Engineer** · Dubai, UAE / Remote · July 2025 – Present

- Designed Hybrid RAG system combining FAISS vector search with Knowledge Graph traversal for multi-hop reasoning
- Built end-to-end document processing pipeline using Tesseract OCR with custom layout analysis
- Architected orchestration layer for "LumenCipher" Insurance CRM with JWT/OAuth2 security
- Developed intelligent agents for automated claims processing using SQLAlchemy (Async)"""
        },
        "exp_zoho_mts": {
            "title": "Zoho MTS Experience",
            "content": """## Zoho Corporation
**Member Technical Staff (NLP & AI)** · Chennai, TN · June 2023 – June 2025

- **4x Throughput:** Migrated to vLLM with Continuous Batching, increasing throughput from 20 to 80 tokens/sec
- **40% Latency Reduction:** Implemented Int8 Quantization using CTranslate2, reducing P99 from 5s to 3s
- **60% Cost Reduction:** Achieved through CPU offloading and optimized GEMM kernels
- Fine-tuned FLAN-T5 and LLaMA 3.1 using LoRA/QLoRA for specialized tasks
- Deployed on Kubernetes (EKS) with HPA based on GPU metrics and Prometheus/Grafana monitoring"""
        },
        "exp_zoho_trainee": {
            "title": "Zoho Trainee Experience",
            "content": """## Zoho Corporation
**Project Trainee (AI/ML)** · Chennai, TN · Oct 2022 – May 2023

- Led migration from RNN/LSTM to Transformer-based pipelines
- Built data migration pipelines using Zoho Catalyst
- Enforced code quality with Poetry and Pytest"""
        },
        "education": {
            "title": "Education",
            "content": """## Education

**B.Tech in Computer Science & Engineering**
Sri Venkateswara College of Engineering · CGPA: 7.72"""
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
