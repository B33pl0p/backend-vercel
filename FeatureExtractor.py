import clip
import torch
from PIL import Image
import numpy

#initialization of CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def extract_text_embedding(query_text):
    with torch.no_grad():
        tokenized_text = clip.tokenize([query_text]).to(device)
        text_embedding = model.encode_text(tokenized_text)
        
        # Check shape and normalization
        #print("Text embedding shape:", text_embedding.shape)
        text_embedding /= text_embedding.norm(dim=1, keepdim=True)
        #print("Normalized text embedding:", text_embedding)

        return text_embedding.cpu().numpy().flatten()

def extract_image_embedding(image_path):
    with torch.no_grad():
        image = Image.open(image_path).convert("RGB")
        preprocessed_image = preprocess(image).unsqueeze(0).to(device)
        
        image_embedding = model.encode_image(preprocessed_image)

        # Check shape and normalization
        #print("Image embedding shape:", image_embedding.shape)
        image_embedding /= image_embedding.norm(dim=1, keepdim=True)
        #print("Normalized image embedding:", image_embedding)

        return image_embedding.cpu().numpy().flatten()