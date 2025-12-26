"""Site settings and content management service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import SiteSettings, Page, ResumeSection
from app.config import get_settings


# Default site settings
DEFAULT_SETTINGS = {
    # Header/Profile
    "site_name": "Hemanth Irivichetty",
    "site_tagline": "AI & MLOps Engineer",
    "site_email": "ihemanth.2001@gmail.com",
    "site_phone": "+91 8500363606",
    "linkedin_url": "https://www.linkedin.com/in/hemanth-irivichetty/",
    "github_url": "https://github.com/Hemanth-stack",
    
    # Home page
    "home_greeting": "Hi, I'm Hemanth 👋",
    "home_intro": "I'm an **AI & MLOps Engineer** with 2+ years of experience building high-performance LLM inference engines and distributed RAG pipelines.",
    "home_current": "Currently working on LLM infrastructure at [EonForge](https://eonforge.com), previously at [Zoho Corporation](https://zoho.com).",
    "home_what_i_do": """- Build production LLM systems (vLLM, CTranslate2, LoRA fine-tuning)
- Design RAG pipelines with hybrid search and knowledge graphs
- Optimize inference latency and reduce cloud costs
- Deploy scalable AI microservices on Kubernetes""",
    "home_cta": "Looking for an AI/ML engineer? [Send me a message](/contact) or email me at [ihemanth.2001@gmail.com](mailto:ihemanth.2001@gmail.com).",
    
    # Footer
    "footer_text": "",
}

# Default pages content
DEFAULT_PAGES = {
    "about": {
        "title": "About Me",
        "meta_description": "About Hemanth Irivichetty, AI & MLOps Engineer with expertise in LLM systems and distributed pipelines.",
        "content": """I'm **Hemanth Irivichetty**, a product-focused AI Engineer with 2+ years of experience architecting high-performance LLM inference engines and distributed RAG pipelines.

## What I specialize in

- **LLM Inference Optimization:** vLLM, CTranslate2, PagedAttention, quantization (Int8/AWQ)
- **RAG Systems:** Hybrid search (Vector + Knowledge Graph), FAISS, cross-encoder re-ranking
- **MLOps:** Kubernetes (EKS), Docker, CI/CD, Prometheus/Grafana monitoring
- **Fine-tuning:** LoRA/QLoRA, PEFT techniques for domain adaptation

## Experience

Currently at **EonForge (Logos Technologies LLC)** as an LLM & Vision Infrastructure Engineer, where I design RAG pipelines and OCR systems for insurance automation.

Previously at **Zoho Corporation** for 2+ years, where I:
- Increased LLM inference throughput from 20 to 80 tokens/sec (4x improvement)
- Reduced P99 latency by 40% and inference costs by 60%
- Led migration from RNN/LSTM to Transformer-based architectures

## Education

B.Tech in Computer Science & Engineering from Sri Venkateswara College of Engineering (CGPA: 7.72)

## Currently

Looking for opportunities at MAANG companies and interesting freelance projects. If you're working on challenging AI/ML problems, [let's talk](/contact)."""
    },
    "now": {
        "title": "Now",
        "meta_description": "What Hemanth Irivichetty is currently working on and learning.",
        "content": """This is a ["now page"](https://nownownow.com/about) – what I'm currently focused on.

## Working on

- Building RAG pipelines with hybrid search at EonForge
- OCR and document processing systems for insurance automation
- Exploring multi-agent architectures

## Learning

- Advanced prompt engineering techniques
- Rust for systems programming
- Building in public

## Reading

- *Designing Machine Learning Systems* by Chip Huyen
- LLM research papers (Llama, Qwen series)

## Goals for 2025

- Land a role at a MAANG company
- Write more technical blog posts
- Contribute to open-source LLM projects"""
    },
}

# Default resume sections
DEFAULT_RESUME_SECTIONS = [
    {
        "section_type": "header",
        "title": "Hemanth Irivichetty",
        "content": """{
    "tagline": "AI & MLOps Engineer",
    "email": "ihemanth.2001@gmail.com",
    "phone": "+91 8500363606",
    "linkedin": "https://www.linkedin.com/in/hemanth-irivichetty/",
    "github": "https://github.com/Hemanth-stack"
}""",
        "order": 1
    },
    {
        "section_type": "summary",
        "title": "Professional Summary",
        "content": "Product-focused AI Engineer with 2+ years of experience architecting high-performance LLM inference engines and distributed RAG pipelines. Expert in reducing production latency by 40% and inference costs by 60% through advanced quantization and memory optimization. Proven track record of migrating legacy NLP systems to Transformer-based architectures and deploying scalable, secure AI microservices on Kubernetes (EKS).",
        "order": 2
    },
    {
        "section_type": "skills",
        "title": "Technical Skills",
        "content": """- **GenAI & LLM Inference:** vLLM, CTranslate2, PagedAttention, Dynamic Batching, Quantization (Int8/AWQ), LoRA/QLoRA Fine-tuning
- **RAG & Retrieval:** Hybrid Search (Vector + Knowledge Graph), FAISS, Cross-Encoders (BGE/Cohere), RAGAS Evaluation
- **Models:** LLaMA 3.1, Qwen 2.5, FLAN-T5, LSTM, RNN
- **MLOps & Cloud:** Kubernetes (EKS), Docker, AWS (EC2, S3), CI/CD (GitHub Actions), Prometheus, Grafana
- **Backend Engineering:** Python (AsyncIO), FastAPI, Celery, SQLAlchemy (Async), Hybrid Encryption, JWT/OAuth2
- **Vision & OCR:** Tesseract OCR, Document Layout Analysis, Object Detection (YOLO)""",
        "order": 3
    },
    {
        "section_type": "experience",
        "title": "LLM & Vision Infrastructure Engineer",
        "content": """{
    "company": "EonForge (Logos Technologies LLC)",
    "location": "Dubai, UAE / Remote",
    "period": "July 2025 – Present",
    "bullets": [
        "Designed Hybrid RAG system combining FAISS vector search with Knowledge Graph traversal for multi-hop reasoning",
        "Built end-to-end document processing pipeline using Tesseract OCR with custom layout analysis",
        "Architected orchestration layer for 'LumenCipher' Insurance CRM with JWT/OAuth2 security",
        "Developed intelligent agents for automated claims processing using SQLAlchemy (Async)"
    ]
}""",
        "order": 4
    },
    {
        "section_type": "experience",
        "title": "Member Technical Staff (NLP & AI)",
        "content": """{
    "company": "Zoho Corporation",
    "location": "Chennai, TN",
    "period": "June 2023 – June 2025",
    "bullets": [
        "**4x Throughput:** Migrated to vLLM with Continuous Batching, increasing throughput from 20 to 80 tokens/sec",
        "**40% Latency Reduction:** Implemented Int8 Quantization using CTranslate2, reducing P99 from 5s to 3s",
        "**60% Cost Reduction:** Achieved through CPU offloading and optimized GEMM kernels",
        "Fine-tuned FLAN-T5 and LLaMA 3.1 using LoRA/QLoRA for specialized tasks",
        "Deployed on Kubernetes (EKS) with HPA based on GPU metrics and Prometheus/Grafana monitoring"
    ]
}""",
        "order": 5
    },
    {
        "section_type": "experience",
        "title": "Project Trainee (AI/ML)",
        "content": """{
    "company": "Zoho Corporation",
    "location": "Chennai, TN",
    "period": "Oct 2022 – May 2023",
    "bullets": [
        "Led migration from RNN/LSTM to Transformer-based pipelines",
        "Built data migration pipelines using Zoho Catalyst",
        "Enforced code quality with Poetry and Pytest"
    ]
}""",
        "order": 6
    },
    {
        "section_type": "education",
        "title": "Education",
        "content": """{
    "degree": "B.Tech in Computer Science & Engineering",
    "institution": "Sri Venkateswara College of Engineering",
    "cgpa": "7.72"
}""",
        "order": 7
    }
]


async def get_setting(db: AsyncSession, key: str) -> str:
    """Get a site setting by key, returns default if not in DB."""
    result = await db.execute(select(SiteSettings).where(SiteSettings.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        return setting.value
    return DEFAULT_SETTINGS.get(key, "")


async def get_all_settings(db: AsyncSession) -> dict:
    """Get all site settings as a dictionary."""
    result = await db.execute(select(SiteSettings))
    db_settings = {s.key: s.value for s in result.scalars().all()}
    
    # Merge with defaults
    settings = DEFAULT_SETTINGS.copy()
    settings.update(db_settings)
    return settings


async def set_setting(db: AsyncSession, key: str, value: str, description: str = ""):
    """Set a site setting."""
    result = await db.execute(select(SiteSettings).where(SiteSettings.key == key))
    setting = result.scalar_one_or_none()
    
    if setting:
        setting.value = value
        if description:
            setting.description = description
    else:
        setting = SiteSettings(key=key, value=value, description=description)
        db.add(setting)
    
    await db.commit()


async def get_page(db: AsyncSession, slug: str) -> Page:
    """Get a page by slug, creates with default content if not exists."""
    result = await db.execute(select(Page).where(Page.slug == slug))
    page = result.scalar_one_or_none()
    
    if not page and slug in DEFAULT_PAGES:
        defaults = DEFAULT_PAGES[slug]
        page = Page(
            slug=slug,
            title=defaults["title"],
            content=defaults["content"],
            meta_description=defaults.get("meta_description", "")
        )
        db.add(page)
        await db.commit()
        await db.refresh(page)
    
    return page


async def get_resume_sections(db: AsyncSession) -> list[ResumeSection]:
    """Get all resume sections, creates defaults if empty."""
    result = await db.execute(
        select(ResumeSection).where(ResumeSection.visible == True).order_by(ResumeSection.order)
    )
    sections = result.scalars().all()
    
    if not sections:
        # Create default sections
        for section_data in DEFAULT_RESUME_SECTIONS:
            section = ResumeSection(**section_data)
            db.add(section)
        await db.commit()
        
        result = await db.execute(
            select(ResumeSection).where(ResumeSection.visible == True).order_by(ResumeSection.order)
        )
        sections = result.scalars().all()
    
    return sections


async def init_default_content(db: AsyncSession):
    """Initialize all default content in database."""
    # Initialize settings
    for key, value in DEFAULT_SETTINGS.items():
        result = await db.execute(select(SiteSettings).where(SiteSettings.key == key))
        if not result.scalar_one_or_none():
            db.add(SiteSettings(key=key, value=value))
    
    # Initialize pages
    for slug, data in DEFAULT_PAGES.items():
        result = await db.execute(select(Page).where(Page.slug == slug))
        if not result.scalar_one_or_none():
            db.add(Page(
                slug=slug,
                title=data["title"],
                content=data["content"],
                meta_description=data.get("meta_description", "")
            ))
    
    # Initialize resume sections
    result = await db.execute(select(ResumeSection))
    if not result.scalars().first():
        for section_data in DEFAULT_RESUME_SECTIONS:
            db.add(ResumeSection(**section_data))
    
    await db.commit()
