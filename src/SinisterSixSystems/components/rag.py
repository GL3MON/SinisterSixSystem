import fitz  # PyMuPDF
import camelot
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from PIL import Image
import torch
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer, AutoModelForCausalLM

# ------------------- Lightweight Image Captioning -------------------
device = "cuda" if torch.cuda.is_available() else "cpu"

# ViT-GPT2 model (fast & memory-efficient)
caption_model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning").to(device)
caption_processor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
caption_tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

def caption_image(image_path):
    image = Image.open(image_path).convert("RGB")
    pixel_values = caption_processor(images=image, return_tensors="pt").pixel_values.to(device)
    output_ids = caption_model.generate(pixel_values, max_length=64)
    caption = caption_tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return caption

# ------------------- RAG Pipeline -------------------
class MultimodalGraniteRAG:
    def __init__(self, pdf_path, image_dir="images", k_retrieve=3):
        self.pdf_path = pdf_path
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(exist_ok=True)
        self.k_retrieve = k_retrieve

        # LLM (Granite)
        self.llm_tokenizer = AutoTokenizer.from_pretrained("ibm-granite/granite-3.0-8b-instruct")
        self.llm_model = AutoModelForCausalLM.from_pretrained(
            "ibm-granite/granite-3.0-8b-instruct",
            torch_dtype=torch.float16,
            device_map="auto"
        )

        # Sentence embeddings
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

        # Build chunks and FAISS index
        self.chunks = self.build_multimodal_chunks()
        self.build_index()

    # ---------------- Text ----------------
    def extract_text(self):
        doc = fitz.open(self.pdf_path)
        return "\n".join(page.get_text() for page in doc)

    # ---------------- Tables ----------------
    def extract_tables(self):
        tables = camelot.read_pdf(self.pdf_path, pages="all")
        return [t.df.to_string(index=False) for t in tables]

    # ---------------- Images ----------------
    def extract_images(self):
        doc = fitz.open(self.pdf_path)
        image_paths = []
        for page_num, page in enumerate(doc):
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base = doc.extract_image(xref)
                path = self.image_dir / f"page{page_num}_img{img_index}.{base['ext']}"
                with open(path, "wb") as f:
                    f.write(base["image"])
                image_paths.append(str(path))
        return image_paths

    # ---------------- Chunks ----------------
    def build_multimodal_chunks(self):
        chunks = []

        # Text
        text = self.extract_text()
        chunks.append({"text": text, "type": "text", "source": self.pdf_path})

        # Tables
        for i, table_text in enumerate(self.extract_tables()):
            chunks.append({"text": table_text, "type": "table", "source": f"{self.pdf_path}_table_{i}"})

        # Images
        for img_path in self.extract_images():
            caption = caption_image(img_path)
            chunks.append({"text": caption, "type": "image", "source": img_path})

        return chunks

    # ---------------- FAISS Index ----------------
    def build_index(self):
        texts = [c["text"] for c in self.chunks]
        embeddings = self.embed_model.encode(texts, convert_to_numpy=True)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def retrieve(self, query):
        q_emb = self.embed_model.encode([query], convert_to_numpy=True)
        _, idx = self.index.search(q_emb, self.k_retrieve)
        return [self.chunks[i] for i in idx[0]]

    # ---------------- Generate Answer ----------------
    def generate_answer(self, query):
        docs = self.retrieve(query)
        context = "\n".join(f"[{d['type'].upper()} from {d['source']}]\n{d['text']}" for d in docs)

        prompt = f"""
Use the context below to answer the question.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{query}

Answer:
"""
        inputs = self.llm_tokenizer(prompt, return_tensors="pt").to(self.llm_model.device)
        output = self.llm_model.generate(
            **inputs,
            max_new_tokens=300,
            temperature=0.2,
            do_sample=False
        )
        return self.llm_tokenizer.decode(output[0], skip_special_tokens=True)


# ---------------- Example ----------------
if __name__ == "__main__":
    pdf_path = "/kaggle/input/sampledataset/sample.pdf"
    rag_system = MultimodalGraniteRAG(pdf_path)

    question = "Summarize the key findings including tables and figures."
    answer = rag_system.generate_answer(question)
    print("Answer:\n", answer)
